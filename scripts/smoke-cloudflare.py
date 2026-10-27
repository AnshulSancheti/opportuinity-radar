"""Exercise the deployed API with disposable, isolated accounts; write exact cleanup SQL."""
import http.cookiejar,json,secrets,sys,urllib.request,urllib.error,uuid
from pathlib import Path
base=sys.argv[1].rstrip('/')
class Client:
    def __init__(self):
        self.cookies=http.cookiejar.CookieJar();self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
    def call(self,path,method='GET',data=None,headers=None):
        hdr={'Content-Type':'application/json','User-Agent':'OpportunityRadar deployment verification',**(headers or {})}
        req=urllib.request.Request(base+'/api/v1'+path,data=json.dumps(data).encode() if data is not None else None,headers=hdr,method=method)
        try:
            with self.opener.open(req,timeout=45) as r:return r.status,json.load(r),r.headers
        except urllib.error.HTTPError as e:return e.code,json.load(e),e.headers

a,b=Client(),Client();created=[];password=secrets.token_urlsafe(24)
def expect(client,path,status=200,method='GET',data=None,headers=None):
    actual,value,hdr=client.call(path,method,data,headers)
    assert actual==status,(path,actual,value)
    return value,hdr
try:
    expect(a,'/health');expect(a,'/actions',401);expect(a,'/actions/saved',401)
    articles,_=expect(a,'/news?limit=1');hacks,_=expect(a,'/hackathons?limit=1')
    article=articles['items'][0]['id'];hack=hacks['items'][0]['id']
    assert hacks['items'][0]['source_name'] in ['mlh','devpost']
    for client,name in [(a,'Alice'),(b,'Bob')]:
        email=f'radar-smoke-{uuid.uuid4().hex}@example.com'
        user,hdr=expect(client,'/auth/register',201,'POST',{'email':email,'name':name,'password':password});created.append(user)
        ck=hdr.get('Set-Cookie');assert 'HttpOnly' in ck and 'SameSite=Lax' in ck
        if base.startswith('https:'):assert 'Secure' in ck
        assert 'password_hash' not in user
        me,_=expect(client,'/auth/me');assert me['id']==user['id']
    expect(b,'/auth/register',409,'POST',{'name':'Duplicate','email':created[0]['email'],'password':password})
    expect(a,'/actions',method='POST',data={'item_type':'article','item_id':article,'action':'saved'})
    expect(a,'/actions',method='POST',data={'item_type':'hackathon','item_id':hack,'action':'saved'})
    expect(a,'/actions',method='POST',data={'item_type':'hackathon','item_id':hack,'action':'applied'})
    expect(a,'/actions',method='POST',data={'item_type':'article','item_id':article,'action':'saved'})
    saved,_=expect(a,'/actions/saved');assert len(saved)==2 and all(i['title'] and i['url'] for i in saved)
    applied,_=expect(a,'/actions/saved?action=applied');assert len(applied)==1
    assert expect(b,'/actions/saved')[0]==[]
    expect(b,f'/actions?item_type=hackathon&item_id={hack}&action=saved',method='DELETE')
    assert len(expect(a,'/actions/saved')[0])==2
    expect(a,f'/actions?item_type=article&item_id={article}&action=saved',method='DELETE')
    expect(a,f'/actions?item_type=hackathon&item_id={hack}&action=applied',method='DELETE')
    assert expect(a,'/actions/saved?action=applied')[0]==[]
    expect(a,'/actions',422,'POST',{'item_type':'article','item_id':article,'action':'applied'})
    expect(a,'/actions',422,'POST',{'item_type':'job','item_id':article,'action':'saved'})
    expect(a,'/auth/logout',403,'POST',{},headers={'Origin':'https://attacker.example'})
    expect(a,'/admin/run-scraper',401,'POST',{'module':'hackathons'})
    expect(a,'/jobs',404);expect(a,'/matches/status',404);expect(a,'/news?limit=0',422)
    old='; '.join(f'{c.name}={c.value}' for c in a.cookies)
    expect(a,'/auth/logout',method='POST',data={});expect(a,'/auth/me',401)
    expect(a,'/auth/me',401,headers={'Cookie':old})
    expect(a,'/auth/login',method='POST',data={'email':created[0]['email'].upper(),'password':password})
    expect(a,'/auth/login',401,'POST',{'email':created[0]['email'],'password':'wrong-password-value'})
    expect(a,'/auth/logout',method='POST',data={});expect(b,'/auth/logout',method='POST',data={})
    print('PASS: public feeds; registration/login/logout; secure-cookie flags; duplicate registration; account isolation; save/unsave; applied/undo; revoked sessions; validation; origin checks; operator rejection.')
finally:
    if created:
        ids=','.join("'"+u['id'].replace("'","''")+"'" for u in created)
        path=Path('.radar/cloudflare-smoke-cleanup.sql');path.write_text(f"DELETE FROM accounts WHERE id IN ({ids}) AND email LIKE 'radar-smoke-%@example.com';\n");path.chmod(0o600)

import { hash, token, passwordHash, passwordValid, secretEqual } from './auth';
import { count, HttpError, integer, nowISO, present, Row, rows, visibleArgs, visibleSQL } from './db';
import { claimIngestion, ingest, sourceNames } from './ingestion';

const COOKIE = 'radar_session';
function json(body: unknown, status = 200, headers: HeadersInit = {}) { return Response.json(body,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...headers}}); }
function cookie(request: Request) { return request.headers.get('Cookie')?.split(';').map(v=>v.trim()).find(v=>v.startsWith(COOKIE+'='))?.slice(COOKIE.length+1); }
function sessionCookie(request: Request, value: string, age=604800) { return `${COOKIE}=${value}; Path=/; HttpOnly; SameSite=Lax; Max-Age=${age}${new URL(request.url).protocol==='https:'?'; Secure':''}`; }
async function body(request: Request): Promise<Row> {
  if (!request.headers.get('content-type')?.includes('application/json')) throw new HttpError(415,'JSON content type required');
  const reader=request.body?.getReader(); if(!reader)throw new HttpError(400,'JSON body required');
  let size=0; const chunks: Uint8Array[]=[];
  while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>16384){await reader.cancel();throw new HttpError(413,'Request body too large');}chunks.push(value);}
  const data=new Uint8Array(size);let offset=0;for(const chunk of chunks){data.set(chunk,offset);offset+=chunk.length;}
  try { const value: unknown=JSON.parse(new TextDecoder().decode(data));if(typeof value!=='object'||value===null||Array.isArray(value))throw new Error();return value as Row; } catch { throw new HttpError(400,'Invalid JSON body'); }
}
function field(data: Row,key:string,max=254) { const value=data[key];if(typeof value!=='string'||value.length>max)throw new HttpError(422,`Invalid ${key}`);return value; }
function positiveID(value: unknown) { if(typeof value!=='number'||!Number.isSafeInteger(value)||value<1)throw new HttpError(422,'Invalid item ID');return value; }
async function account(request: Request,env: Env) {
  const raw=cookie(request); const row=raw?await env.DB.prepare('SELECT a.* FROM accounts a JOIN account_sessions s ON s.user_id=a.id WHERE s.token_hash=? AND s.expires_at>?').bind(hash(raw),nowISO()).first<Row>():null;
  if(!row)throw new HttpError(401,'Sign in to continue');return row;
}
function publicAccount(row: Row) { return {id:row.id,email:row.email,name:row.name}; }
async function throttle(request: Request,env: Env,email:string) {
  const since=new Date(Date.now()-15*60000).toISOString();
  const keys=[hash('email:'+email),hash('ip:'+(request.headers.get('CF-Connecting-IP')||'local'))];
  const totals=await env.DB.batch<{total:number}>(keys.map(key=>env.DB.prepare('SELECT COUNT(*) AS total FROM auth_attempts WHERE key=? AND created_at>?').bind(key,since)));
  if(totals.some((r,i)=>(Number(r.results[0]?.total)||0)>=(i===0?10:40)))throw new HttpError(429,'Too many attempts. Try again in 15 minutes.');
  await env.DB.batch([env.DB.prepare('DELETE FROM auth_attempts WHERE created_at<?').bind(new Date(Date.now()-3600000).toISOString()),...keys.map(key=>env.DB.prepare('INSERT INTO auth_attempts(key,created_at) VALUES (?,?)').bind(key,nowISO()))]);
}
async function startSession(request: Request,env: Env,row: Row,status=200) {
  const raw=token(),old=cookie(request),now=nowISO();
  await env.DB.batch([env.DB.prepare('DELETE FROM account_sessions WHERE expires_at<=? OR token_hash=?').bind(now,old?hash(old):''),env.DB.prepare('INSERT INTO account_sessions(token_hash,user_id,expires_at) VALUES (?,?,?)').bind(hash(raw),row.id,new Date(Date.now()+604800000).toISOString())]);
  return json(publicAccount(row),status,{'Set-Cookie':sessionCookie(request,raw)});
}
async function requireAdmin(request: Request,env: Env) {
  await account(request,env);
  if(!env.ADMIN_PASSWORD||['change-me','password','admin'].includes(env.ADMIN_PASSWORD))throw new HttpError(503,'Operator access is not configured');
  if(!secretEqual(request.headers.get('X-Admin-Password')||'',env.ADMIN_PASSWORD))throw new HttpError(401,'Invalid admin password');
}
async function sourceStatus(env: Env) {
  const sources=[];
  for(const name of sourceNames){
    const last=await env.DB.prepare("SELECT status,error_message FROM scrape_runs WHERE module='hackathons' AND source_name=? ORDER BY started_at DESC LIMIT 1").bind(name).first<Row>();
    const success=await env.DB.prepare("SELECT MAX(finished_at) AS checked FROM scrape_runs WHERE module='hackathons' AND source_name=? AND status='success'").bind(name).first<{checked:string|null}>();
    sources.push({name,status:last?.status||'not_run',last_success_at:success?.checked||null,error:last?.status==='failed'?'Latest source refresh failed':null,count:await count(env.DB,'hackathons',visibleSQL+' AND source_name=?',[...visibleArgs(),name])});
  }
  return {sources,auto_refresh:true,refresh_hours:Number(env.HACKATHON_REFRESH_HOURS)};
}
async function enqueue(env:Env,module:'news'|'hackathons') {
  const owner=await claimIngestion(env,module);if(!owner)return false;
  try { await env.INGESTION_QUEUE.send({module,owner}); return true; }
  catch(error){await env.DB.prepare('DELETE FROM ingestion_locks WHERE module=? AND owner=?').bind(module,owner).run();throw error;}
}
async function api(request: Request,env: Env,ctx: ExecutionContext) {
  const url=new URL(request.url),path=url.pathname.replace(/\/$/,''),q=url.searchParams,method=request.method;
  if(method==='OPTIONS')return new Response(null,{status:204});
  if(!['GET','HEAD'].includes(method)){
    const origin=request.headers.get('Origin');
    const local=['localhost','127.0.0.1'].includes(url.hostname);
    if((origin&&origin!==(local?url.origin:env.APP_ORIGIN))||request.headers.get('Sec-Fetch-Site')==='cross-site')throw new HttpError(403,'Origin not allowed');
  }
  if(path==='/api/v1/health'&&method==='GET'){await env.DB.prepare('SELECT 1').first();return json({status:'ok',database:'ok',platform:'cloudflare'});}
  if(['/api/v1/auth/register','/api/v1/auth/login'].includes(path)&&method==='POST'){
    const data=await body(request),email=field(data,'email').trim().toLowerCase(),password=field(data,'password',128);
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)||password.length<10)throw new HttpError(422,'Enter a valid email and a password of at least 10 characters');
    await throttle(request,env,email);
    if(path.endsWith('/register')){
      const name=field(data,'name',80).trim();if(!name)throw new HttpError(422,'Enter your name');
      const row={id:crypto.randomUUID(),email,name,password_hash:await passwordHash(password)};
      const result=await env.DB.prepare('INSERT OR IGNORE INTO accounts(id,email,name,password_hash,created_at) VALUES (?,?,?,?,?)').bind(row.id,email,name,row.password_hash,nowISO()).run();
      if(!result.meta.changes)throw new HttpError(409,'An account with that email already exists');
      return startSession(request,env,row,201);
    }
    const row=await env.DB.prepare('SELECT * FROM accounts WHERE email=?').bind(email).first<Row>();
    if(!await passwordValid(password,typeof row?.password_hash==='string'?row.password_hash:undefined)||!row)throw new HttpError(401,'Email or password is incorrect');
    if(String(row.password_hash).startsWith('scrypt$'))await env.DB.prepare('UPDATE accounts SET password_hash=? WHERE id=?').bind(await passwordHash(password),row.id).run();
    return startSession(request,env,row);
  }
  if(path==='/api/v1/auth/me'&&method==='GET')return json(publicAccount(await account(request,env)));
  if(path==='/api/v1/auth/logout'&&method==='POST'){
    await body(request);const raw=cookie(request);if(raw)await env.DB.prepare('DELETE FROM account_sessions WHERE token_hash=?').bind(hash(raw)).run();
    return json({status:'signed out'},200,{'Set-Cookie':sessionCookie(request,'',0)});
  }
  if((path==='/api/v1/news'||path==='/api/v1/hackathons')&&method==='GET'){
    const hacks=path.endsWith('hackathons'),table=hacks?'hackathons':'articles';
    const limit=integer(q.get('limit'),20,1,100),offset=integer(q.get('offset'),0,0,1000000);
    let where=hacks?visibleSQL:'1=1';const args:(string|number|null)[]=hacks?visibleArgs():[];
    if(q.get('q')){where+=hacks?' AND (name LIKE ? OR organizer LIKE ?)':' AND (title LIKE ? OR summary LIKE ?)';args.push('%'+q.get('q')+'%','%'+q.get('q')+'%');}
    for(const [param,column] of (hacks?[['mode','mode'],['source','source_name']]:[['category','category'],['source','source_name']]))if(q.get(param)){where+=` AND ${column}=?`;args.push(q.get(param));}
    if(hacks&&q.get('theme')){where+=' AND EXISTS (SELECT 1 FROM json_each(themes) WHERE value=?)';args.push(q.get('theme'));}
    const order=hacks?'COALESCE(registration_deadline,end_date,start_date) ASC':'COALESCE(published_at,first_seen_at) DESC';
    return json({items:(await rows(env.DB,`SELECT * FROM ${table} WHERE ${where} ORDER BY ${order} LIMIT ? OFFSET ?`,[...args,limit,offset])).map(present),total:await count(env.DB,table,where,args),limit,offset});
  }
  if(path==='/api/v1/hackathons/sources'&&method==='GET')return json(await sourceStatus(env));
  if(/^\/api\/v1\/(news|hackathons)\/\d+$/.test(path)&&method==='GET'){
    const table=path.includes('/news/')?'articles':'hackathons',id=integer(path.split('/').pop()||null,0,1,Number.MAX_SAFE_INTEGER);
    const item=await env.DB.prepare(`SELECT * FROM ${table} WHERE id=?`).bind(id).first<Row>();if(!item)throw new HttpError(404,'Item not found');return json(present(item));
  }
  if(path==='/api/v1/actions'&&['GET','POST','DELETE'].includes(method)){
    const user=await account(request,env);
    if(method==='GET')return json(await rows(env.DB,'SELECT id,item_type,item_id,action,created_at FROM user_actions WHERE user_id=? ORDER BY created_at DESC',[String(user.id)]));
    const data=method==='POST'?await body(request):Object.fromEntries(q);
    const kind=field(data,'item_type'),action=field(data,'action'),id=method==='POST'?positiveID(data.item_id):integer(q.get('item_id'),0,1,Number.MAX_SAFE_INTEGER);
    if(!['article','hackathon'].includes(kind)||!['saved','applied'].includes(action)||(action==='applied'&&kind!=='hackathon'))throw new HttpError(422,'Invalid item or action');
    if(method==='DELETE'){await env.DB.prepare('DELETE FROM user_actions WHERE user_id=? AND item_type=? AND item_id=? AND action=?').bind(user.id,kind,id,action).run();return json({status:'removed'});}
    const exists=await env.DB.prepare(`SELECT id FROM ${kind==='article'?'articles':'hackathons'} WHERE id=?`).bind(id).first();if(!exists)throw new HttpError(404,'Item not found');
    await env.DB.prepare('INSERT OR IGNORE INTO user_actions(user_id,item_type,item_id,action,created_at) VALUES (?,?,?,?,?)').bind(user.id,kind,id,action,nowISO()).run();
    return json(await env.DB.prepare('SELECT id,item_type,item_id,action,created_at FROM user_actions WHERE user_id=? AND item_type=? AND item_id=? AND action=?').bind(user.id,kind,id,action).first());
  }
  if(path==='/api/v1/actions/saved'&&method==='GET'){
    const user=await account(request,env),action=q.get('action')||'saved';if(!['saved','applied'].includes(action))throw new HttpError(422,'Invalid action');
    const items=[];
    for(const [kind,table,title,subtitle] of [['article','articles','title','source_name'],['hackathon','hackathons','name','organizer']]){
      items.push(...await rows(env.DB,`SELECT a.id,a.item_type,a.item_id,a.action,a.created_at,i.${title} AS title,i.${subtitle} AS subtitle,i.url,i.source_name,${kind==='hackathon'?'i.registration_deadline AS deadline,i.status,i.end_date':'NULL AS deadline,NULL AS status,NULL AS end_date'} FROM user_actions a JOIN ${table} i ON i.id=a.item_id WHERE a.user_id=? AND a.item_type=? AND a.action=?`,[String(user.id),kind,action]));
    }
    return json(items.sort((a,b)=>String(b.created_at).localeCompare(String(a.created_at))));
  }
  if(path==='/api/v1/admin/stats'&&method==='GET'){
    const last=await env.DB.prepare('SELECT MAX(finished_at) AS checked FROM scrape_runs').first<{checked:string|null}>();
    const locks=await rows(env.DB,'SELECT module FROM ingestion_locks WHERE expires_at>?',[nowISO()]);
    const failed=await rows(env.DB,"SELECT DISTINCT source_name FROM scrape_runs r WHERE status='failed' AND id=(SELECT id FROM scrape_runs x WHERE x.source_name=r.source_name ORDER BY started_at DESC LIMIT 1)");
    return json({total_articles:await count(env.DB,'articles','1=1'),total_hackathons:await count(env.DB,'hackathons',visibleSQL,visibleArgs()),last_scrape_at:last?.checked||null,failed_sources:failed.length,active_scrapes:locks.map(l=>l.module)});
  }
  if(path==='/api/v1/admin/scrape-runs'&&method==='GET'){await requireAdmin(request,env);return json(await rows(env.DB,'SELECT * FROM scrape_runs ORDER BY started_at DESC LIMIT ?',[integer(q.get('limit'),50,1,100)]));}
  if(path==='/api/v1/admin/run-scraper'&&method==='POST'){
    await requireAdmin(request,env);const data=await body(request);if(data.module!=='news'&&data.module!=='hackathons')throw new HttpError(422,'Invalid scraper module');
    if(!await enqueue(env,data.module))throw new HttpError(409,'Scrape already queued or running');return json({status:'queued',module:data.module});
  }
  throw new HttpError(404,'Not found');
}
export default {
  async fetch(request: Request,env: Env,ctx: ExecutionContext) {
    if(!new URL(request.url).pathname.startsWith('/api/'))return env.ASSETS.fetch(request);
    try{return await api(request,env,ctx);}catch(error){
      if(error instanceof HttpError)return json({detail:error.message},error.status);
      console.error(JSON.stringify({event:'api_failure',path:new URL(request.url).pathname,type:error instanceof Error?error.name:'unknown'}));
      return json({detail:'Something went wrong. Please try again.'},500);
    }
  },
  async scheduled(controller: ScheduledController,env: Env) { await enqueue(env,controller.cron==='0 */6 * * *'?'hackathons':'news'); },
  async queue(batch: MessageBatch<{module:'news'|'hackathons';owner?:string}>,env: Env) {
    for(const message of batch.messages){try{await ingest(env,message.body.module,message.body.owner);message.ack();}catch(error){console.error(JSON.stringify({event:'ingestion_failure',module:message.body.module,type:error instanceof Error?error.name:'unknown'}));message.retry({delaySeconds:900});}}
  }
} satisfies ExportedHandler<Env,{module:'news'|'hackathons';owner?:string}>;

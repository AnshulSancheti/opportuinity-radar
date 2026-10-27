import assert from 'node:assert/strict';
import { test } from 'node:test';
import { scryptSync } from 'node:crypto';
import { passwordHash,passwordValid } from './auth';
import { canonical,contentHash,parseMLH,parseDevpost,parseRSS,submissionDates } from './ingestion';

test('existing Python scrypt hashes remain usable',async()=>{
 const password='Compatibility-test-password',salt='1234567890abcdef';
 const encoded='scrypt$'+salt+'$'+scryptSync(password,salt,64,{N:131072,r:8,p:1,maxmem:268435456}).toString('hex');
 assert.equal(await passwordValid(password,encoded),true);
 assert.equal(await passwordValid('Incorrect-password',encoded),false);
});
test('new memory-bounded scrypt hashes verify passwords',async()=>{
 const encoded=await passwordHash('Account-test-password');assert.equal(await passwordValid('Account-test-password',encoded),true);assert.equal(await passwordValid('Wrong-password',encoded),false);assert.equal(await passwordValid('Wrong-password'),false);
});
test('MLH reads structured source identity and dates',()=>{
 const event={id:'abc',name:'Example Hack',startsAt:'2027-01-09T10:00:00Z',endsAt:'2027-01-10T20:00:00Z',websiteUrl:'https://example.com/hack',formatType:'physical',venueAddress:{city:'Delhi',state:'Delhi',country:'IN'}};
 const items=parseMLH('<script data-page="app" type="application/json">'+JSON.stringify({props:{upcomingEvents:[event]}})+'</script>');assert.equal(items[0].location,'Delhi, IN');assert.equal(items[0].content_hash,contentHash('mlh','abc'));assert.equal(items[0].registration_deadline,null);assert.throws(()=>parseMLH('<article>Changed layout</article>'));
});
test('Devpost distinguishes submission dates from registration deadlines',()=>{
 const item=parseDevpost({id:123,title:'Example Hack',url:'https://example.devpost.com/',submission_period_dates:'Oct 27 - Nov 3, 2026',open_state:'open',displayed_location:{location:'Online'},prize_amount:'$<span>5000</span>',themes:[{name:'AI'}]});assert.equal(item.mode,'online');assert.equal(item.registration_deadline,null);assert.equal(item.prize_text,'$ 5000');assert.equal(item.end_date,'2026-11-03T23:59:59.999Z');
});
for(const [input,start,end] of [
 ['Aug 26 - Oct 30, 2026','2026-08-26','2026-10-30'],['Oct 27 - 30, 2026','2026-10-27','2026-10-30'],['Dec 20 - Jan 5, 2027','2026-12-20','2027-01-05'],['Dec 20, 2026 - Jan 5, 2027','2026-12-20','2027-01-05'],['Nov 02, 2026',null,'2026-11-02']
])test('submission range '+input,()=>{const result=submissionDates(input!);assert.equal(result[0]?.slice(0,10)||null,start);assert.equal(result[1].slice(0,10),end);});
test('unrecognized dates never get guessed',()=>{assert.throws(()=>submissionDates('Dates to be announced'));assert.throws(()=>submissionDates('Oct 32 - Nov 5, 2026'));});
test('RSS and Atom feeds produce safe canonical article links',()=>{
 const rss='<rss><channel><item><title>Cloudflare news</title><link>https://example.com/news?utm_source=rss</link><description>Latest update</description><pubDate>Tue, 27 Oct 2026 12:00:00 GMT</pubDate></item></channel></rss>';
 const row=parseRSS(rss,'Example')[0];assert.equal(row.url,'https://example.com/news');assert.equal(row.category,'Cloud');assert.equal(row.published_at,'2026-10-27T12:00:00.000Z');
 const atom='<feed><entry><title>Test</title><link href="https://example.com/atom" rel="alternate"/><updated>2026-10-27T10:00:00Z</updated></entry></feed>';assert.equal(parseRSS(atom,'Example')[0].url,'https://example.com/atom');assert.equal(canonical('javascript:alert(1)'),null);
});

import { XMLParser } from 'fast-xml-parser';
import { hash, token } from './auth';
import { nowISO, Row, rows } from './db';

export const sourceNames = ['mlh','devpost'] as const;
type Module = 'news'|'hackathons';
export const object = (value: unknown): Row => value && typeof value==='object'&&!Array.isArray(value)?value as Row:{};
const array = (value: unknown): unknown[] => value===undefined||value===null?[]:Array.isArray(value)?value:[value];
const string = (value: unknown) => typeof value==='string'?value:'';
export const clean = (value: unknown) => (string(value)||string(object(value)['#text'])).replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();
const date = (value: unknown) => {const ms=Date.parse(string(value));return Number.isFinite(ms)?new Date(ms).toISOString():null;};
export function canonical(value: unknown) {
  try{const url=new URL(string(value));if(!['http:','https:'].includes(url.protocol))return null;url.hash='';for(const name of [...url.searchParams.keys()])if(/^(utm_|ref$|fbclid$|gclid$)/i.test(name))url.searchParams.delete(name);return url.toString().replace(/\/$/,'');}catch{return null;}
}
export const contentHash = (...parts: string[]) => hash(parts.map(s=>s.replace(/\s+/g,' ').trim().toLowerCase()).join('|'));
async function textURL(url: string) {
  const response=await fetch(url,{headers:{'User-Agent':'OpportunityRadar/1.0 (+https://hackathons.intelligentape.online)'},redirect:'follow',signal:AbortSignal.timeout(25000)});
  if(!response.ok)throw new Error(`Source returned HTTP ${response.status}`);
  const reader=response.body?.getReader();if(!reader)throw new Error('Source returned no body');const chunks:Uint8Array[]=[];let size=0;
  while(true){const {value,done}=await reader.read();if(done)break;size+=value.byteLength;if(size>4*1024*1024){await reader.cancel();throw new Error('Source response exceeded size limit');}chunks.push(value);}
  const result=new Uint8Array(size);let offset=0;for(const part of chunks){result.set(part,offset);offset+=part.length;}return new TextDecoder().decode(result);
}
async function jsonURL(url: string): Promise<unknown> {return JSON.parse(await textURL(url));}

export function parseMLH(html: string): Row[] {
  const script=html.match(/<script\b[^>]*data-page=["']app["'][^>]*>([\s\S]*?)<\/script>/i);
  if(!script)throw new Error('MLH event data missing');
  const events=object(object(JSON.parse(script[1])).props).upcomingEvents;
  if(!Array.isArray(events)||!events.length)throw new Error('MLH upcoming events missing');
  return events.map(value=>{
    const event=object(value),venue=object(event.venueAddress),start=date(event.startsAt),end=date(event.endsAt),url=canonical(event.websiteUrl);
    if(!event.id||!event.name||!start||!end||!url)throw new Error('MLH event identity or dates missing');
    const format=string(event.formatType);
    return {name:string(event.name),source_name:'mlh',url,canonical_url:url,content_hash:contentHash('mlh',String(event.id)),start_date:start,end_date:end,mode:format==='physical'?'offline':['digital','virtual','online'].includes(format)?'online':format==='hybrid'?'hybrid':null,location:[...new Set([venue.city,venue.state,venue.country].filter(v=>typeof v==='string'&&v))].join(', ')||string(event.location)||null,themes:'[]',organizer:null,registration_deadline:null,prize_text:null,application_status:null};
  });
}
const months=['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'];
function calendar(value: string,year: number,month?: number) {
  const match=value.trim().match(/^(?:([A-Za-z]+)\s+)?(\d{1,2})(?:,?\s+(\d{4}))?$/);if(!match)throw new Error('Unrecognized submission date');
  const y=Number(match[3]||year),m=match[1]?months.indexOf(match[1].slice(0,3).toLowerCase()):month,d=Number(match[2]);if(m===undefined||m<0)throw new Error('Submission month missing');
  const result=new Date(Date.UTC(y,m,d));if(result.getUTCDate()!==d||result.getUTCMonth()!==m)throw new Error('Invalid submission date');return result;
}
export function submissionDates(value: string): [string|null,string] {
  const parts=value.trim().split(/\s+(?:-|–|—)\s+/),year=Number(value.match(/\b(\d{4})\s*$/)?.[1]);if(!year)throw new Error('Submission year missing');
  if(parts.length===1){const end=calendar(parts[0],year);end.setUTCHours(23,59,59,999);return [null,end.toISOString()];}
  if(parts.length!==2)throw new Error('Unrecognized submission period');
  const startMonth=months.indexOf(parts[0].slice(0,3).toLowerCase());const end=calendar(parts[1],year,startMonth);end.setUTCHours(23,59,59,999);
  let start=calendar(parts[0],end.getUTCFullYear());if(start>end&&!/\b\d{4}\b/.test(parts[0]))start=calendar(parts[0],end.getUTCFullYear()-1);if(start>end)throw new Error('Submission dates reversed');return [start.toISOString(),end.toISOString()];
}
export function parseDevpost(value: unknown): Row {
  const event=object(value),url=canonical(event.url),[start,end]=submissionDates(string(event.submission_period_dates));
  if(!event.id||!event.title||!url)throw new Error('Devpost event identity missing');
  const location=string(object(event.displayed_location).location)||null;
  return {name:string(event.title),source_name:'devpost',url,canonical_url:url,content_hash:contentHash('devpost',String(event.id)),organizer:string(event.organization_name)||null,mode:location?.toLowerCase()==='online'?'online':location?'offline':null,location,start_date:start,end_date:end,registration_deadline:null,prize_text:clean(event.prize_amount)||null,themes:JSON.stringify(array(event.themes).map(t=>string(object(t).name)).filter(Boolean)),application_status:string(event.open_state)||null};
}
async function devpost() {
  const result:Row[]=[],seen=new Set<string>();let expected:number|undefined;
  for(let page=1;page<=30;page++){
    if(page>1)await new Promise(resolve=>setTimeout(resolve,1000));
    const data=object(await jsonURL(`https://devpost.com/api/hackathons?page=${page}&status[]=open&status[]=upcoming`)),meta=object(data.meta),total=Number(meta.total_count),perPage=Number(meta.per_page);
    if(!Array.isArray(data.hackathons)||!data.hackathons.length||!Number.isInteger(total)||!perPage||Math.ceil(total/perPage)>30)throw new Error('Devpost pagination changed or exceeded limit');
    expected??=total;if(expected!==total)throw new Error('Devpost listing changed during pagination; retrying later');
    for(const value of data.hackathons){const event=object(value);if(!['open','upcoming'].includes(string(event.open_state)))continue;const item=parseDevpost(event),key=String(item.content_hash);if(!seen.has(key)){result.push(item);seen.add(key);}}
    if(page>=Math.ceil(total/perPage)){if(seen.size!==total)throw new Error('Devpost listing incomplete');return result;}
  }
  throw new Error('Devpost pagination incomplete');
}
async function saveHackathons(env: Env,items:Row[],source:string,checked:string) {
  const known=new Set((await rows(env.DB,'SELECT content_hash FROM hackathons WHERE source_name=?',[source])).map(r=>String(r.content_hash)));
  const now=nowISO();let inserted=0,updated=0;const statements=[];
  for(const item of items){if(known.has(String(item.content_hash)))updated++;else inserted++;
    const values={...item,status:String(item.end_date)<now?'expired':'active',first_seen_at:now,last_seen_at:now,created_at:now,updated_at:now};
    const keys=Object.keys(values);statements.push(env.DB.prepare(`INSERT INTO hackathons(${keys.join(',')}) VALUES (${keys.map(()=>'?').join(',')}) ON CONFLICT(content_hash) DO UPDATE SET ${keys.filter(k=>!['content_hash','first_seen_at','created_at'].includes(k)).map(k=>`${k}=excluded.${k}`).join(',')}`).bind(...Object.values(values)));
  }
  for(let i=0;i<statements.length;i+=50)await env.DB.batch(statements.slice(i,i+50));
  await env.DB.batch([env.DB.prepare("UPDATE hackathons SET status='unavailable' WHERE source_name=? AND last_seen_at<? AND status='active'").bind(source,checked),env.DB.prepare("UPDATE hackathons SET status='expired' WHERE source_name=? AND COALESCE(end_date,registration_deadline,start_date)<?").bind(source,now)]);
  return {inserted,updated};
}
const categoryWords:Record<string,string[]>={'AI/ML':['openai','llm','anthropic','machine learning','gpt','neural'],'Cybersecurity':['breach','vulnerability','cve','malware','ransomware','security'],'Startups':['startup','funding','series a','venture','accelerator'],'Developer Tools':['developer tool','ide','sdk','api','framework','devtools'],'Cloud':['aws','azure','gcp','cloudflare','kubernetes','docker'],'Programming':['python','javascript','rust','golang','programming'],'Data Science':['data science','pandas','numpy','analytics','dataset']};
function category(title:string,summary:string){const text=(title+' '+summary).toLowerCase();return Object.entries(categoryWords).find(([,words])=>words.some(w=>text.includes(w)))?.[0]||'Other';}
const feeds=[['TechCrunch','https://techcrunch.com/feed/'],['The Verge','https://www.theverge.com/rss/index.xml'],['Ars Technica','https://feeds.arstechnica.com/arstechnica/index'],['Hacker News (Lobsters)','https://lobste.rs/rss'],['OpenAI Blog','https://openai.com/blog/rss.xml'],['Google AI Blog','https://blog.google/technology/ai/rss/'],['Cloudflare Blog','https://blog.cloudflare.com/rss/'],['GitHub Blog','https://github.blog/feed/'],['AWS News Blog','https://aws.amazon.com/blogs/aws/feed/'],['Meta Engineering','https://engineering.fb.com/feed/']] as const;
const parser=new XMLParser({ignoreAttributes:false,attributeNamePrefix:'@_',processEntities:true,htmlEntities:true});
export function parseRSS(xml:string,source:string):Row[] {
  const root=object(parser.parse(xml)),channel=object(object(root.rss).channel),feed=object(root.feed);const entries=array(channel.item||feed.entry);
  if(!entries.length)throw new Error('RSS/Atom entries missing');
  return entries.slice(0,40).flatMap(value=>{
    const entry=object(value);const links=array(entry.link);const link=typeof entry.link==='string'?entry.link:string(object(links.find(v=>!object(v)['@_rel']||object(v)['@_rel']==='alternate'))['@_href']);
    const title=clean(entry.title),url=canonical(link);if(!title||!url)return [];
    const summary=clean(entry.description||entry.summary||entry.content||entry['content:encoded']).slice(0,2000);
    const media=object(entry['media:content']||entry['media:thumbnail']||entry.enclosure),image=canonical(media['@_url']);
    return [{title,url,canonical_url:url,source_name:source,author:clean(typeof entry.author==='object'?object(entry.author).name:entry.author)||null,published_at:date(entry.pubDate||entry.published||entry.updated),summary:summary||null,category:category(title,summary),image_url:image,tags:'[]',score:null,content_hash:contentHash(url,source)}];
  });
}
async function saveArticles(env:Env,items:Row[]) {
  let inserted=0,updated=0;const statements=[];
  const known=new Set((await rows(env.DB,'SELECT url FROM articles')).map(r=>String(r.url)));
  for(const item of items){if(known.has(String(item.url)))updated++;else{inserted++;known.add(String(item.url));}const now=nowISO(),values={...item,first_seen_at:now,last_seen_at:now,created_at:now,updated_at:now};const keys=Object.keys(values);
    statements.push(env.DB.prepare(`INSERT INTO articles(${keys.join(',')}) VALUES (${keys.map(()=>'?').join(',')}) ON CONFLICT(url) DO UPDATE SET title=excluded.title,last_seen_at=excluded.last_seen_at,updated_at=excluded.updated_at,category=excluded.category,summary=COALESCE(excluded.summary,articles.summary),image_url=COALESCE(excluded.image_url,articles.image_url),score=COALESCE(excluded.score,articles.score)`).bind(...Object.values(values)));
  }
  for(let i=0;i<statements.length;i+=50)await env.DB.batch(statements.slice(i,i+50));return {inserted,updated};
}
async function runSource(env:Env,module:Module,source:string,fetchItems:()=>Promise<Row[]>) {
  const checked=nowISO();const row=await env.DB.prepare("INSERT INTO scrape_runs(source_name,module,status,started_at) VALUES (?,?,'running',?) RETURNING id").bind(source,module,checked).first<{id:number}>();
  try{
    const items=await fetchItems();if(!items.length)throw new Error('Source returned no usable items');
    const saved=module==='hackathons'?await saveHackathons(env,items,source,checked):await saveArticles(env,items);
    await env.DB.prepare("UPDATE scrape_runs SET status='success',items_found=?,items_inserted=?,items_updated=?,finished_at=? WHERE id=?").bind(items.length,saved.inserted,saved.updated,nowISO(),row!.id).run();
    console.log(JSON.stringify({event:'source_refreshed',source,count:items.length}));return true;
  }catch(error){
    const detail=error instanceof Error?error.message:'Source refresh failed';
    await env.DB.prepare("UPDATE scrape_runs SET status='failed',error_message=?,finished_at=? WHERE id=?").bind(detail.slice(0,300),nowISO(),row!.id).run();
    console.error(JSON.stringify({event:'source_failed',source,detail}));return false;
  }
}
export async function claimIngestion(env:Env,module:Module,existingOwner?:string) {
  const owner=existingOwner||token(),checked=nowISO();
  const lock=await env.DB.prepare('INSERT INTO ingestion_locks(module,owner,expires_at) VALUES (?,?,?) ON CONFLICT(module) DO UPDATE SET owner=excluded.owner,expires_at=excluded.expires_at WHERE ingestion_locks.expires_at<? OR ingestion_locks.owner=? RETURNING owner').bind(module,owner,new Date(Date.now()+15*60000).toISOString(),checked,existingOwner||'').first<{owner:string}>();
  return lock?.owner===owner?owner:null;
}
export async function ingest(env:Env,module:Module,existingOwner?:string) {
  const owner=await claimIngestion(env,module,existingOwner);if(!owner)return;
  try{
    let successes=0;
    if(module==='hackathons'){
      if(await runSource(env,module,'mlh',async()=>parseMLH(await textURL('https://mlh.io/events'))))successes++;
      if(await runSource(env,module,'devpost',devpost))successes++;
    }else{
      for(const [name,url] of feeds)if(await runSource(env,module,name,async()=>parseRSS(await textURL(url),name)))successes++;
      if(await runSource(env,module,'devto',async()=>{
        const data=await jsonURL('https://dev.to/api/articles?per_page=40&top=1');if(!Array.isArray(data))throw new Error('Dev.to format changed');
        return data.flatMap(value=>{const a=object(value),url=canonical(a.url),title=clean(a.title);if(!url||!title)return [];const summary=clean(a.description);return [{title,url,canonical_url:url,source_name:'Dev.to',author:string(object(a.user).username)||null,published_at:date(a.published_at),summary:summary||null,category:category(title,summary),tags:JSON.stringify(array(a.tag_list)),image_url:canonical(a.cover_image||a.social_image),score:null,content_hash:contentHash(url,'Dev.to')}];});
      }))successes++;
      if(await runSource(env,module,'hacker_news',async()=>{
        const ids=await jsonURL('https://hacker-news.firebaseio.com/v0/topstories.json');if(!Array.isArray(ids))throw new Error('Hacker News format changed');const result:Row[]=[];
        for(const id of ids.slice(0,20)){const a=object(await jsonURL(`https://hacker-news.firebaseio.com/v0/item/${Number(id)}.json`));if(a.type!=='story')continue;const url=canonical(a.url)||`https://news.ycombinator.com/item?id=${id}`,title=clean(a.title);result.push({title,url,canonical_url:url,source_name:'Hacker News',author:string(a.by)||null,published_at:new Date(Number(a.time)*1000).toISOString(),summary:null,category:category(title,''),tags:'[]',image_url:null,score:Number(a.score)||null,content_hash:contentHash(url,'Hacker News')});}return result;
      }))successes++;
    }
    if(!successes)throw new Error('All sources failed');
    if(module==='hackathons'&&successes<2)throw new Error('A hackathon source failed; retrying ingestion');
  }finally{await env.DB.prepare('DELETE FROM ingestion_locks WHERE module=? AND owner=?').bind(module,owner).run();}
}

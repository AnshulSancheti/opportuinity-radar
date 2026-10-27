export type Row = Record<string, unknown>;
export const nowISO = () => new Date().toISOString();
export const visibleSQL = `status='active' AND source_name IN ('mlh','devpost') AND COALESCE(end_date,registration_deadline,start_date)>=? AND (registration_deadline IS NULL OR registration_deadline>=?) AND last_seen_at>=?`;
export const visibleArgs = () => { const now=Date.now(); return [new Date(now).toISOString(),new Date(now).toISOString(),new Date(now-48*3600000).toISOString()]; };
export function present(row: Row) {
  const result = { ...row };
  for (const key of ['tags','themes']) if (typeof result[key] === 'string') result[key] = JSON.parse(result[key] as string);
  return result;
}
export async function rows(db: D1Database, sql: string, args: (string|number|null)[] = []) { return (await db.prepare(sql).bind(...args).all<Row>()).results; }
export async function count(db: D1Database, table: 'articles'|'hackathons', where: string, args: (string|number|null)[] = []) { const row=await db.prepare(`SELECT COUNT(*) AS total FROM ${table} WHERE ${where}`).bind(...args).first<{total:number}>(); return row?.total || 0; }
export class HttpError extends Error { constructor(public status: number, message: string) { super(message); } }
export const ensure = (condition: unknown, status: number, message: string): asserts condition => { if(!condition) throw new HttpError(status,message); };
export function integer(value: string|null, fallback: number, min: number, max: number) { const n=value===null ? fallback : Number(value); if(!Number.isSafeInteger(n)||n<min||n>max)throw new HttpError(422,'Invalid pagination or item ID'); return n; }

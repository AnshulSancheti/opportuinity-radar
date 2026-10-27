import { createHash, randomBytes, scrypt, timingSafeEqual } from 'node:crypto';
export const hash = (value: string) => createHash('sha256').update(value).digest('hex');
export const token = () => randomBytes(32).toString('base64url');
const derive = (password: string, salt: string, n: number, p: number) => new Promise<Buffer>((resolve, reject) => {
  scrypt(password, salt, 64, { N: n, r: 8, p, maxmem: 268435456 }, (error, key) => error ? reject(error) : resolve(key));
});
export async function passwordHash(password: string) {
  const salt = randomBytes(16).toString('hex');
  return `scrypt-v2$32768$3$${salt}$${(await derive(password, salt, 32768, 3)).toString('hex')}`;
}
export async function passwordValid(password: string, encoded?: string) {
  const parts = encoded?.split('$');
  const legacy = parts?.[0] === 'scrypt';
  const salt = legacy ? parts?.[1] : parts?.[3];
  const expected = legacy ? parts?.[2] : parts?.[4];
  const actual = await derive(password, salt || 'radar-dummy-hash-salt', legacy ? 131072 : 32768, legacy ? 1 : 3);
  if (!encoded || (!legacy && parts?.[0] !== 'scrypt-v2') || !expected) return false;
  const decoded = Buffer.from(expected, 'hex');
  return decoded.length === actual.length && timingSafeEqual(decoded, actual);
}
export const secretEqual = (a: string, b: string) => timingSafeEqual(Buffer.from(hash(a), 'hex'), Buffer.from(hash(b), 'hex'));

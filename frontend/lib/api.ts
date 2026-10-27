export const API_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store", credentials: "include", ...options });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail = typeof data.detail === "string" ? data.detail : Array.isArray(data.detail) ? data.detail.map((e: { msg: string }) => e.msg).join(". ") : "Request failed. Please try again.";
    throw new ApiError(res.status, detail);
  }
  return res.json();
}
export const apiGet = <T>(path: string) => request<T>(path);
export const apiPost = <T>(path: string, body: unknown, headers?: Record<string, string>) => request<T>(path, { method: "POST", headers: { "Content-Type": "application/json", ...headers }, body: JSON.stringify(body) });
export const apiDelete = (path: string) => request(path, { method: "DELETE" });

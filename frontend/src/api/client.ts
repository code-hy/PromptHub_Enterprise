const rawBase = (import.meta.env.VITE_API_URL as string | undefined) || "/api/v1";
// Render blueprint injects just the host (e.g. prompthub-api-56ez.onrender.com) via fromService.
// Normalize to a full https:// URL so fetch works on the free-tier.
let API_BASE = rawBase;
if (rawBase && !rawBase.startsWith("http") && !rawBase.startsWith("/")) {
  API_BASE = `https://${rawBase}/api/v1`;
} else if (rawBase && !rawBase.startsWith("http") && rawBase.startsWith("/")) {
  // already a path like /api/v1 — keep as is for local proxy
  API_BASE = rawBase;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `${res.status} ${res.statusText}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined });
const put = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "PUT", body: JSON.stringify(body) });
const del = <T>(path: string) => request<T>(path, { method: "DELETE" });

export const api = {
  get,
  post,
  put,
  del,
};

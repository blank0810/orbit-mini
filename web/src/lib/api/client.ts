// Every fetch happens in the browser, never in a server component.
// Inside Docker, containers reach each other as http://api:8000, which a browser
// cannot resolve; keeping fetches client-side means one base URL instead of two.
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:7302";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  // Headers normalizes every RequestInit header form, including Headers objects.
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${BASE}/api${path}`, {
    ...init,
    // The session is an httpOnly cookie, so JavaScript cannot read it and it
    // must be sent explicitly on cross-origin requests.
    credentials: "include",
    headers,
  });

  if (!res.ok) {
    // Proxies can return non-JSON errors; preserve the HTTP status in that case.
    const body: unknown = await res.json().catch(() => null);
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? body.detail
        : undefined;
    throw new ApiError(
      res.status,
      typeof detail === "string" ? detail : `Request failed (${res.status})`,
    );
  }

  if (res.status === 204) return undefined as T;
  const body = await res.text();
  return body.trim() ? (JSON.parse(body) as T) : (undefined as T);
}

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.status = status;
    this.payload = payload;
  }
}

async function parseJsonSafe(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(path, { credentials: "include" });
  const payload = await parseJsonSafe(res);
  if (!res.ok) {
    const message =
      (payload as any)?.error || `Request failed (${res.status})`;
    throw new ApiError(message, res.status, payload);
  }
  return payload as T;
}

export async function apiPost<T>(
  path: string,
  body?: Record<string, unknown>
): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : "{}"
  });
  const payload = await parseJsonSafe(res);
  if (!res.ok) {
    const message =
      (payload as any)?.error || `Request failed (${res.status})`;
    throw new ApiError(message, res.status, payload);
  }
  return payload as T;
}


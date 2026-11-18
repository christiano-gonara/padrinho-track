export async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!resp.ok) {
    let msg = `Erro ${resp.status}`;
    try {
      const body = (await resp.json()) as { error?: string; message?: string };
      msg = body.error || body.message || msg;
    } catch {
      // ignora parse de corpo não-JSON
    }
    throw new Error(msg);
  }

  return (await resp.json()) as T;
}

export const api = {
  authMe: () => apiFetch<{ authenticated: boolean }>("/api/auth/me"),
  login: (username: string, password: string) =>
    apiFetch<{ ok: boolean }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () => apiFetch<{ ok: boolean }>("/api/auth/logout", { method: "POST" }),
};

export type Tokens = { access: string; refresh: string };

const API_BASE = import.meta.env.VITE_DJANGO_API_BASE ?? "http://localhost:8000";

export async function login(username: string, password: string): Promise<Tokens> {
  const res = await fetch(`${API_BASE}/api/v1/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
    credentials: "include",
  });
  if (!res.ok) throw new Error("Invalid credentials");
  return res.json();
}

export async function refreshToken(refresh: string): Promise<{ access: string }> {
  const res = await fetch(`${API_BASE}/api/v1/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
    credentials: "include",
  });
  if (!res.ok) throw new Error("Refresh failed");
  return res.json();
}

export async function registerUser(payload: {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  role?: string;
  organization?: string;
  phone?: string;
}): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    credentials: "include",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Registration failed");
  }
  return res.json();
}

export async function logout(refresh: string): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/auth/logout/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
    credentials: "include",
  });
  if (!res.ok) throw new Error("Logout failed");
  return res.json();
}



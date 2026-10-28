const BASE = "/api";

export const getToken = () => localStorage.getItem("token");
export const setSession = (t, name) => { localStorage.setItem("token", t); localStorage.setItem("name", name); };
export const clearSession = () => { localStorage.removeItem("token"); localStorage.removeItem("name"); };

export async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(BASE + path, {
    method,
    headers: { "Content-Type": "application/json", ...(getToken() && { Authorization: `Bearer ${getToken()}` }) },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401 && getToken()) { clearSession(); window.location.href = "/login"; }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    throw new Error(Array.isArray(d) ? d.map((e) => e.msg).join(", ") : d || "Request failed");
  }
  return data;
}

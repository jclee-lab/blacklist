// Use empty string for client-side (same-origin, proxied by server.js)
// Server-side uses the full URL
export const API_URL = typeof window === "undefined" 
  ? (process.env.NEXT_PUBLIC_API_URL || "http://blacklist-app:2542")
  : "";

export async function fetcher<T>(url: string): Promise<T> {
  const res = await fetch(`${API_URL}${url}`);
  if (!res.ok) {
    throw new Error(`API Error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

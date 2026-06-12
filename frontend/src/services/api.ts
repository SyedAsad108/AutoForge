/**
 * Base API client for AutoForge Industrial Intelligence Dashboard.
 * Integrates with FastAPI backend using native fetch.
 */

const BASE_URL = "http://127.0.0.1:8000";
const API_KEY = "autoforge-dev-key-2026";

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json",
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error ${response.status}: ${errorText || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

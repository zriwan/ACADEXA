// src/api/client.ts
import axios from "axios";

const TOKEN_KEY = "acadexa_token";

// CRA uses process.env.REACT_APP_*
const API_BASE =
  process.env.REACT_APP_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000, // ✅ FIX 1: prevent infinite loading (10 seconds)
});

// Set/remove token manually (used after login/logout)
export function setAuthToken(token: string | null) {
  const prevToken = localStorage.getItem(TOKEN_KEY); // ✅ track previous

  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    delete api.defaults.headers.common["Authorization"];
    localStorage.removeItem(TOKEN_KEY);
  }

  // ✅ Only notify if token actually changed
  const nextToken = token ?? null;
  const prev = prevToken ?? null;

  if (prev !== nextToken) {
    window.dispatchEvent(new Event("acadexa-auth-changed"));
  }
}

// ✅ Always attach token for every request (Analytics, Voice, etc.)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers = config.headers || {};
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

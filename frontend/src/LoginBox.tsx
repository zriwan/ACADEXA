import React, { useState } from "react";
import { api, setAuthToken } from "./api/client";

const TOKEN_KEY = "acadexa_token";

export default function LoginBox({ onLoggedIn }: { onLoggedIn: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function login(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setLoading(true);

    try {
      const form = new URLSearchParams();
      form.append("username", email);
      form.append("password", password);

      const res = await api.post("/auth/token", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });

      const token = res.data.access_token;

      // ✅ save token
      localStorage.setItem(TOKEN_KEY, token);
      setAuthToken(token);

      // ✅ notify app
      onLoggedIn();
      window.dispatchEvent(new Event("acadexa-auth-changed"));
    } catch (e: any) {
      setErr(e?.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);

    // ✅ notify app
    onLoggedIn();
    window.dispatchEvent(new Event("acadexa-auth-changed"));
  }

  return (
    <div
      style={{
        border: "1px solid #ddd",
        padding: 12,
        borderRadius: 8,
        maxWidth: 420,
      }}
    >
      <h3 style={{ marginTop: 0 }}>Login</h3>

      <form onSubmit={login}>
        <div style={{ display: "grid", gap: 8 }}>
          <input
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          <input
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          <button type="submit" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>

          <button type="button" onClick={logout}>
            Logout
          </button>
        </div>
      </form>

      {err && <p style={{ color: "crimson" }}>{err}</p>}
    </div>
  );
}

import React, { useState } from "react";
import { api, setAuthToken } from "./api/client";
import PasswordInput from "./PasswordInput";

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

  return (
    <div className="login-card">
      <div className="login-header">
        <div className="login-logo">A</div>
        <h1 className="login-title">Welcome to ACADEXA</h1>
        <p className="login-subtitle">University Student & Teacher Portal</p>
      </div>

      <form onSubmit={login}>
        <div className="form-row">
          <label htmlFor="email">Email Address</label>
          <input
            id="email"
            type="email"
            placeholder="Enter your email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div className="form-row">
          <label htmlFor="password">Password</label>
          <PasswordInput
            id="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {err && (
          <div className="alert alert-error" style={{ marginBottom: "1rem" }}>
            {err}
          </div>
        )}

        <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: "100%" }}>
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <div style={{ marginTop: "1.5rem", textAlign: "center" }}>
        <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", margin: 0 }}>
          Secure access to your academic portal
        </p>
      </div>
    </div>
  );
}

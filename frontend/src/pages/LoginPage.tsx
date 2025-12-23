import type { FormEvent } from "react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { apiPost } from "../api/client";
import { Field, TextInput } from "../components/Fields";
import { Toast } from "../components/Toast";
import { useAuth } from "../app/App";

export default function LoginPage() {
  const navigate = useNavigate();
  const { refreshMe } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiPost("/api/auth/login", { email, password });
      await refreshMe();
      navigate("/host");
    } catch (err: any) {
      setError(err?.message || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 520, margin: "0 auto" }}>
        <div className="cardInner">
          <div className="h2">Log in</div>
          <div className="muted" style={{ marginTop: 8 }}>
            Hosts sign in to create and manage rooms.
          </div>
          <form className="stack" style={{ marginTop: 14 }} onSubmit={onSubmit}>
            <Field label="Email">
              <TextInput
                value={email}
                onChange={setEmail}
                placeholder="you@example.com"
                type="email"
                autoComplete="email"
              />
            </Field>
            <Field label="Password">
              <TextInput
                value={password}
                onChange={setPassword}
                placeholder="••••••••"
                type="password"
                autoComplete="current-password"
              />
            </Field>
            {error ? <Toast message={error} /> : null}
            <div className="row" style={{ justifyContent: "space-between" }}>
              <Link className="btn btnGhost" to="/signup">
                Create account
              </Link>
              <button className="btn btnPrimary" disabled={busy}>
                {busy ? "Signing in…" : "Log in"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

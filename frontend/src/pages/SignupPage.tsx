import type { FormEvent } from "react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { apiPost } from "../api/client";
import { Field, TextInput } from "../components/Fields";
import { Toast } from "../components/Toast";
import { useAuth } from "../app/App";

export default function SignupPage() {
  const navigate = useNavigate();
  const { refreshMe } = useAuth();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiPost("/api/auth/signup", { email, username, password });
      await refreshMe();
      navigate("/host");
    } catch (err: any) {
      setError(err?.message || "Signup failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 520, margin: "0 auto" }}>
        <div className="cardInner">
          <div className="h2">Create your host account</div>
          <div className="muted" style={{ marginTop: 8 }}>
            Guests can join rooms without accounts.
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
            <Field label="Username" hint="Shown in the host UI">
              <TextInput
                value={username}
                onChange={setUsername}
                placeholder="dj-nahian"
                autoComplete="username"
              />
            </Field>
            <Field label="Password">
              <TextInput
                value={password}
                onChange={setPassword}
                placeholder="••••••••"
                type="password"
                autoComplete="new-password"
              />
            </Field>
            {error ? <Toast message={error} /> : null}
            <div className="row" style={{ justifyContent: "space-between" }}>
              <Link className="btn btnGhost" to="/login">
                I already have an account
              </Link>
              <button className="btn btnPrimary" disabled={busy}>
                {busy ? "Creating…" : "Create account"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

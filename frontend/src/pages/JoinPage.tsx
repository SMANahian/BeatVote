import type { FormEvent } from "react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { apiPost } from "../api/client";
import { Field, TextInput } from "../components/Fields";
import { Toast } from "../components/Toast";
import type { Room } from "../types";

export default function JoinPage() {
  const navigate = useNavigate();
  const [displayName, setDisplayName] = useState("Guest");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await apiPost<{ room: Room }>("/api/rooms/join", {
        code,
        display_name: displayName
      });
      navigate(`/${res.room._id}/guest`);
    } catch (err: any) {
      setError(err?.message || "Join failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <div className="card" style={{ maxWidth: 720, margin: "0 auto" }}>
        <div className="cardInner">
          <div className="h2">Join a room</div>
          <div className="muted" style={{ marginTop: 8 }}>
            Enter the join code your host shared.
          </div>
          <form className="stack" style={{ marginTop: 14 }} onSubmit={onSubmit}>
            <Field label="Display name" hint="Shown in chat and queue">
              <TextInput
                value={displayName}
                onChange={setDisplayName}
                placeholder="Guest"
                autoComplete="nickname"
              />
            </Field>
            <Field label="Join code" hint="Starts with L- or S-">
              <TextInput
                value={code}
                onChange={setCode}
                placeholder="S-ABCD"
                autoComplete="off"
              />
            </Field>
            {error ? <Toast message={error} /> : null}
            <button className="btn btnPrimary" disabled={busy}>
              {busy ? "Joining…" : "Join"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

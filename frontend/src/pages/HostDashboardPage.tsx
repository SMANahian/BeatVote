import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { apiGet, apiPost } from "../api/client";
import { Field, TextInput } from "../components/Fields";
import { Toast } from "../components/Toast";
import { copy } from "../lib/format";
import type { Room } from "../types";
import { useAuth } from "../app/App";

export default function HostDashboardPage() {
  const { me } = useAuth();
  const [room, setRoom] = useState<Room | null>(null);
  const [name, setName] = useState("My Party");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const isAuthed = me?.authenticated === true;

  const load = async () => {
    const res = await apiGet<{ room: Room | null }>("/api/rooms/mine");
    setRoom(res.room);
  };

  useEffect(() => {
    if (!isAuthed) return;
    load().catch(() => {
      setError("Failed to load your room");
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthed]);

  const hostLink = useMemo(() => {
    if (!room?._id) return null;
    return `/${room._id}/host`;
  }, [room?._id]);

  const onCreate = async () => {
    setError(null);
    setBusy(true);
    try {
      const res = await apiPost<{ room: Room }>("/api/rooms", { name });
      setRoom(res.room);
    } catch (err: any) {
      setError(err?.message || "Failed to create room");
    } finally {
      setBusy(false);
    }
  };

  const onCopy = async (label: string, value: string) => {
    await copy(value);
    setCopied(label);
    setTimeout(() => setCopied(null), 1200);
  };

  if (!isAuthed) {
    return (
      <div className="container">
        <div className="card" style={{ maxWidth: 720, margin: "0 auto" }}>
          <div className="cardInner">
            <div className="h2">Host a room</div>
            <div className="muted" style={{ marginTop: 8 }}>
              Sign in to create a room and get join codes.
            </div>
            <div className="row" style={{ marginTop: 14 }}>
              <Link className="btn btnPrimary" to="/login">
                Log in
              </Link>
              <Link className="btn" to="/signup">
                Create account
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="grid grid2">
        <div className="card">
          <div className="cardInner">
            <div className="h2">Your room</div>
            <div className="muted" style={{ marginTop: 8 }}>
              Create one room per host account (prototype limit).
            </div>
            {error ? <div style={{ marginTop: 12 }}><Toast message={error} /></div> : null}

            {room ? (
              <div className="stack" style={{ marginTop: 14 }}>
                <div className="row">
                  <span className="pill">
                    Room ID: <span className="mono">{room._id}</span>
                  </span>
                  {hostLink ? (
                    <Link className="btn btnPrimary" to={hostLink}>
                      Open host view
                    </Link>
                  ) : null}
                </div>

                <div className="card" style={{ background: "rgba(255,255,255,0.06)" }}>
                  <div className="cardInner">
                    <div className="cardTitle">Share these codes</div>
                    <div className="stack">
                      <div className="row">
                        <span className="badge badgeActive">Suggestor</span>
                        <span className="mono">{room.code_suggestor}</span>
                        {room.code_suggestor ? (
                          <button
                            className="btn"
                            onClick={() => onCopy("Suggestor code", room.code_suggestor!)}
                          >
                            {copied === "Suggestor code" ? "Copied" : "Copy"}
                          </button>
                        ) : null}
                      </div>
                      <div className="row">
                        <span className="badge">Listener</span>
                        <span className="mono">{room.code_listener}</span>
                        {room.code_listener ? (
                          <button
                            className="btn"
                            onClick={() => onCopy("Listener code", room.code_listener!)}
                          >
                            {copied === "Listener code" ? "Copied" : "Copy"}
                          </button>
                        ) : null}
                      </div>
                    </div>
                    <div className="muted2" style={{ marginTop: 10 }}>
                      Guests join at <span className="mono">/join</span> and can vote even as listeners.
                    </div>
                  </div>
                </div>

                {room.host_token ? (
                  <div className="card" style={{ background: "rgba(255,255,255,0.06)" }}>
                    <div className="cardInner">
                      <div className="cardTitle">Extension host token</div>
                      <div className="muted2">
                        Paste this in the extension popup so it can advance the queue without cookies.
                      </div>
                      <div className="row" style={{ marginTop: 10 }}>
                        <span className="mono" style={{ overflowWrap: "anywhere" }}>
                          {room.host_token}
                        </span>
                        <button
                          className="btn"
                          onClick={() => onCopy("Host token", room.host_token!)}
                        >
                          {copied === "Host token" ? "Copied" : "Copy"}
                        </button>
                      </div>
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="stack" style={{ marginTop: 14 }}>
                <Field label="Room name" hint="Shown to guests">
                  <TextInput
                    value={name}
                    onChange={setName}
                    placeholder="My Party"
                    autoComplete="off"
                  />
                </Field>
                <button className="btn btnPrimary" disabled={busy} onClick={onCreate}>
                  {busy ? "Creating…" : "Create room"}
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="cardInner">
            <div className="cardTitle">Extension</div>
            <div className="muted" style={{ lineHeight: 1.6 }}>
              The Chrome/Brave extension keeps your host tab pinned and plays queued songs in a dedicated YouTube tab.
            </div>
            <div className="muted2" style={{ marginTop: 12 }}>
              Load <span className="mono">extension/</span> unpacked, set Room ID + Host Token, and keep this host page open.
            </div>
            <div className="row" style={{ marginTop: 12 }}>
              <Link className="btn" to="/join">
                Test join flow
              </Link>
              {hostLink ? (
                <Link className="btn btnSuccess" to={hostLink}>
                  Open host view
                </Link>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { apiGet, apiPost } from "../api/client";
import { Field, TextInput } from "../components/Fields";
import { Toast } from "../components/Toast";
import YouTubePlayer from "../components/YouTubePlayer";
import { copy, formatDuration } from "../lib/format";
import type { ChatMessage, QueueResponse, Room, Song, YoutubeResult } from "../types";

function QueueItem({
  song,
  isCurrent,
  canVote,
  canHostControl,
  onVote,
  onPlay,
  onRemove
}: {
  song: Song;
  isCurrent: boolean;
  canVote: boolean;
  canHostControl: boolean;
  onVote: (vote: "like" | "dislike" | "clear") => void;
  onPlay: () => void;
  onRemove: () => void;
}) {
  const voteLike = () => onVote(song.my_vote === "like" ? "clear" : "like");
  const voteDislike = () => onVote(song.my_vote === "dislike" ? "clear" : "dislike");

  return (
    <div className="queueItem">
      <div className="thumb">
        {song.thumbnail_url ? <img src={song.thumbnail_url} alt="" /> : null}
      </div>
      <div>
        <div className="queueTitle">
          {song.title}{" "}
          {isCurrent ? <span className="badge badgeActive">Now</span> : null}
        </div>
        <div className="queueMeta">
          <span className="badge">{formatDuration(song.duration_sec)}</span>{" "}
          <span className="badge">Score {song.score}</span>{" "}
          {song.added_by_display_name ? (
            <span className="badge">Added by {song.added_by_display_name}</span>
          ) : null}
        </div>
      </div>
      <div className="row" style={{ justifyContent: "flex-end" }}>
        {canVote ? (
          <>
            <button className="btn" onClick={voteLike}>
              {song.my_vote === "like" ? "Liked" : "Like"}
            </button>
            <button className="btn" onClick={voteDislike}>
              {song.my_vote === "dislike" ? "Disliked" : "Dislike"}
            </button>
          </>
        ) : null}
        {canHostControl ? (
          <>
            <button className="btn" onClick={onPlay}>
              Play
            </button>
            <button className="btn btnDanger" onClick={onRemove}>
              Remove
            </button>
          </>
        ) : null}
      </div>
    </div>
  );
}

function useInterval(callback: () => void, delayMs: number | null) {
  const cbRef = useRef(callback);
  cbRef.current = callback;

  useEffect(() => {
    if (delayMs == null) return;
    const id = window.setInterval(() => cbRef.current(), delayMs);
    return () => window.clearInterval(id);
  }, [delayMs]);
}

export default function RoomPage({ mode }: { mode: "host" | "guest" }) {
  const params = useParams();
  const roomId = params.roomId!;

  const [room, setRoom] = useState<Room | null>(null);
  const [queue, setQueue] = useState<QueueResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQ, setSearchQ] = useState("");
  const [results, setResults] = useState<YoutubeResult[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [chatMsg, setChatMsg] = useState("");

  const [joinName, setJoinName] = useState("Guest");
  const [joinCode, setJoinCode] = useState("");
  const [joinError, setJoinError] = useState<string | null>(null);

  const isHost = room?.role === "host";
  const canSuggest = room?.role === "host" || room?.role === "suggestor";
  const canVote = room?.role === "host" || room?.role === "suggestor" || room?.role === "listener";

  const playerPrefKey = `beatvote.useExtension.${roomId}`;
  const [useExtension, setUseExtension] = useState<boolean>(() => {
    const stored = localStorage.getItem(playerPrefKey);
    return stored ? stored === "true" : true;
  });

  const currentSong = useMemo(() => {
    if (!queue?.queue?.length) return null;
    if (queue.current_song_id) {
      const found = queue.queue.find((s) => s._id === queue.current_song_id);
      if (found) return found;
    }
    return queue.queue[0] || null;
  }, [queue]);

  const refreshRoom = useCallback(async () => {
    const res = await apiGet<{ room: Room }>(`/api/rooms/${roomId}`);
    setRoom(res.room);
  }, [roomId]);

  const refreshQueue = useCallback(async () => {
    const res = await apiGet<QueueResponse>(`/api/rooms/${roomId}/queue`);
    setQueue(res);
    window.dispatchEvent(new Event("queue-updated"));
  }, [roomId]);

  const refreshChat = useCallback(async () => {
    try {
      const res = await apiGet<{ messages: ChatMessage[] }>(
        `/api/rooms/${roomId}/chat`
      );
      setChat(res.messages);
    } catch {
      // not joined yet
    }
  }, [roomId]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    Promise.all([refreshRoom(), refreshQueue(), refreshChat()])
      .catch((err: any) => setError(err?.message || "Failed to load room"))
      .finally(() => setLoading(false));
  }, [refreshChat, refreshQueue, refreshRoom]);

  useInterval(() => {
    refreshQueue().catch(() => {});
    refreshChat().catch(() => {});
  }, 5000);

  useEffect(() => {
    localStorage.setItem(playerPrefKey, useExtension.toString());
  }, [playerPrefKey, useExtension]);

  useEffect(() => {
    const el = document.getElementById("use-extension");
    if (!el) return;
    // no-op; retained for the extension content script to bind.
  }, []);

  useEffect(() => {
    if (!canSuggest) {
      setResults([]);
      return;
    }
    const q = searchQ.trim();
    if (q.length < 2) {
      setResults([]);
      setSearchError(null);
      return;
    }
    const handle = window.setTimeout(async () => {
      setSearchError(null);
      try {
        const res = await apiGet<{ results: YoutubeResult[] }>(
          `/api/youtube/search?q=${encodeURIComponent(q)}&room_id=${encodeURIComponent(
            roomId
          )}`
        );
        setResults(res.results);
      } catch (err: any) {
        setSearchError(err?.message || "Search failed");
      }
    }, 400);
    return () => window.clearTimeout(handle);
  }, [canSuggest, roomId, searchQ]);

  const joinInline = async () => {
    setJoinError(null);
    try {
      const res = await apiPost<{ room: Room }>("/api/rooms/join", {
        code: joinCode,
        display_name: joinName
      });
      setRoom(res.room);
      setJoinCode("");
      await refreshChat();
    } catch (err: any) {
      setJoinError(err?.message || "Join failed");
    }
  };

  const vote = async (songId: string, v: "like" | "dislike" | "clear") => {
    await apiPost(`/api/rooms/${roomId}/queue/${songId}/vote`, { vote: v });
    await refreshQueue();
  };

  const add = async (r: YoutubeResult) => {
    await apiPost(`/api/rooms/${roomId}/queue/add`, {
      video_id: r.video_id,
      title: r.title,
      thumbnail_url: r.thumbnail_url,
      duration_sec: r.duration_sec
    });
    setSearchQ("");
    setResults([]);
    await refreshQueue();
  };

  const hostPlay = async (songId: string) => {
    await apiPost(`/api/rooms/${roomId}/queue/${songId}/play`);
    await refreshQueue();
  };

  const hostRemove = async (songId: string) => {
    await apiPost(`/api/rooms/${roomId}/queue/${songId}/remove`);
    await refreshQueue();
  };

  const hostNext = async () => {
    await apiPost(`/api/rooms/${roomId}/queue/next`);
    await refreshQueue();
  };

  const sendChat = async () => {
    const msg = chatMsg.trim();
    if (!msg) return;
    await apiPost(`/api/rooms/${roomId}/chat`, { message: msg });
    setChatMsg("");
    await refreshChat();
  };

  const onPlayerEnded = async () => {
    try {
      await hostNext();
    } catch {
      // ignore
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="card">
          <div className="cardInner">Loading…</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="card">
          <div className="cardInner">
            <Toast message={error} />
          </div>
        </div>
      </div>
    );
  }

  if (!room) {
    return (
      <div className="container">
        <div className="card">
          <div className="cardInner">Room not found.</div>
        </div>
      </div>
    );
  }

  if (mode === "host" && !isHost) {
    return (
      <div className="container">
        <div className="card">
          <div className="cardInner">
            <div className="h2">Host access required</div>
            <div className="muted" style={{ marginTop: 8 }}>
              Open your host room from <Link to="/host" className="btn btnGhost">/host</Link>.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      {mode === "host" && isHost ? (
        <div
          id="beatvote-extension-config"
          data-room-id={roomId}
          data-host-token={room.host_token ?? ""}
          data-server-url={window.location.origin}
          data-use-extension={useExtension ? "true" : "false"}
          style={{ display: "none" }}
        />
      ) : null}
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 14 }}>
        <div className="stack" style={{ gap: 6 }}>
          <div className="h2">{room.name}</div>
          <div className="row">
            <span className="pill">
              Room <span className="mono">{room._id}</span>
            </span>
            <span className="pill">
              Role <span className="mono">{room.role ?? "none"}</span>
            </span>
            {mode === "guest" ? (
              <Link className="btn btnGhost" to="/join">
                Join another room
              </Link>
            ) : null}
          </div>
        </div>
        {mode === "host" ? (
          <div className="row">
            <button
              id="use-extension"
              className="btn"
              onClick={() => setUseExtension((v) => !v)}
            >
              {useExtension ? "Use Web Player" : "Use Extension Player"}
            </button>
            <button className="btn btnSuccess" onClick={hostNext}>
              Next
            </button>
          </div>
        ) : null}
      </div>

      <div className="split">
        <div className="stack">
          {mode === "host" ? (
            <div className="card">
              <div className="cardInner">
                <div className="cardTitle">Now Playing</div>
                <div className="row" style={{ justifyContent: "space-between" }}>
                  <div className="muted">
                    {currentSong ? currentSong.title : "Queue is empty"}
                  </div>
                  {room.host_token ? (
                    <button
                      className="btn"
                      onClick={() => copy(room.host_token!)}
                      title="Copy host token for the extension"
                    >
                      Copy host token
                    </button>
                  ) : null}
                </div>
                <div style={{ marginTop: 12 }}>
                  <YouTubePlayer
                    videoId={useExtension ? null : currentSong?.video_id || null}
                    onEnded={onPlayerEnded}
                    hidden={useExtension}
                  />
                  {useExtension ? (
                    <div className="toast" style={{ marginTop: 12 }}>
                      Extension mode: the browser extension controls playback in a separate YouTube tab.
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          ) : null}

          <div className="card">
            <div className="cardInner">
              <div className="cardTitle">Queue</div>
              {queue?.queue?.length ? (
                <div className="stack">
                  {queue.queue.map((s) => (
                    <QueueItem
                      key={s._id}
                      song={s}
                      isCurrent={!!queue.current_song_id && s._id === queue.current_song_id}
                      canVote={canVote}
                      canHostControl={mode === "host"}
                      onVote={(v) => vote(s._id, v)}
                      onPlay={() => hostPlay(s._id)}
                      onRemove={() => hostRemove(s._id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="muted">No songs yet — add one!</div>
              )}
            </div>
          </div>

          {canSuggest ? (
            <div className="card">
              <div className="cardInner">
                <div className="cardTitle">Search YouTube</div>
                <TextInput
                  value={searchQ}
                  onChange={setSearchQ}
                  placeholder="Search for a song…"
                  autoComplete="off"
                />
                {searchError ? <div style={{ marginTop: 10 }}><Toast message={searchError} /></div> : null}
                {results.length ? (
                  <div className="stack" style={{ marginTop: 12 }}>
                    {results.map((r) => (
                      <div key={r.video_id} className="queueItem">
                        <div className="thumb">
                          {r.thumbnail_url ? <img src={r.thumbnail_url} alt="" /> : null}
                        </div>
                        <div>
                          <div className="queueTitle">{r.title}</div>
                          <div className="queueMeta">
                            <span className="badge">{r.channel}</span>{" "}
                            <span className="badge">{formatDuration(r.duration_sec)}</span>
                          </div>
                        </div>
                        <div className="row" style={{ justifyContent: "flex-end" }}>
                          <button className="btn btnSuccess" onClick={() => add(r)}>
                            Add
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="muted2" style={{ marginTop: 10 }}>
                    Type at least 2 characters to search.
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="cardInner">
                <div className="cardTitle">Want to suggest songs?</div>
                <div className="muted">
                  Join with a suggestor code to unlock search + add.
                </div>
                <div className="row" style={{ marginTop: 12 }}>
                  <Link className="btn btnPrimary" to="/join">
                    Join with code
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="stack">
          {mode === "host" ? (
            <div className="card">
              <div className="cardInner">
                <div className="cardTitle">Share codes</div>
                <div className="stack">
                  <div className="row">
                    <span className="badge badgeActive">Suggestor</span>
                    <span className="mono">{room.code_suggestor}</span>
                    {room.code_suggestor ? (
                      <button className="btn" onClick={() => copy(room.code_suggestor!)}>
                        Copy
                      </button>
                    ) : null}
                  </div>
                  <div className="row">
                    <span className="badge">Listener</span>
                    <span className="mono">{room.code_listener}</span>
                    {room.code_listener ? (
                      <button className="btn" onClick={() => copy(room.code_listener!)}>
                        Copy
                      </button>
                    ) : null}
                  </div>
                </div>
                <div className="muted2" style={{ marginTop: 10 }}>
                  Guests join at <span className="mono">/join</span>.
                </div>
              </div>
            </div>
          ) : null}

          {mode === "guest" && !room.role ? (
            <div className="card">
              <div className="cardInner">
                <div className="cardTitle">Join this room</div>
                <div className="muted">
                  You can view the queue, but you need a join code to vote or chat.
                </div>
                <div className="stack" style={{ marginTop: 12 }}>
                  <Field label="Display name">
                    <TextInput value={joinName} onChange={setJoinName} />
                  </Field>
                  <Field label="Join code">
                    <TextInput value={joinCode} onChange={setJoinCode} placeholder="L-ABCD / S-ABCD" />
                  </Field>
                  {joinError ? <Toast message={joinError} /> : null}
                  <button className="btn btnPrimary" onClick={joinInline}>
                    Join
                  </button>
                </div>
              </div>
            </div>
          ) : null}

          <div className="card">
            <div className="cardInner">
              <div className="cardTitle">Chat</div>
              {room.role ? (
                <>
                  <div
                    className="stack"
                    style={{
                      maxHeight: 320,
                      overflow: "auto",
                      paddingRight: 6
                    }}
                  >
                    {chat.length ? (
                      chat.map((m) => (
                        <div key={m._id} className="toast">
                          <div style={{ fontWeight: 700 }}>{m.sender_name}</div>
                          <div style={{ marginTop: 6, whiteSpace: "pre-wrap" }}>
                            {m.message}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="muted">No messages yet.</div>
                    )}
                  </div>
                  <div className="row" style={{ marginTop: 12 }}>
                    <input
                      className="input"
                      value={chatMsg}
                      onChange={(e) => setChatMsg(e.target.value)}
                      placeholder="Say something…"
                      onKeyDown={(e) => {
                        if (e.key === "Enter") sendChat().catch(() => {});
                      }}
                    />
                    <button className="btn btnSuccess" onClick={() => sendChat().catch(() => {})}>
                      Send
                    </button>
                  </div>
                </>
              ) : (
                <div className="muted">
                  Join the room to chat.
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <div className="cardInner">
              <div className="cardTitle">Links</div>
              <div className="stack">
                <div className="row">
                  <Link className="btn" to={`/${roomId}/guest`}>
                    Guest view
                  </Link>
                  <Link className="btn" to={`/${roomId}/host`}>
                    Host view
                  </Link>
                </div>
                <div className="row">
                  <button className="btn" onClick={() => copy(window.location.href)}>
                    Copy page URL
                  </button>
                  <button className="btn" onClick={() => copy(roomId)}>
                    Copy room ID
                  </button>
                </div>
              </div>
              <div className="muted2" style={{ marginTop: 10 }}>
                The extension uses Room ID + Host Token (host-only) to run playback.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

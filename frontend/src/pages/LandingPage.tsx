import { Link } from "react-router-dom";

export default function LandingPage() {
  return (
    <div className="container">
      <div className="grid grid2">
        <div className="card">
          <div className="cardInner">
            <div className="h1">Make the room decide the next song.</div>
            <p className="lead" style={{ marginTop: 12 }}>
              BeatVote is a collaborative music queue for karaoke nights and
              house parties. Search YouTube, add songs, vote, and keep playback
              moving with a host-controlled player (web or extension).
            </p>
            <div className="row" style={{ marginTop: 16 }}>
              <Link className="btn btnPrimary" to="/host">
                Host a room
              </Link>
              <Link className="btn" to="/join">
                Join with code
              </Link>
            </div>
            <div className="row" style={{ marginTop: 16 }}>
              <span className="pill">No accounts needed for guests</span>
              <span className="pill">Votes reorder the queue</span>
              <span className="pill">Chrome / Brave extension player</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="cardInner">
            <div className="cardTitle">How it works</div>
            <div className="stack">
              <div className="toast">
                <div style={{ fontWeight: 700 }}>1) Host</div>
                <div className="muted" style={{ marginTop: 6 }}>
                  Create a room, share join codes, and control playback.
                </div>
              </div>
              <div className="toast">
                <div style={{ fontWeight: 700 }}>2) Guests</div>
                <div className="muted" style={{ marginTop: 6 }}>
                  Suggest songs (if allowed) and vote to push favorites up.
                </div>
              </div>
              <div className="toast">
                <div style={{ fontWeight: 700 }}>3) Play</div>
                <div className="muted" style={{ marginTop: 6 }}>
                  Use the extension for hands-off next-song, or the web player
                  with auto-advance.
                </div>
              </div>
            </div>
            <div className="muted2" style={{ marginTop: 12 }}>
              Tip: For dev with Vite proxy, open the app on{" "}
              <span className="mono">http://127.0.0.1:5173</span>.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


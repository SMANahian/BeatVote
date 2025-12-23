import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Link, Route, Routes, useNavigate } from "react-router-dom";

import { apiGet, apiPost } from "../api/client";
import LandingPage from "../pages/LandingPage";
import LoginPage from "../pages/LoginPage";
import SignupPage from "../pages/SignupPage";
import HostDashboardPage from "../pages/HostDashboardPage";
import JoinPage from "../pages/JoinPage";
import RoomPage from "../pages/RoomPage";
import type { MeResponse } from "../types";

type AuthContextValue = {
  me: MeResponse | null;
  refreshMe: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("AuthContext missing");
  return ctx;
}

function Nav() {
  const { me, refreshMe } = useAuth();
  const navigate = useNavigate();

  const onLogout = async () => {
    await apiPost("/api/auth/logout");
    await refreshMe();
    navigate("/");
  };

  return (
    <div className="nav">
      <div className="navInner">
        <Link to="/" className="brand" aria-label="BeatVote home">
          <div className="brandMark" />
          <div>BeatVote</div>
        </Link>
        <div className="navLinks">
          <Link className="btn btnGhost" to="/join">
            Join
          </Link>
          <Link className="btn btnGhost" to="/host">
            Host
          </Link>
          {me?.authenticated ? (
            <>
              <div className="chip">
                <span className="muted2">Signed in as</span>
                <span style={{ fontWeight: 700 }}>{me.user.username}</span>
              </div>
              <button className="btn" onClick={onLogout}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link className="btn" to="/login">
                Login
              </Link>
              <Link className="btn btnPrimary" to="/signup">
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function NotFound() {
  return (
    <div className="container">
      <div className="card">
        <div className="cardInner">
          <div className="h2">Page not found</div>
          <div className="muted" style={{ marginTop: 8 }}>
            That route doesn’t exist.
          </div>
          <div style={{ marginTop: 14 }}>
            <Link className="btn btnPrimary" to="/">
              Go home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [me, setMe] = useState<MeResponse | null>(null);

  const refreshMe = useCallback(async () => {
    const res = await apiGet<MeResponse>("/api/me");
    setMe(res);
  }, []);

  useEffect(() => {
    refreshMe().catch(() => {
      setMe({ authenticated: false, guest: { id: null, name: null } });
    });
  }, [refreshMe]);

  const value = useMemo(() => ({ me, refreshMe }), [me, refreshMe]);

  return (
    <AuthContext.Provider value={value}>
      <Nav />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/host" element={<HostDashboardPage />} />
        <Route path="/join" element={<JoinPage />} />
        <Route path="/:roomId/host" element={<RoomPage mode="host" />} />
        <Route path="/:roomId/guest" element={<RoomPage mode="guest" />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthContext.Provider>
  );
}


import React, { useEffect, useRef } from "react";

type YTPlayer = any;
type YTNamespace = any;

let ytApiPromise: Promise<YTNamespace> | null = null;

function loadYouTubeIframeApi(): Promise<YTNamespace> {
  if (ytApiPromise) return ytApiPromise;
  ytApiPromise = new Promise((resolve) => {
    const w = window as any;
    if (w.YT?.Player) {
      resolve(w.YT);
      return;
    }

    const existing = document.querySelector(
      'script[src="https://www.youtube.com/iframe_api"]'
    );
    if (!existing) {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.body.appendChild(tag);
    }

    const prev = w.onYouTubeIframeAPIReady;
    w.onYouTubeIframeAPIReady = () => {
      if (typeof prev === "function") prev();
      resolve(w.YT);
    };
  });
  return ytApiPromise;
}

export default function YouTubePlayer({
  videoId,
  onEnded,
  hidden
}: {
  videoId: string | null;
  onEnded: () => void;
  hidden?: boolean;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const playerRef = useRef<YTPlayer | null>(null);

  useEffect(() => {
    if (!videoId) return;
    let cancelled = false;

    loadYouTubeIframeApi()
      .then((YT) => {
        if (cancelled || !hostRef.current) return;
        const onStateChange = (evt: any) => {
          const ended = evt?.data === YT.PlayerState?.ENDED;
          if (ended) onEnded();
        };
        const onError = () => onEnded();

        if (!playerRef.current) {
          playerRef.current = new YT.Player(hostRef.current, {
            height: "100%",
            width: "100%",
            videoId,
            playerVars: { autoplay: 1, modestbranding: 1, rel: 0 },
            events: { onStateChange, onError }
          });
          return;
        }

        try {
          playerRef.current.loadVideoById(videoId);
        } catch {
          // ignore
        }
      })
      .catch(() => {
        // ignore
      });

    return () => {
      cancelled = true;
    };
  }, [videoId, onEnded]);

  useEffect(() => {
    return () => {
      try {
        playerRef.current?.destroy?.();
      } catch {
        // ignore
      }
      playerRef.current = null;
    };
  }, []);

  return (
    <div
      className="videoFrame"
      style={{ display: hidden ? "none" : "block", padding: 0 }}
      ref={(el) => {
        hostRef.current = el;
      }}
    />
  );
}


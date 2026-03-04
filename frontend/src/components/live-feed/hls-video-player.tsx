"use client";

import { useEffect, useMemo, useState } from "react";

type HlsVideoPlayerProps = {
  src?: string;
  title: string;
};

export function HlsVideoPlayer({ src, title }: HlsVideoPlayerProps) {
  const [reloadKey, setReloadKey] = useState(0);
  const [playerState, setPlayerState] = useState<"idle" | "loading" | "playing" | "error">("loading");

  useEffect(() => {
    if (playerState !== "loading") {
      return;
    }

    const timeout = window.setTimeout(() => {
      setPlayerState("error");
    }, 6000);

    return () => window.clearTimeout(timeout);
  }, [playerState, reloadKey, src]);

  const unsupported = useMemo(() => {
    if (typeof document === "undefined") {
      return false;
    }

    const probe = document.createElement("video");
    return probe.canPlayType("application/vnd.apple.mpegurl") === "";
  }, []);

  if (!src) {
    return (
      <div className="flex h-full items-center justify-center px-4 text-center text-sm text-slate-500 dark:text-slate-400">
        Stream unavailable.
      </div>
    );
  }

  if (unsupported) {
    return (
      <div className="flex h-full items-center justify-center px-4 text-center text-sm text-slate-500 dark:text-slate-400">
        This browser does not support native HLS playback.
      </div>
    );
  }

  return (
    <div className="relative h-full w-full bg-black">
      <video
        key={`${src}-${reloadKey}`}
        className="h-full w-full bg-black object-cover"
        autoPlay
        muted
        loop
        playsInline
        controls
        preload="metadata"
        src={src}
        aria-label={title}
        onLoadStart={() => setPlayerState("loading")}
        onLoadedData={() => setPlayerState("playing")}
        onCanPlay={() => setPlayerState("playing")}
        onPlaying={() => setPlayerState("playing")}
        onWaiting={() => setPlayerState("loading")}
        onStalled={() => setPlayerState("error")}
        onError={() => setPlayerState("error")}
      />

      {playerState === "loading" ? (
        <div className="absolute inset-0 flex items-center justify-center bg-black/35 text-sm font-medium text-white">
          Loading stream...
        </div>
      ) : null}

      {playerState === "error" ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/65 px-4 text-center text-sm text-slate-100">
          <p>Stream interrupted.</p>
          <button
            type="button"
            onClick={() => {
              setPlayerState("loading");
              setReloadKey((prev) => prev + 1);
            }}
            className="inline-flex items-center rounded-md border border-slate-300 bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-800 transition-colors hover:bg-slate-200"
          >
            Retry
          </button>
        </div>
      ) : null}
    </div>
  );
}

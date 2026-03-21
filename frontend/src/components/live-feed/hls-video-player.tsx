"use client";

import Hls from "hls.js";
import { useEffect, useMemo, useRef, useState } from "react";

type HlsVideoPlayerProps = {
  src?: string;
  title: string;
};

export function HlsVideoPlayer({ src, title }: HlsVideoPlayerProps) {
  const [reloadKey, setReloadKey] = useState(0);

  const unsupported = useMemo(() => {
    if (typeof window === "undefined") {
      return false;
    }

    return !Hls.isSupported();
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
    <RuntimeVideo
      key={`${src}-${reloadKey}`}
      src={src}
      title={title}
      onRetry={() => setReloadKey((prev) => prev + 1)}
    />
  );
}

function RuntimeVideo({ src, title, onRetry }: { src: string; title: string; onRetry: () => void }) {
  const [playerState, setPlayerState] = useState<"loading" | "playing" | "error">("loading");
  const [hasPlayed, setHasPlayed] = useState(false);
  const hasPlayedRef = useRef(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const showLoadingOverlay = !hasPlayed && playerState === "loading";

  useEffect(() => {
    if (playerState !== "loading") {
      return;
    }

    const timeout = window.setTimeout(() => {
      setPlayerState("error");
    }, hasPlayedRef.current ? 15000 : 12000);

    return () => window.clearTimeout(timeout);
  }, [playerState]);

  useEffect(() => {
    const video = videoRef.current;

    if (!video) {
      return;
    }

    if (!Hls.isSupported()) {
      return;
    }

    const hls = new Hls({
      lowLatencyMode: true,
      backBufferLength: 90,
    });

    hls.attachMedia(video);
    hls.on(Hls.Events.MEDIA_ATTACHED, () => {
      hls.loadSource(src);
    });
    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      void video.play().catch(() => {
        // Playback can be blocked until enough data is buffered.
      });
    });
    hls.on(Hls.Events.ERROR, (_, data) => {
      if (!data.fatal) {
        return;
      }

      switch (data.type) {
        case Hls.ErrorTypes.NETWORK_ERROR:
          hls.startLoad();
          break;
        case Hls.ErrorTypes.MEDIA_ERROR:
          hls.recoverMediaError();
          break;
        default:
          setPlayerState("error");
          hls.destroy();
      }
    });

    return () => {
      hls.destroy();
      video.removeAttribute("src");
      video.load();
    };
  }, [src]);

  return (
    <div className="relative h-full w-full bg-black">
      <video
        ref={videoRef}
        className="h-full w-full bg-black object-cover"
        autoPlay
        muted
        playsInline
        controls
        preload="metadata"
        aria-label={title}
        onLoadStart={() => setPlayerState("loading")}
        onLoadedData={() => setPlayerState("playing")}
        onCanPlay={() => setPlayerState("playing")}
        onPlaying={() => {
          hasPlayedRef.current = true;
          setHasPlayed(true);
          setPlayerState("playing");
        }}
        onWaiting={() => setPlayerState("loading")}
        onStalled={() => setPlayerState("loading")}
        onError={() => setPlayerState("error")}
      />

      {showLoadingOverlay ? (
        <div className="absolute inset-0 flex items-center justify-center bg-black/35 text-sm font-medium text-white">
          Loading stream...
        </div>
      ) : null}

      {playerState === "error" ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-black/65 px-4 text-center text-sm text-slate-100">
          <p>Stream interrupted.</p>
          <button
            type="button"
            onClick={onRetry}
            className="inline-flex items-center rounded-md border border-slate-300 bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-800 transition-colors hover:bg-slate-200"
          >
            Retry
          </button>
        </div>
      ) : null}
    </div>
  );
}

"use client";

import { useMemo } from "react";

type HlsVideoPlayerProps = {
  src?: string;
  title: string;
};

export function HlsVideoPlayer({ src, title }: HlsVideoPlayerProps) {
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
    <video
      key={src}
      className="h-full w-full bg-black object-cover"
      autoPlay
      muted
      loop
      playsInline
      controls
      preload="metadata"
      src={src}
      aria-label={title}
    />
  );
}

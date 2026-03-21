"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getStreams, type StreamInfo } from "@/lib/api/streams";

type UseLiveStreamsResult = {
  visualStream?: StreamInfo;
  thermalStream?: StreamInfo;
  isLoading: boolean;
  errorMessage?: string;
  refresh: () => Promise<void>;
};

export function useLiveStreams(): UseLiveStreamsResult {
  const [streams, setStreams] = useState<StreamInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | undefined>(undefined);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(undefined);

    try {
      const response = await getStreams();
      setStreams(response.streams);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load streams";
      setErrorMessage(message);
      setStreams([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const visualStream = useMemo(
    () => streams.find((stream) => stream.name === "visual"),
    [streams],
  );
  const thermalStream = useMemo(
    () => streams.find((stream) => stream.name === "thermal"),
    [streams],
  );

  return {
    visualStream,
    thermalStream,
    isLoading,
    errorMessage,
    refresh,
  };
}

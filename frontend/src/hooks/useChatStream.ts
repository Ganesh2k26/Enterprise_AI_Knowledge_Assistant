import { useCallback, useRef, useState } from "react";
import { store } from "@/store";

/**
 * Consumes an SSE-style streaming endpoint token-by-token using fetch +
 * ReadableStream (not EventSource, since EventSource doesn't support POST
 * bodies or custom Authorization headers). Used for both new messages and
 * regeneration, which share the same wire format.
 */
export function useChatStream() {
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const consume = useCallback(async (url: string, body: unknown, onDone: (fullText: string) => void) => {
    setStreamingText("");
    setIsStreaming(true);
    const controller = new AbortController();
    abortRef.current = controller;

    const token = store.getState().auth.accessToken;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    if (!response.ok) {
      let detail = `Chat request failed (${response.status})`;
      try {
        const err = await response.json();
        if (err?.detail) detail = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
      } catch {
        /* ignore parse errors */
      }
      setStreamingText(detail);
      setIsStreaming(false);
      onDone(detail);
      return;
    }

    if (!response.body) {
      setIsStreaming(false);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let full = "";
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";
      for (const evt of events) {
        if (evt.startsWith("data: ")) {
          const chunk = evt.slice(6).replace(/\\n/g, "\n");
          full += chunk;
          setStreamingText((prev) => prev + chunk);
        }
      }
    }

    setIsStreaming(false);
    onDone(full);
  }, []);

  const send = useCallback(
    (sessionId: string, message: string, onDone: (fullText: string) => void) =>
      consume("/api/v1/chat/messages", { session_id: sessionId, message }, onDone),
    [consume]
  );

  const regenerate = useCallback(
    (sessionId: string, onDone: (fullText: string) => void) =>
      consume(`/api/v1/chat/sessions/${sessionId}/regenerate`, null, onDone),
    [consume]
  );

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return { streamingText, isStreaming, send, regenerate, stop };
}

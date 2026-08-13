import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, Pencil, Plus, Send, Sparkles, Square, MessagesSquare, Trash2 } from "lucide-react";
import { chatApi, documentsApi } from "@/services/api";
import { useChatStream } from "@/hooks/useChatStream";
import MessageBubble from "@/components/chat/MessageBubble";
import type { ChatMessage, ChatSession, Document } from "@/types";

export default function ChatPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [input, setInput] = useState("");
  const [pendingUserMsg, setPendingUserMsg] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { streamingText, isStreaming, send, regenerate, stop } = useChatStream();

  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: async () => (await chatApi.listSessions()).data as ChatSession[],
  });
  const { data: session, refetch } = useQuery({
    queryKey: ["chat-session", sessionId],
    queryFn: async () => (await chatApi.getSession(sessionId!)).data,
    enabled: !!sessionId,
  });
  const { data: documents } = useQuery({
    queryKey: ["documents"],
    queryFn: async () => (await documentsApi.list()).data as Document[],
  });

  const createSessionMutation = useMutation({
    mutationFn: () => chatApi.createSession("New Chat", []),
    onSuccess: ({ data }) => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      navigate(`/chat/${data.id}`);
    },
  });

  const deleteSessionMutation = useMutation({
    mutationFn: (id: string) => chatApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      if (sessionId) navigate("/chat");
    },
  });

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: isStreaming ? "auto" : "smooth" });
  }, [session?.messages, streamingText, isStreaming]);

  const handleSend = async () => {
    if (!input.trim()) return;
    let activeSessionId = sessionId;
    if (!activeSessionId) {
      const { data } = await chatApi.createSession(input.slice(0, 60), []);
      activeSessionId = data.id;
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      navigate(`/chat/${activeSessionId}`, { replace: true });
    }
    const message = input;
    setInput("");
    setPendingUserMsg(message);
    await send(activeSessionId!, message, async () => {
      setPendingUserMsg(null);
      await refetch();
    });
  };

  const handleRegenerate = async () => {
    if (!sessionId) return;
    await regenerate(sessionId, async () => {
      await refetch();
    });
  };

  const handleAskSuggestion = (question: string) => {
    setInput(question);
  };

  const handleRename = async () => {
    if (!sessionId || !session) return;
    const title = prompt("Rename chat", session.title);
    if (title && title.trim()) {
      await chatApi.rename(sessionId, title.trim());
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] });
      refetch();
    }
  };

  const handleExport = async () => {
    if (!sessionId) return;
    const { data } = await chatApi.export(sessionId);
    const blob = new Blob([data.content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = data.filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const readyDocs = documents?.filter((d) => d.status === "ready") ?? [];
  const lastAssistantId = [...(session?.messages ?? [])].reverse().find((m: ChatMessage) => m.role === "assistant")?.id;
  const lastMessage: ChatMessage | undefined = session?.messages?.[session.messages.length - 1];
  const suggestions = !isStreaming ? lastMessage?.token_usage?.suggested_questions ?? [] : [];

  return (
    <div className="flex h-full">
      <aside className="hidden w-72 shrink-0 flex-col border-r border-ink-700/20 dark:border-ink-700/40 lg:flex">
        <div className="p-4">
          <button
            onClick={() => createSessionMutation.mutate()}
            className="flex w-full items-center justify-center gap-2 rounded-lg border border-signal/30 bg-signal/10 py-2.5 text-sm font-medium text-signal hover:bg-signal/15"
          >
            <Plus size={15} /> New chat
          </button>
        </div>
        <div className="flex-1 space-y-1 overflow-y-auto scrollbar-thin px-2">
          {sessions?.map((s) => (
            <div
              key={s.id}
              className={`group flex items-center justify-between rounded-lg px-3 py-2.5 text-sm cursor-pointer ${
                s.id === sessionId
                  ? "bg-signal/15 text-signal"
                  : "text-ink-700/70 hover:bg-ink-700/5 dark:text-paper-200/70 dark:hover:bg-white/5"
              }`}
              onClick={() => navigate(`/chat/${s.id}`)}
            >
              <span className="truncate">{s.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  deleteSessionMutation.mutate(s.id);
                }}
                className="opacity-0 group-hover:opacity-100 text-ink-700/40 hover:text-red-400"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
          {!sessions?.length && (
            <p className="px-3 py-6 text-center text-sm text-ink-700/40 dark:text-paper-200/30">
              No chats yet. Start one above.
            </p>
          )}
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        {sessionId && session && (
          <div className="flex items-center justify-between border-b border-ink-700/20 px-4 py-2.5 dark:border-ink-700/40">
            <span className="truncate text-sm font-medium text-ink-900 dark:text-paper-50">{session.title}</span>
            <div className="flex items-center gap-1">
              <button onClick={handleRename} title="Rename chat" className="rounded p-1.5 text-ink-700/50 hover:bg-ink-700/5 dark:text-paper-200/50 dark:hover:bg-white/5">
                <Pencil size={14} />
              </button>
              <button onClick={handleExport} title="Export chat" className="rounded p-1.5 text-ink-700/50 hover:bg-ink-700/5 dark:text-paper-200/50 dark:hover:bg-white/5">
                <Download size={14} />
              </button>
            </div>
          </div>
        )}

        {!sessionId && !session ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 px-6 text-center">
            <MessagesSquare size={32} className="text-signal/60" />
            <h2 className="font-display text-2xl text-ink-900 dark:text-paper-50">Ask your documents anything</h2>
            <p className="max-w-md text-sm text-ink-700/60 dark:text-paper-200/50">
              {readyDocs.length
                ? `${readyDocs.length} document${readyDocs.length > 1 ? "s" : ""} ready. Start typing below to begin.`
                : "Upload a document first, then come back here to chat with it."}
            </p>
          </div>
        ) : (
          <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto scrollbar-thin px-6 py-6">
            {session?.messages?.map((m: ChatMessage) => (
              <MessageBubble
                key={m.id}
                messageId={m.id}
                role={m.role as "user" | "assistant"}
                content={m.content}
                citations={m.citations}
                confidence={m.confidence_score}
                isLatestAssistant={m.id === lastAssistantId}
                onRegenerate={handleRegenerate}
              />
            ))}
            {pendingUserMsg && <MessageBubble role="user" content={pendingUserMsg} />}
            {isStreaming && <MessageBubble role="assistant" content={streamingText} isStreaming />}

            {!!suggestions.length && (
              <div className="flex flex-wrap gap-2 pl-10">
                {suggestions.map((q: string, i: number) => (
                  <button
                    key={i}
                    onClick={() => handleAskSuggestion(q)}
                    className="flex items-center gap-1.5 rounded-full border border-signal/30 bg-signal/5 px-3 py-1.5 text-xs text-signal hover:bg-signal/10"
                  >
                    <Sparkles size={11} />
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="border-t border-ink-700/20 p-4 dark:border-ink-700/40">
          <div className="mx-auto flex max-w-3xl items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a question about your documents..."
              rows={1}
              className="max-h-40 flex-1 resize-none rounded-xl border border-ink-700/20 bg-white/60 px-4 py-3 text-sm outline-none focus:border-signal dark:border-ink-700/40 dark:bg-ink-900/50 dark:text-paper-50"
            />
            {isStreaming ? (
              <button onClick={stop} className="flex h-11 w-11 items-center justify-center rounded-xl bg-red-500/90 text-white hover:opacity-90">
                <Square size={16} />
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="flex h-11 w-11 items-center justify-center rounded-xl bg-signal text-white hover:opacity-90 disabled:opacity-40"
              >
                <Send size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

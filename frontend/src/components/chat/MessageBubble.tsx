import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Check, Copy, FileText, RefreshCw, Sparkles, ThumbsDown, ThumbsUp } from "lucide-react";
import type { Citation } from "@/types";
import { feedbackApi } from "@/services/api";

export default function MessageBubble({
  messageId,
  role,
  content,
  citations,
  confidence,
  isStreaming,
  isLatestAssistant,
  onRegenerate,
}: {
  messageId?: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  confidence?: number | null;
  isStreaming?: boolean;
  isLatestAssistant?: boolean;
  onRegenerate?: () => void;
}) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleFeedback = async (rating: "up" | "down") => {
    if (!messageId) return;
    setFeedback(rating);
    try {
      await feedbackApi.submit({ message_id: messageId, rating });
    } catch {
      // Non-critical -- feedback failing silently is preferable to blocking the chat UI.
    }
  };

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {!isUser && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-signal/15 text-signal">
          <Sparkles size={14} />
        </div>
      )}
      <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser ? "bg-signal text-white" : "bg-white/70 text-ink-900 dark:bg-ink-800/80 dark:text-paper-100"
          }`}
        >
          {isStreaming ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || "");
                  return match ? (
                    <SyntaxHighlighter
                      style={oneDark as any}
                      language={match[1]}
                      PreTag="div"
                      customStyle={{ borderRadius: "0.5rem", fontSize: "0.8rem" }}
                    >
                      {String(children).replace(/\n$/, "")}
                    </SyntaxHighlighter>
                  ) : (
                    <code className="rounded bg-black/20 px-1 py-0.5 text-xs" {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {content}
            </ReactMarkdown>
          )}
          {isStreaming && <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse bg-current align-text-bottom" />}
        </div>

        {!!citations?.length && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {citations.map((c, i) => (
              <span
                key={i}
                title={c.chunk_text}
                className="flex items-center gap-1 rounded-full border border-ink-700/20 bg-white/50 px-2 py-1 text-[11px] text-ink-700/70 dark:border-ink-700/40 dark:bg-ink-900/50 dark:text-paper-200/60"
              >
                <FileText size={10} />
                {c.filename}
                {c.page_number ? ` · p.${c.page_number}` : ""}
              </span>
            ))}
            {confidence != null && (
              <span className="rounded-full bg-emerald-400/10 px-2 py-1 text-[11px] text-emerald-400">
                {Math.round(confidence * 100)}% confidence
              </span>
            )}
          </div>
        )}

        {!isUser && !isStreaming && content && (
          <div className="mt-1.5 flex items-center gap-1">
            <button
              onClick={handleCopy}
              title="Copy response"
              className="rounded p-1 text-ink-700/40 hover:bg-ink-700/5 hover:text-ink-900 dark:text-paper-200/40 dark:hover:bg-white/10 dark:hover:text-paper-50"
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
            </button>
            {isLatestAssistant && onRegenerate && (
              <button
                onClick={onRegenerate}
                title="Regenerate response"
                className="rounded p-1 text-ink-700/40 hover:bg-ink-700/5 hover:text-ink-900 dark:text-paper-200/40 dark:hover:bg-white/10 dark:hover:text-paper-50"
              >
                <RefreshCw size={13} />
              </button>
            )}
            <button
              onClick={() => handleFeedback("up")}
              title="Good response"
              className={`rounded p-1 hover:bg-ink-700/5 dark:hover:bg-white/10 ${
                feedback === "up" ? "text-emerald-400" : "text-ink-700/40 dark:text-paper-200/40"
              }`}
            >
              <ThumbsUp size={13} />
            </button>
            <button
              onClick={() => handleFeedback("down")}
              title="Bad response"
              className={`rounded p-1 hover:bg-ink-700/5 dark:hover:bg-white/10 ${
                feedback === "down" ? "text-red-400" : "text-ink-700/40 dark:text-paper-200/40"
              }`}
            >
              <ThumbsDown size={13} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

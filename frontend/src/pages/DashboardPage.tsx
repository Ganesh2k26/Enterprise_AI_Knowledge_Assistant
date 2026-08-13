import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { FileStack, MessagesSquare, CheckCircle2, Clock, ArrowUpRight, Star, HardDrive } from "lucide-react";
import { documentsApi, chatApi } from "@/services/api";
import { useAuth } from "@/hooks/useAuth";
import type { Document, ChatSession } from "@/types";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: documents, isLoading: docsLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: async () => (await documentsApi.list()).data as Document[],
  });
  const { data: sessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: async () => (await chatApi.listSessions()).data as ChatSession[],
  });

  const readyCount = documents?.filter((d) => d.status === "ready").length ?? 0;
  const processingCount = documents?.filter((d) => d.status === "processing" || d.status === "pending").length ?? 0;
  const totalStorage = documents?.reduce((sum, d) => sum + d.file_size_bytes, 0) ?? 0;
  const pinned = documents?.filter((d) => d.is_favorite) ?? [];

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="font-display text-3xl text-ink-900 dark:text-paper-50">
        Good to see you, {user?.full_name?.split(" ")[0]}
      </h1>
      <p className="mt-1 text-ink-700/70 dark:text-paper-200/60">Here's what's happening in your workspace.</p>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-4">
        <StatCard icon={FileStack} label="Documents ready" value={readyCount} accent="text-signal" />
        <StatCard icon={Clock} label="Processing" value={processingCount} accent="text-amber" />
        <StatCard icon={MessagesSquare} label="Chat sessions" value={sessions?.length ?? 0} accent="text-emerald-400" />
        <StatCard icon={HardDrive} label="Storage used" value={formatBytes(totalStorage)} accent="text-violet-400" />
      </div>

      {!!pinned.length && (
        <div className="mt-8">
          <h2 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-ink-900 dark:text-paper-50">
            <Star size={14} className="text-amber" fill="currentColor" /> Pinned documents
          </h2>
          <div className="flex flex-wrap gap-2">
            {pinned.map((d) => (
              <Link
                key={d.id}
                to="/documents"
                className="rounded-lg border border-ink-700/20 bg-white/60 px-3 py-2 text-sm text-ink-900 hover:border-signal/40 dark:border-ink-700/40 dark:bg-ink-900/50 dark:text-paper-100"
              >
                {d.filename}
              </Link>
            ))}
          </div>
        </div>
      )}

      <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-2">
        <Panel title="Recent documents" viewAllHref="/documents">
          {docsLoading && <EmptyRow text="Loading documents..." />}
          {documents?.slice(0, 5).map((d) => (
            <div key={d.id} className="flex items-center justify-between py-2.5 text-sm">
              <span className="truncate text-ink-900 dark:text-paper-100">{d.filename}</span>
              <StatusPill status={d.status} />
            </div>
          ))}
          {!docsLoading && !documents?.length && <EmptyRow text="No documents yet. Upload your first file to get started." />}
        </Panel>

        <Panel title="Recent chats" viewAllHref="/chat">
          {sessions?.slice(0, 5).map((s) => (
            <Link
              key={s.id}
              to={`/chat/${s.id}`}
              className="flex items-center justify-between py-2.5 text-sm text-ink-900 hover:text-signal dark:text-paper-100"
            >
              <span className="truncate">{s.title}</span>
              <ArrowUpRight size={14} className="opacity-40" />
            </Link>
          ))}
          {!sessions?.length && <EmptyRow text="No conversations yet. Start one from the Chat tab." />}
        </Panel>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, accent }: { icon: any; label: string; value: number | string; accent: string }) {
  return (
    <div className="rounded-xl2 border border-ink-700/20 bg-white/60 p-5 shadow-panel dark:border-ink-700/40 dark:bg-ink-900/50">
      <Icon className={accent} size={20} />
      <p className="mt-3 font-display text-2xl text-ink-900 dark:text-paper-50">{value}</p>
      <p className="text-sm text-ink-700/60 dark:text-paper-200/50">{label}</p>
    </div>
  );
}

function Panel({ title, viewAllHref, children }: { title: string; viewAllHref: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl2 border border-ink-700/20 bg-white/60 p-5 dark:border-ink-700/40 dark:bg-ink-900/50">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-ink-900 dark:text-paper-50">{title}</h2>
        <Link to={viewAllHref} className="text-xs text-signal hover:underline">
          View all
        </Link>
      </div>
      <div className="divide-y divide-ink-700/10 dark:divide-ink-700/30">{children}</div>
    </div>
  );
}

function EmptyRow({ text }: { text: string }) {
  return <p className="py-4 text-sm text-ink-700/50 dark:text-paper-200/40">{text}</p>;
}

function StatusPill({ status }: { status: Document["status"] }) {
  const map: Record<Document["status"], { label: string; cls: string; icon: any }> = {
    ready: { label: "Ready", cls: "text-emerald-400 bg-emerald-400/10", icon: CheckCircle2 },
    processing: { label: "Processing", cls: "text-amber bg-amber/10", icon: Clock },
    pending: { label: "Pending", cls: "text-amber bg-amber/10", icon: Clock },
    failed: { label: "Failed", cls: "text-red-400 bg-red-400/10", icon: Clock },
  };
  const { label, cls, icon: Icon } = map[status];
  return (
    <span className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${cls}`}>
      <Icon size={11} />
      {label}
    </span>
  );
}

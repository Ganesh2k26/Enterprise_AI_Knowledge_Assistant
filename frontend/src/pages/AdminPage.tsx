import { useQuery } from "@tanstack/react-query";
import { ShieldCheck, Users, FileStack, Activity, Database, AlertTriangle } from "lucide-react";
import { adminApi } from "@/services/api";
import type { AdminOverview } from "@/types";

function formatBytes(bytes: number): string {
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

export default function AdminPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-overview"],
    queryFn: async () => (await adminApi.overview()).data as AdminOverview,
  });

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex items-center gap-2">
        <ShieldCheck className="text-amber" size={22} />
        <h1 className="font-display text-3xl text-ink-900 dark:text-paper-50">Admin overview</h1>
      </div>
      <p className="mt-1 text-ink-700/70 dark:text-paper-200/60">Organization-wide usage, last 30 days.</p>

      {isLoading && <p className="mt-8 text-sm text-ink-700/50 dark:text-paper-200/40">Loading...</p>}

      {data && (
        <>
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            <Card icon={Users} label="Registered users" value={data.registered_users} />
            <Card icon={FileStack} label="Uploaded documents" value={data.uploaded_documents} />
            <Card icon={AlertTriangle} label="Failed uploads" value={data.failed_documents} />
            <Card icon={Database} label="Embeddings stored" value={data.embedding_count} />
            <Card icon={Activity} label="Storage used" value={formatBytes(data.storage_used_bytes)} />
          </div>

          <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="rounded-xl2 border border-ink-700/20 bg-white/60 p-5 dark:border-ink-700/40 dark:bg-ink-900/50">
              <h2 className="mb-3 text-sm font-semibold text-ink-900 dark:text-paper-50">API usage by action</h2>
              {data.usage_last_30_days.length ? (
                <div className="space-y-2">
                  {data.usage_last_30_days.map((u) => (
                    <div key={u.action} className="flex items-center justify-between text-sm">
                      <span className="capitalize text-ink-700/70 dark:text-paper-200/60">{u.action}</span>
                      <span className="text-ink-900 dark:text-paper-100">
                        {u.count} calls &middot; {u.avg_latency_ms}ms avg
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-ink-700/40 dark:text-paper-200/30">No API activity in the last 30 days.</p>
              )}
            </div>

            <div className="rounded-xl2 border border-ink-700/20 bg-white/60 p-5 dark:border-ink-700/40 dark:bg-ink-900/50">
              <h2 className="mb-3 text-sm font-semibold text-ink-900 dark:text-paper-50">Recent uploads</h2>
              {data.recent_documents.length ? (
                <div className="divide-y divide-ink-700/10 dark:divide-ink-700/30">
                  {data.recent_documents.map((d) => (
                    <div key={d.id} className="flex items-center justify-between py-2 text-sm">
                      <span className="truncate text-ink-900 dark:text-paper-100">{d.filename}</span>
                      <span
                        className={
                          d.status === "ready" ? "text-emerald-400" : d.status === "failed" ? "text-red-400" : "text-amber"
                        }
                      >
                        {d.status}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-ink-700/40 dark:text-paper-200/30">No uploads yet.</p>
              )}
            </div>
          </div>
        </>
      )}

      <div className="mt-8 rounded-xl2 border border-amber/20 bg-amber/5 p-5 text-sm text-ink-700/80 dark:text-paper-200/70">
        This admin view is scoped to your organization. A production build could extend it with
        per-user drill-down and cross-org superuser views on top of the same <code>usage_logs</code> table.
      </div>
    </div>
  );
}

function Card({ icon: Icon, label, value }: { icon: any; label: string; value: number | string }) {
  return (
    <div className="rounded-xl2 border border-ink-700/20 bg-white/60 p-5 dark:border-ink-700/40 dark:bg-ink-900/50">
      <Icon className="text-amber" size={20} />
      <p className="mt-3 font-display text-2xl text-ink-900 dark:text-paper-50">{value}</p>
      <p className="text-sm text-ink-700/60 dark:text-paper-200/50">{label}</p>
    </div>
  );
}

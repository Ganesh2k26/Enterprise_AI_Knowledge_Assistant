import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDispatch, useSelector } from "react-redux";
import { Copy, Key, Moon, Plus, Sun, Trash2 } from "lucide-react";
import type { RootState } from "@/store";
import { toggleTheme } from "@/store/slices/uiSlice";
import { useAuth } from "@/hooks/useAuth";
import { apiKeysApi } from "@/services/api";
import type { APIKey } from "@/types";

export default function SettingsPage() {
  const { user } = useAuth();
  const dispatch = useDispatch();
  const theme = useSelector((state: RootState) => state.ui.theme);
  const queryClient = useQueryClient();
  const [newKeyPlaintext, setNewKeyPlaintext] = useState<string | null>(null);

  const { data: apiKeys } = useQuery({
    queryKey: ["api-keys"],
    queryFn: async () => (await apiKeysApi.list()).data as APIKey[],
  });

  const createKeyMutation = useMutation({
    mutationFn: (name: string) => apiKeysApi.create(name),
    onSuccess: ({ data }) => {
      setNewKeyPlaintext(data.plaintext_key);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  const revokeKeyMutation = useMutation({
    mutationFn: (id: string) => apiKeysApi.revoke(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
  });

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="font-display text-3xl text-ink-900 dark:text-paper-50">Settings</h1>
      <p className="mt-1 text-ink-700/70 dark:text-paper-200/60">Manage your profile, preferences, and API access.</p>

      <section className="mt-8 rounded-xl2 border border-ink-700/20 bg-white/60 p-6 dark:border-ink-700/40 dark:bg-ink-900/50">
        <h2 className="text-sm font-semibold text-ink-900 dark:text-paper-50">Profile</h2>
        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-ink-700/50 dark:text-paper-200/40">Full name</p>
            <p className="mt-0.5 text-ink-900 dark:text-paper-100">{user?.full_name}</p>
          </div>
          <div>
            <p className="text-ink-700/50 dark:text-paper-200/40">Email</p>
            <p className="mt-0.5 text-ink-900 dark:text-paper-100">{user?.email}</p>
          </div>
          <div>
            <p className="text-ink-700/50 dark:text-paper-200/40">Role</p>
            <p className="mt-0.5 capitalize text-ink-900 dark:text-paper-100">{user?.role}</p>
          </div>
        </div>
      </section>

      <section className="mt-6 rounded-xl2 border border-ink-700/20 bg-white/60 p-6 dark:border-ink-700/40 dark:bg-ink-900/50">
        <h2 className="text-sm font-semibold text-ink-900 dark:text-paper-50">Appearance</h2>
        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-ink-700/70 dark:text-paper-200/60">
            {theme === "dark" ? <Moon size={16} /> : <Sun size={16} />}
            {theme === "dark" ? "Dark mode" : "Light mode"}
          </div>
          <button
            onClick={() => dispatch(toggleTheme())}
            className="rounded-lg border border-ink-700/20 px-3 py-1.5 text-sm text-ink-900 hover:bg-ink-700/5 dark:border-ink-700/40 dark:text-paper-100 dark:hover:bg-white/5"
          >
            Switch to {theme === "dark" ? "light" : "dark"}
          </button>
        </div>
      </section>

      <section className="mt-6 rounded-xl2 border border-ink-700/20 bg-white/60 p-6 dark:border-ink-700/40 dark:bg-ink-900/50">
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-1.5 text-sm font-semibold text-ink-900 dark:text-paper-50">
            <Key size={15} /> API keys
          </h2>
          <button
            onClick={() => {
              const name = prompt("Name this key (e.g. 'CI pipeline')");
              if (name) createKeyMutation.mutate(name);
            }}
            className="flex items-center gap-1 rounded-lg border border-signal/30 bg-signal/10 px-2.5 py-1.5 text-xs font-medium text-signal hover:bg-signal/15"
          >
            <Plus size={13} /> New key
          </button>
        </div>

        {newKeyPlaintext && (
          <div className="mt-4 rounded-lg border border-amber/30 bg-amber/5 p-3 text-xs text-ink-900 dark:text-paper-100">
            <p className="mb-1 font-medium text-amber">Copy this key now -- it won't be shown again.</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 truncate rounded bg-black/10 px-2 py-1 dark:bg-black/30">{newKeyPlaintext}</code>
              <button onClick={() => navigator.clipboard.writeText(newKeyPlaintext)} className="text-ink-700/60 hover:text-ink-900 dark:text-paper-200/50 dark:hover:text-paper-50">
                <Copy size={14} />
              </button>
            </div>
          </div>
        )}

        <div className="mt-4 divide-y divide-ink-700/10 dark:divide-ink-700/30">
          {apiKeys?.map((k) => (
            <div key={k.id} className="flex items-center justify-between py-2.5 text-sm">
              <div>
                <p className="text-ink-900 dark:text-paper-100">{k.name}</p>
                <p className="text-xs text-ink-700/50 dark:text-paper-200/40">{k.key_prefix}...</p>
              </div>
              <button onClick={() => revokeKeyMutation.mutate(k.id)} className="text-ink-700/30 hover:text-red-400 dark:text-paper-200/30">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {!apiKeys?.length && <p className="py-3 text-sm text-ink-700/40 dark:text-paper-200/30">No API keys yet.</p>}
        </div>
      </section>
    </div>
  );
}

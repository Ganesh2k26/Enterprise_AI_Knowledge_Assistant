import { NavLink } from "react-router-dom";
import { LayoutGrid, FileStack, MessagesSquare, Settings, ShieldCheck, Sparkles } from "lucide-react";
import clsx from "clsx";
import { useAuth } from "@/hooks/useAuth";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutGrid, end: true },
  { to: "/documents", label: "Documents", icon: FileStack },
  { to: "/chat", label: "Chat", icon: MessagesSquare },
  { to: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const { user } = useAuth();
  const isAdmin = user?.role === "owner" || user?.role === "admin";

  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-ink-700/30 bg-ink-900/40 dark:bg-ink-900/70 md:flex">
      <div className="flex items-center gap-2 px-6 py-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-signal/15 text-signal">
          <Sparkles size={18} />
        </div>
        <div>
          <p className="font-display text-lg leading-none text-paper-50">Atlas</p>
          <p className="text-[11px] uppercase tracking-wider text-paper-200/50">Knowledge Assistant</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                isActive
                  ? "bg-signal/15 text-signal font-medium"
                  : "text-paper-200/70 hover:bg-white/5 hover:text-paper-50"
              )
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}

        {isAdmin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors",
                isActive ? "bg-amber/15 text-amber font-medium" : "text-paper-200/70 hover:bg-white/5 hover:text-paper-50"
              )
            }
          >
            <ShieldCheck size={17} />
            Admin
          </NavLink>
        )}
      </nav>

      <div className="mx-3 mb-4 rounded-xl border border-ink-700/40 bg-ink-800/50 p-3 text-xs text-paper-200/60">
        Signed in as
        <p className="mt-0.5 truncate text-sm font-medium text-paper-50">{user?.full_name}</p>
      </div>
    </aside>
  );
}

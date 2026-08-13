import { useDispatch, useSelector } from "react-redux";
import { Moon, Sun, LogOut } from "lucide-react";
import type { RootState } from "@/store";
import { toggleTheme } from "@/store/slices/uiSlice";
import { useAuth } from "@/hooks/useAuth";

export default function Topbar() {
  const dispatch = useDispatch();
  const theme = useSelector((state: RootState) => state.ui.theme);
  const { logout } = useAuth();

  return (
    <header className="flex h-14 items-center justify-between border-b border-ink-700/30 px-6">
      <div />
      <div className="flex items-center gap-2">
        <button
          onClick={() => dispatch(toggleTheme())}
          className="rounded-lg p-2 text-paper-200/70 hover:bg-white/5 hover:text-paper-50"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
        </button>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm text-paper-200/70 hover:bg-white/5 hover:text-paper-50"
        >
          <LogOut size={15} />
          Sign out
        </button>
      </div>
    </header>
  );
}

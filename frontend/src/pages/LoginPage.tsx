import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { Sparkles, ArrowRight } from "lucide-react";
import { authApi } from "@/services/api";
import { setCredentials } from "@/store/slices/authSlice";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data: tokens } = await authApi.login({ email, password });
      // Pass token explicitly — interceptor only sees Redux after setCredentials.
      const { data: user } = await authApi.me(tokens.access_token);
      dispatch(setCredentials({ user, accessToken: tokens.access_token, refreshToken: tokens.refresh_token }));
      navigate("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Unable to sign in. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell>
      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <h1 className="font-display text-2xl text-paper-50">Welcome back</h1>
          <p className="mt-1 text-sm text-paper-200/60">Sign in to keep talking to your documents.</p>
        </div>

        {error && <p className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</p>}

        <Field label="Email">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="auth-input"
            placeholder="you@company.com"
          />
        </Field>
        <Field label="Password">
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="auth-input"
            placeholder="••••••••"
          />
        </Field>

        <button type="submit" disabled={loading} className="auth-submit">
          {loading ? "Signing in..." : "Sign in"}
          <ArrowRight size={16} />
        </button>

        <p className="text-center text-sm text-paper-200/60">
          Don&apos;t have an account?{" "}
          <Link to="/signup" className="text-signal hover:underline">
            Create one
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-ink-950 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-signal/15 text-signal">
            <Sparkles size={20} />
          </div>
          <span className="font-display text-xl text-paper-50">Atlas</span>
        </div>
        <div className="rounded-xl2 border border-ink-700/40 bg-ink-900/60 p-8 shadow-panel">{children}</div>
      </div>
      <style>{`
        .auth-input { width: 100%; border-radius: 0.6rem; border: 1px solid rgba(255,255,255,0.08);
          background: rgba(255,255,255,0.03); padding: 0.6rem 0.85rem; font-size: 0.9rem; color: #F7F8FA; }
        .auth-input:focus { outline: 2px solid #3E8FF2; outline-offset: 1px; }
        .auth-submit { width: 100%; display:flex; align-items:center; justify-content:center; gap: 0.4rem;
          border-radius: 0.6rem; background: #3E8FF2; padding: 0.65rem; font-size: 0.9rem; font-weight: 500;
          color: white; transition: opacity 0.15s; }
        .auth-submit:hover { opacity: 0.9; }
        .auth-submit:disabled { opacity: 0.6; }
      `}</style>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-paper-200/50">{label}</span>
      {children}
    </label>
  );
}

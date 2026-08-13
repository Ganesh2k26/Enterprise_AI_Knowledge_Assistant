import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { ArrowRight, Check, X } from "lucide-react";
import { authApi } from "@/services/api";
import { setCredentials } from "@/store/slices/authSlice";
import { AuthShell } from "./LoginPage";

const PASSWORD_RULES: { label: string; test: (pw: string) => boolean }[] = [
  { label: "At least 8 characters", test: (pw) => pw.length >= 8 },
  { label: "An uppercase letter", test: (pw) => /[A-Z]/.test(pw) },
  { label: "A lowercase letter", test: (pw) => /[a-z]/.test(pw) },
  { label: "A digit", test: (pw) => /\d/.test(pw) },
  { label: "A special character", test: (pw) => /[^A-Za-z0-9]/.test(pw) },
];

export default function SignupPage() {
  const [form, setForm] = useState({ full_name: "", email: "", password: "", organization_name: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const passwordChecks = useMemo(() => PASSWORD_RULES.map((r) => ({ ...r, met: r.test(form.password) })), [form.password]);
  const passwordValid = passwordChecks.every((c) => c.met);

  const update = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!passwordValid) {
      setError("Please meet all password requirements.");
      return;
    }
    setLoading(true);
    try {
      await authApi.register(form);
      const { data: tokens } = await authApi.login({ email: form.email, password: form.password });
      const { data: user } = await authApi.me(tokens.access_token);
      dispatch(setCredentials({ user, accessToken: tokens.access_token, refreshToken: tokens.refresh_token }));
      navigate("/");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Unable to create your account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <h1 className="font-display text-2xl text-paper-50">Create your workspace</h1>
          <p className="mt-1 text-sm text-paper-200/60">Start chatting with your documents in minutes.</p>
        </div>

        {error && <p className="rounded-lg bg-red-500/10 px-3 py-2 text-sm text-red-400">{error}</p>}

        <label className="block">
          <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-paper-200/50">Full name</span>
          <input required value={form.full_name} onChange={update("full_name")} className="auth-input" placeholder="Jane Doe" />
        </label>
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-paper-200/50">Organization</span>
          <input required value={form.organization_name} onChange={update("organization_name")} className="auth-input" placeholder="Acme Inc" />
        </label>
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-paper-200/50">Email</span>
          <input type="email" required value={form.email} onChange={update("email")} className="auth-input" placeholder="you@company.com" />
        </label>
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium uppercase tracking-wide text-paper-200/50">Password</span>
          <input type="password" required value={form.password} onChange={update("password")} className="auth-input" placeholder="Create a strong password" />
        </label>

        {form.password && (
          <div className="grid grid-cols-1 gap-1 rounded-lg border border-white/5 bg-white/5 p-2.5 sm:grid-cols-2">
            {passwordChecks.map((c) => (
              <div key={c.label} className={`flex items-center gap-1.5 text-xs ${c.met ? "text-emerald-400" : "text-paper-200/40"}`}>
                {c.met ? <Check size={12} /> : <X size={12} />}
                {c.label}
              </div>
            ))}
          </div>
        )}

        <button type="submit" disabled={loading} className="auth-submit">
          {loading ? "Creating account..." : "Create account"}
          <ArrowRight size={16} />
        </button>

        <p className="text-center text-sm text-paper-200/60">
          Already have an account?{" "}
          <Link to="/login" className="text-signal hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </AuthShell>
  );
}

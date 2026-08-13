import { lazy, Suspense, useEffect } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useSelector } from "react-redux";
import type { RootState } from "@/store";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import AppLayout from "@/layouts/AppLayout";

const LoginPage = lazy(() => import("@/pages/LoginPage"));
const SignupPage = lazy(() => import("@/pages/SignupPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const DocumentsPage = lazy(() => import("@/pages/DocumentsPage"));
const ChatPage = lazy(() => import("@/pages/ChatPage"));
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));
const AdminPage = lazy(() => import("@/pages/AdminPage"));

function PageLoader() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center text-sm text-ink-700/50 dark:text-paper-200/40">
      Loading...
    </div>
  );
}

export default function App() {
  const theme = useSelector((state: RootState) => state.ui.theme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/chat/:sessionId" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

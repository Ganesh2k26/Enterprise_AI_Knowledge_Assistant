import axios from "axios";
import { store } from "@/store";
import { logout, setCredentials } from "@/store/slices/authSlice";

export const api = axios.create({ baseURL: "/api/v1" });

api.interceptors.request.use((config) => {
  const token = store.getState().auth.accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRefreshing = false;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry && !isRefreshing) {
      original._retry = true;
      isRefreshing = true;
      try {
        const refreshToken = store.getState().auth.refreshToken;
        const user = store.getState().auth.user;
        if (!refreshToken || !user) throw new Error("No refresh token");
        const { data } = await axios.post("/api/v1/auth/refresh", { refresh_token: refreshToken });
        store.dispatch(setCredentials({ user, accessToken: data.access_token, refreshToken: data.refresh_token }));
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return api(original);
      } catch {
        store.dispatch(logout());
        window.location.href = "/login";
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

// --- Auth ---
export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    organization_id: string;
  };
}

export const authApi = {
  register: (payload: { email: string; password: string; full_name: string; organization_name: string }) =>
    api.post<AuthResponse>("/auth/register", payload),
  login: (payload: { email: string; password: string }) => api.post<AuthResponse>("/auth/login", payload),
  me: (accessToken?: string) =>
    api.get("/users/me", accessToken ? { headers: { Authorization: `Bearer ${accessToken}` } } : undefined),
};

// --- Documents ---
export const documentsApi = {
  list: (params?: { folder_id?: string; search?: string }) => api.get("/documents", { params }),
  upload: (file: File, folderId?: string, onProgress?: (pct: number) => void) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/documents/upload", form, {
      params: folderId ? { folder_id: folderId } : undefined,
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (evt) => {
        if (onProgress && evt.total) onProgress(Math.round((evt.loaded / evt.total) * 100));
      },
    });
  },
  get: (id: string) => api.get(`/documents/${id}`),
  update: (id: string, payload: { is_favorite?: boolean; folder_id?: string | null }) =>
    api.patch(`/documents/${id}`, payload),
  remove: (id: string) => api.delete(`/documents/${id}`),
};

// --- Folders ---
export const foldersApi = {
  list: () => api.get("/folders"),
  create: (name: string, parentFolderId?: string) =>
    api.post("/folders", { name, parent_folder_id: parentFolderId }),
  remove: (id: string) => api.delete(`/folders/${id}`),
};

// --- Chat ---
export const chatApi = {
  listSessions: () => api.get("/chat/sessions"),
  createSession: (title: string, documentIds: string[]) =>
    api.post("/chat/sessions", { title, document_ids: documentIds }),
  getSession: (id: string) => api.get(`/chat/sessions/${id}`),
  rename: (id: string, title: string) => api.patch(`/chat/sessions/${id}/rename`, null, { params: { title } }),
  remove: (id: string) => api.delete(`/chat/sessions/${id}`),
  export: (id: string) => api.get(`/chat/sessions/${id}/export`),
};

// --- Feedback ---
export const feedbackApi = {
  submit: (payload: { message_id: string; document_id?: string; rating: "up" | "down"; comment?: string }) =>
    api.post("/feedback", payload),
};

// --- Org settings ---
export const settingsApi = {
  list: () => api.get("/settings"),
  upsert: (key: string, value: string) => api.put("/settings", { key, value }),
};

// --- API keys ---
export const apiKeysApi = {
  list: () => api.get("/api-keys"),
  create: (name: string) => api.post("/api-keys", { name }),
  revoke: (id: string) => api.delete(`/api-keys/${id}`),
};

// --- Admin ---
export const adminApi = {
  overview: () => api.get("/admin/overview"),
};

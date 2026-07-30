import { create } from "zustand";
import { persist } from "zustand/middleware";
import { api, type AuthResult } from "@/lib/api";

export type User = {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role?: string;
};

type AuthState = {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (name: string, email: string, password: string) => Promise<void>;
  googleSignIn: (credential: string) => Promise<void>;
  signOut: () => void;
  updateProfile: (patch: Partial<User>) => void;
  hydrate: () => Promise<void>;
};

function toUser(r: AuthResult): User {
  return {
    id: r.user_id,
    name: r.name,
    email: r.email,
    avatar: r.avatar_url ?? undefined,
    role: r.role ?? undefined,
  };
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      loading: false,

      signIn: async (email, password) => {
        set({ loading: true });
        try {
          const res = await api.auth.login(email, password);
          set({
            user: toUser(res),
            token: res.access_token,
            refreshToken: res.refresh_token ?? null,
            loading: false,
          });
        } catch (e) {
          set({ loading: false });
          throw e;
        }
      },

      signUp: async (_name, email, password) => {
        set({ loading: true });
        try {
          const res = await api.auth.register(email, password);
          set({
            user: toUser(res),
            token: res.access_token,
            refreshToken: res.refresh_token ?? null,
            loading: false,
          });
        } catch (e) {
          set({ loading: false });
          throw e;
        }
      },

      googleSignIn: async (credential) => {
        set({ loading: true });
        try {
          const res = await api.auth.googleLogin(credential);
          set({
            user: toUser(res),
            token: res.access_token,
            refreshToken: res.refresh_token ?? null,
            loading: false,
          });
        } catch (e) {
          set({ loading: false });
          throw e;
        }
      },

      signOut: () => set({ user: null, token: null, refreshToken: null }),

      updateProfile: (patch) =>
        set((s) => ({ user: s.user ? { ...s.user, ...patch } : s.user })),

      hydrate: async () => {
        const token = get().token;
        if (!token) return;
        try {
          const res = await api.auth.getMe();
          set({ user: toUser(res) });
        } catch {
          // Token expired — try refresh
          const rt = get().refreshToken;
          if (rt) {
            try {
              const res = await api.auth.refreshToken(rt);
              set({
                user: toUser(res),
                token: res.access_token,
                refreshToken: res.refresh_token ?? rt,
              });
            } catch {
              set({ user: null, token: null, refreshToken: null });
            }
          } else {
            set({ user: null, token: null, refreshToken: null });
          }
        }
      },
    }),
    { name: "infichat-auth" },
  ),
);

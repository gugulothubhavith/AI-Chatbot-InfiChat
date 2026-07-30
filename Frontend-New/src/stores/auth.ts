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
      loading: false,

      signIn: async (email, password) => {
        set({ loading: true });
        try {
          const res = await api.auth.login(email, password);
          set({
            user: toUser(res),
            token: res.access_token,
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
            loading: false,
          });
        } catch (e) {
          set({ loading: false });
          throw e;
        }
      },

      signOut: () => {
        // Fire-and-forget: clear the httpOnly refresh cookie server-side.
        void api.auth.logout().catch(() => {});
        set({ user: null, token: null });
      },

      updateProfile: (patch) =>
        set((s) => ({ user: s.user ? { ...s.user, ...patch } : s.user })),

      hydrate: async () => {
        const token = get().token;
        // Even without an access token in memory we may still hold a valid
        // refresh cookie (e.g. after a page reload), so always try to refresh.
        if (!token) {
          try {
            const res = await api.auth.refreshToken();
            set({ user: toUser(res), token: res.access_token });
          } catch {
            set({ user: null, token: null });
          }
          return;
        }
        try {
          const res = await api.auth.getMe();
          set({ user: toUser(res) });
        } catch {
          // Access token expired — try the refresh cookie.
          try {
            const res = await api.auth.refreshToken();
            set({ user: toUser(res), token: res.access_token });
          } catch {
            set({ user: null, token: null });
          }
        }
      },
    }),
    {
      name: "infichat-auth",
      // Persist ONLY the short-lived access token and user profile. The refresh
      // token is an httpOnly cookie and must never be written to localStorage.
      partialize: (s) => ({ user: s.user, token: s.token }),
    },
  ),
);

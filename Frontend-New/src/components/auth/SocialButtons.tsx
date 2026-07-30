import { motion } from "framer-motion";
import { tapProps } from "@/lib/motion";
import { useGoogleLogin } from "@react-oauth/google";
import { useAuthStore } from "@/stores/auth";
import { toast } from "sonner";
import { useRouter } from "@tanstack/react-router";

const providers = [
  { id: "google", label: "Google", icon: <GoogleIcon /> },
  { id: "github", label: "GitHub", icon: <GitHubIcon /> },
  { id: "apple", label: "Apple", icon: <AppleIcon /> },
] as const;

export function SocialButtons() {
  const googleSignIn = useAuthStore((s) => s.googleSignIn);
  const router = useRouter();

  const handleGoogleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        await googleSignIn(tokenResponse.access_token);
        toast.success("Successfully logged in with Google!");
        router.navigate({ to: "/chat" });
      } catch (e: any) {
        toast.error(e.message || "Google login failed");
      }
    },
    onError: () => toast.error("Google login failed or was cancelled"),
  });

  return (
    <div className="grid grid-cols-3 gap-2">
      {providers.map((p) => (
        <motion.button
          key={p.id}
          {...tapProps}
          type="button"
          onClick={() => {
            if (p.id === "google") handleGoogleLogin();
            else toast.info(`${p.label} login is not implemented yet.`);
          }}
          className="flex h-11 items-center justify-center gap-2 rounded-full border border-border bg-surface text-sm text-foreground/90 elevated hover:bg-surface-2"
        >
          {p.icon}
          <span>{p.label}</span>
        </motion.button>
      ))}
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09Z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.25 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23Z"/>
      <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 0 1 0-4.2V7.07H2.18a11 11 0 0 0 0 9.87l3.66-2.83Z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.83C6.71 7.3 9.14 5.38 12 5.38Z"/>
    </svg>
  );
}
function GitHubIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 .5C5.65.5.5 5.65.5 12a11.5 11.5 0 0 0 7.86 10.92c.57.11.78-.25.78-.55v-1.93c-3.2.7-3.87-1.54-3.87-1.54-.52-1.32-1.28-1.68-1.28-1.68-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.35.96.11-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.68 0-1.26.45-2.29 1.19-3.09-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.18 1.18a11.06 11.06 0 0 1 5.79 0c2.21-1.49 3.18-1.18 3.18-1.18.63 1.58.23 2.75.11 3.04.74.8 1.19 1.83 1.19 3.09 0 4.41-2.7 5.38-5.27 5.67.41.36.78 1.06.78 2.14v3.17c0 .3.21.67.79.55A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z"/>
    </svg>
  );
}
function AppleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M16.37 12.68c-.03-2.9 2.37-4.29 2.48-4.36-1.35-1.98-3.46-2.25-4.21-2.28-1.79-.18-3.5 1.05-4.4 1.05-.93 0-2.33-1.03-3.83-1-1.97.03-3.79 1.14-4.8 2.9-2.05 3.55-.52 8.8 1.48 11.68.98 1.4 2.14 2.98 3.66 2.92 1.48-.06 2.03-.95 3.81-.95s2.28.95 3.83.92c1.58-.03 2.58-1.43 3.55-2.84 1.12-1.62 1.58-3.2 1.6-3.28-.04-.02-3.07-1.18-3.1-4.68ZM13.77 3.9c.82-1 1.37-2.38 1.22-3.75-1.18.05-2.6.78-3.44 1.77-.76.88-1.42 2.28-1.24 3.63 1.32.1 2.65-.66 3.46-1.65Z"/>
    </svg>
  );
}

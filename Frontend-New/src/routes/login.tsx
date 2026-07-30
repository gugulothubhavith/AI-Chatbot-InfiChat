import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { AuthShell } from "@/components/auth/AuthShell";
import { AuthForm } from "@/components/auth/AuthForm";
import { useAuthStore } from "@/stores/auth";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Sign in — InfiChat" },
      { name: "description", content: "Sign in to your InfiChat workspace." },
      { property: "og:title", content: "Sign in — InfiChat" },
      { property: "og:description", content: "Sign in to your InfiChat workspace." },
    ],
  }),
  component: LoginPage,
});


function LoginPage() {
  const nav = useNavigate();
  const signIn = useAuthStore((s) => s.signIn);
  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to pick up where your team left off."
      footer={
        <>
          Don't have an account?{" "}
          <Link to="/register" className="text-foreground font-medium hover:underline">
            Create one
          </Link>
        </>
      }
    >
      <AuthForm
        mode="login"
        onSubmit={async ({ email, password }) => {
          await signIn(email, password);
          nav({ to: "/chat" });
        }}
      />
    </AuthShell>
  );
}

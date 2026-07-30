import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { AuthShell } from "@/components/auth/AuthShell";
import { AuthForm } from "@/components/auth/AuthForm";
import { useAuthStore } from "@/stores/auth";

export const Route = createFileRoute("/register")({
  head: () => ({
    meta: [
      { title: "Create account — InfiChat" },
      { name: "description", content: "Create your InfiChat workspace — chat, code, research, and images for your team." },
      { property: "og:title", content: "Create account — InfiChat" },
      { property: "og:description", content: "Create your InfiChat workspace — chat, code, research, and images for your team." },
    ],
  }),
  component: RegisterPage,
});

function RegisterPage() {
  const nav = useNavigate();
  const signUp = useAuthStore((s) => s.signUp);
  return (
    <AuthShell
      title="Create your account"
      subtitle="Start free. Bring your team when you're ready."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="text-foreground font-medium hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <AuthForm
        mode="register"
        onSubmit={async ({ name, email, password }) => {
          await signUp(name ?? "", email, password);
          nav({ to: "/chat" });
        }}
      />
    </AuthShell>
  );
}

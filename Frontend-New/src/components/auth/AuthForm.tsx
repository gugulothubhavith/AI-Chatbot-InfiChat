import { motion } from "framer-motion";
import { useId, useState, type FormEvent } from "react";
import { Eye, EyeOff, Loader2, ArrowRight, AlertCircle } from "lucide-react";
import { tapProps } from "@/lib/motion";
import { SocialButtons } from "./SocialButtons";
import { cn } from "@/lib/utils";

export function AuthForm({
  mode,
  onSubmit,
}: {
  mode: "login" | "register";
  onSubmit: (data: { name?: string; email: string; password: string }) => Promise<void>;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", password: "" });

  async function handle(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await onSubmit(form);
    } catch (err) {
      // Surface the failure instead of leaving the button spinning silently.
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <SocialButtons />

      <div className="flex items-center gap-3">
        <div className="bg-border h-px flex-1" />
        <span className="text-muted-foreground text-[11.5px] tracking-wide uppercase">
          or with email
        </span>
        <div className="bg-border h-px flex-1" />
      </div>

      <form onSubmit={handle} className="space-y-3.5" noValidate>
        {mode === "register" && (
          <Field
            label="Full name"
            value={form.name}
            onChange={(v) => setForm((f) => ({ ...f, name: v }))}
            type="text"
            placeholder="Ada Lovelace"
            autoComplete="name"
            required
          />
        )}

        <Field
          label="Work email"
          value={form.email}
          onChange={(v) => setForm((f) => ({ ...f, email: v }))}
          type="email"
          placeholder="you@company.com"
          autoComplete="email"
          required
        />

        <Field
          label="Password"
          value={form.password}
          onChange={(v) => setForm((f) => ({ ...f, password: v }))}
          type={showPassword ? "text" : "password"}
          placeholder={mode === "register" ? "At least 8 characters" : "••••••••••"}
          autoComplete={mode === "register" ? "new-password" : "current-password"}
          required
          hint={
            mode === "login" ? (
              <a
                href="#"
                className="text-muted-foreground hover:text-foreground text-[12px] transition-colors"
              >
                Forgot password?
              </a>
            ) : undefined
          }
          adornment={
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="text-muted-foreground hover:text-foreground focus-visible:ring-brand/50 rounded-md p-1 transition-colors outline-none focus-visible:ring-2"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          }
        />

        {error && (
          <motion.div
            role="alert"
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-destructive flex items-start gap-2 text-[12.5px] leading-snug"
          >
            <AlertCircle className="mt-px h-3.5 w-3.5 shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}

        <motion.button
          {...tapProps}
          disabled={loading}
          type="submit"
          className="bg-primary text-primary-foreground elevated group mt-1 flex h-11 w-full items-center justify-center gap-2 rounded-xl text-[14px] font-medium transition-opacity disabled:opacity-65"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              {mode === "login" ? "Sign in" : "Create account"}
              <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
            </>
          )}
        </motion.button>
      </form>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type,
  placeholder,
  required,
  autoComplete,
  hint,
  adornment,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type: string;
  placeholder?: string;
  required?: boolean;
  autoComplete?: string;
  hint?: React.ReactNode;
  adornment?: React.ReactNode;
}) {
  const id = useId();

  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between">
        <label htmlFor={id} className="text-foreground/80 text-[12.5px] font-medium">
          {label}
        </label>
        {hint}
      </div>
      <div className="relative">
        <input
          id={id}
          className={cn(
            "border-border bg-surface h-11 w-full rounded-xl border px-3.5 text-[14px] transition-all",
            "placeholder:text-muted-foreground/55 outline-none",
            "hover:border-border/80",
            "focus-visible:border-brand/40 focus-visible:shadow-[0_0_0_3px_color-mix(in_oklab,var(--brand)_16%,transparent)]",
            adornment && "pr-11",
          )}
          type={type}
          required={required}
          autoComplete={autoComplete}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
        {adornment && (
          <div className="absolute top-1/2 right-2.5 -translate-y-1/2">{adornment}</div>
        )}
      </div>
    </div>
  );
}

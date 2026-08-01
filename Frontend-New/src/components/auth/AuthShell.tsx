import { type ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Link } from "@tanstack/react-router";
import { AuthAtmosphere } from "./AuthAtmosphere";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/shell/ThemeToggle";

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  const reduceMotion = useReducedMotion();

  return (
    <div className="bg-background text-foreground grid min-h-screen grid-cols-1 lg:grid-cols-[1.05fr_1fr]">
      {/* Visual panel — scoped `dark` so it keeps its own token island while
          the form side follows the user's chosen theme. */}
      <div className="dark relative hidden lg:block">
        <AuthAtmosphere />
      </div>

      <div className="relative flex flex-col px-6 py-8 sm:px-12 lg:px-14">
        <div className="flex items-center justify-between">
          <Link to="/" className="lg:invisible" aria-label="InfiChat home">
            <Logo size={21} />
          </Link>
          <ThemeToggle />
        </div>

        <div className="flex flex-1 items-center justify-center py-10">
          <motion.div
            className="w-full max-w-[380px]"
            initial={reduceMotion ? undefined : { opacity: 0, y: 16 }}
            animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
          >
            <h1
              className="text-balance font-medium tracking-[-0.028em]"
              style={{ fontSize: "clamp(1.65rem, 2.1vw, 2.05rem)", lineHeight: 1.12 }}
            >
              {title}
            </h1>
            <p className="text-muted-foreground mt-2.5 text-[14.5px] leading-relaxed">
              {subtitle}
            </p>

            <div className="mt-8">{children}</div>

            <div className="text-muted-foreground mt-8 text-[13.5px]">{footer}</div>
          </motion.div>
        </div>

        {/* Informational only. Actual consent is an affirmative act — the two
            required checkboxes on the registration form — never this line. */}
        <p className="text-muted-foreground/70 text-center text-[11.5px] leading-relaxed">
          Read our{" "}
          <Link
            to="/terms"
            className="hover:text-foreground underline decoration-dotted underline-offset-2"
          >
            Terms
          </Link>{" "}
          and{" "}
          <Link
            to="/privacy"
            className="hover:text-foreground underline decoration-dotted underline-offset-2"
          >
            Privacy Policy
          </Link>
          .
        </p>
      </div>
    </div>
  );
}

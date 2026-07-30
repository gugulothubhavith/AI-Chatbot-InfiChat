import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { MessageSquareText, Code2, Telescope, Sparkles } from "lucide-react";
import { Logo } from "@/components/brand/Logo";

/**
 * Left-hand visual panel for the auth routes.
 *
 * Always dark regardless of the active theme — it's a fixed brand surface,
 * like the dark hero panels on Linear/Vercel auth pages. Depth comes from a
 * gradient mesh, a fine grain layer, and glass capability cards that parallax
 * against pointer movement.
 */

const CAPABILITIES = [
  { icon: MessageSquareText, label: "Chat", detail: "Long-context conversations" },
  { icon: Code2, label: "Code", detail: "Write, review, and run" },
  { icon: Telescope, label: "Research", detail: "Cited, multi-source answers" },
  { icon: Sparkles, label: "Images", detail: "Generate and iterate" },
] as const;

export function AuthAtmosphere() {
  const ref = useRef<HTMLDivElement>(null);
  const reduceMotion = useReducedMotion();
  const [pointer, setPointer] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (reduceMotion) return;
    const el = ref.current;
    if (!el) return;

    let frame = 0;
    const onMove = (e: PointerEvent) => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        const r = el.getBoundingClientRect();
        // -1..1 from panel center, for parallax offsets.
        setPointer({
          x: ((e.clientX - r.left) / r.width - 0.5) * 2,
          y: ((e.clientY - r.top) / r.height - 0.5) * 2,
        });
      });
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      window.removeEventListener("pointermove", onMove);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [reduceMotion]);

  const shift = (depth: number) => ({
    x: reduceMotion ? 0 : pointer.x * depth,
    y: reduceMotion ? 0 : pointer.y * depth,
  });

  return (
    <div
      ref={ref}
      className="relative isolate h-full w-full overflow-hidden bg-[#07080B]"
    >
      {/* Gradient mesh — three offset blooms that drift slowly. */}
      <motion.div
        aria-hidden
        className="absolute -inset-1/4"
        animate={
          reduceMotion ? undefined : { scale: [1, 1.08, 1], rotate: [0, 6, 0] }
        }
        transition={{ duration: 34, repeat: Infinity, ease: "easeInOut" }}
        style={{
          background: `
            radial-gradient(42% 46% at 24% 26%, color-mix(in oklab, var(--brand) 62%, transparent), transparent 70%),
            radial-gradient(40% 44% at 74% 34%, rgba(139,92,246,0.42), transparent 72%),
            radial-gradient(52% 50% at 52% 82%, rgba(34,211,238,0.24), transparent 76%)
          `,
          filter: "blur(56px)",
        }}
      />

      {/* Vignette so the type never sits on a hot spot. */}
      <div
        aria-hidden
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(78% 78% at 50% 42%, transparent 30%, rgba(7,8,11,0.72) 100%)",
        }}
      />

      {/* Grain — kills the plastic look of pure gradients. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.22] mix-blend-overlay"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='140' height='140' filter='url(%23n)' opacity='0.5'/%3E%3C/svg%3E\")",
          backgroundSize: "140px 140px",
        }}
      />

      {/* Hairline grid, masked to the center. */}
      <div
        aria-hidden
        className="absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
          backgroundSize: "88px 88px",
          maskImage:
            "radial-gradient(ellipse 70% 60% at 50% 45%, black 30%, transparent 78%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 70% 60% at 50% 45%, black 30%, transparent 78%)",
        }}
      />

      {/* Content */}
      <div className="relative z-10 flex h-full flex-col justify-between p-10 xl:p-14">
        <Logo size={22} className="[&_span]:!text-white [&_.bg-foreground]:!bg-white" />

        <motion.div
          className="max-w-lg"
          animate={shift(-10)}
          transition={{ type: "spring", stiffness: 60, damping: 20 }}
        >
          <h2
            className="text-balance font-medium tracking-[-0.03em] text-white"
            style={{ fontSize: "clamp(2.1rem, 2.6vw, 3.1rem)", lineHeight: 1.06 }}
          >
            One workspace for
            <br />
            <span className="text-white/45">your team's thinking.</span>
          </h2>
          <p className="mt-5 max-w-md text-[15px] leading-relaxed text-white/55">
            Chat, write code, research with citations, and generate images —
            with shared projects and history your whole team can build on.
          </p>

          <div className="mt-9 grid grid-cols-2 gap-2.5">
            {CAPABILITIES.map(({ icon: Icon, label, detail }, i) => (
              <motion.div
                key={label}
                initial={reduceMotion ? undefined : { opacity: 0, y: 14 }}
                animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
                transition={{ delay: 0.16 + i * 0.07, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                className="rounded-xl border border-white/10 bg-white/[0.04] p-3.5 backdrop-blur-md"
                style={{
                  boxShadow:
                    "inset 0 1px 0 rgba(255,255,255,0.09), 0 18px 44px -26px rgba(0,0,0,0.9)",
                }}
              >
                <Icon className="h-4 w-4 text-white/75" strokeWidth={1.75} />
                <div className="mt-2.5 text-[13px] font-medium text-white/90">{label}</div>
                <div className="mt-0.5 text-[11.5px] leading-snug text-white/45">{detail}</div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        <div className="flex items-center gap-2.5 text-[11.5px] text-white/40">
          <span className="relative flex h-1.5 w-1.5">
            {!reduceMotion && (
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/70" />
            )}
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
          </span>
          Private by design · SSO &amp; SAML · Audit logs
        </div>
      </div>
    </div>
  );
}

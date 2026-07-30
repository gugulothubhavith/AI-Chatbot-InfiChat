import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { LogoMark } from "@/components/brand/Logo";

export function OrbCanvas() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onMove = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 100;
      const y = ((e.clientY - rect.top) / rect.height) * 100;
      el.style.setProperty("--mx", `${x}%`);
      el.style.setProperty("--my", `${y}%`);
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  return (
    <div
      ref={ref}
      className="relative h-full w-full overflow-hidden bg-[#050608]"
      style={{ ["--mx" as string]: "50%", ["--my" as string]: "50%" }}
    >
      {/* Deep background wash */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(70% 70% at var(--mx) var(--my), rgba(59,130,246,0.35), transparent 70%), radial-gradient(90% 90% at 20% 80%, rgba(34,211,238,0.18), transparent 75%)",
          transition: "background 0.5s ease",
        }}
      />

      {/* Grid lines */}
      <div
        className="absolute inset-0 opacity-[0.08]"
        style={{
          backgroundImage:
            "linear-gradient(to right, #fff 1px, transparent 1px), linear-gradient(to bottom, #fff 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          maskImage: "radial-gradient(ellipse at center, black 40%, transparent 80%)",
        }}
      />

      {/* Central orb */}
      <div className="absolute inset-0 flex items-center justify-center">
        <motion.div
          className="relative h-[420px] w-[420px]"
          animate={{ rotate: 360 }}
          transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
        >
          <div
            className="absolute inset-0 rounded-full blur-2xl"
            style={{
              background:
                "conic-gradient(from 0deg, #3B82F6, #22D3EE, #8B5CF6, #3B82F6)",
              opacity: 0.55,
            }}
          />
          <div
            className="absolute inset-6 rounded-full"
            style={{
              background:
                "radial-gradient(circle at 30% 30%, rgba(255,255,255,0.9), rgba(59,130,246,0.3) 40%, transparent 70%)",
              filter: "blur(2px)",
              opacity: 0.4,
            }}
          />
        </motion.div>

        <motion.div
          className="absolute h-[220px] w-[220px] rounded-full border border-white/10 backdrop-blur-md"
          animate={{ scale: [1, 1.06, 1] }}
          transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
          style={{
            background:
              "radial-gradient(circle at 35% 30%, rgba(255,255,255,0.14), rgba(10,10,12,0.4) 60%)",
            boxShadow:
              "inset 0 1px 0 rgba(255,255,255,0.25), 0 30px 80px -20px rgba(59,130,246,0.55)",
          }}
        />

        <motion.div
          className="absolute flex items-center justify-center"
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
        >
          <span className="font-bold text-white leading-none" style={{ fontSize: 42, letterSpacing: "-0.02em" }}>InfiChat</span>
        </motion.div>

      </div>

      {/* Star field */}
      <div
        className="absolute inset-0 opacity-60"
        style={{
          backgroundImage:
            "radial-gradient(1px 1px at 20% 30%, rgba(255,255,255,0.9) 0, transparent 100%), radial-gradient(1px 1px at 60% 70%, rgba(255,255,255,0.7) 0, transparent 100%), radial-gradient(1.5px 1.5px at 80% 20%, rgba(255,255,255,0.9) 0, transparent 100%), radial-gradient(1px 1px at 40% 80%, rgba(255,255,255,0.6) 0, transparent 100%), radial-gradient(1px 1px at 15% 60%, rgba(255,255,255,0.8) 0, transparent 100%), radial-gradient(1px 1px at 75% 55%, rgba(255,255,255,0.7) 0, transparent 100%)",
          backgroundSize: "500px 500px, 380px 380px, 620px 620px, 440px 440px, 300px 300px, 520px 520px",
        }}
      />

      {/* Bottom fade */}
      <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#050608] to-transparent" />
    </div>
  );
}

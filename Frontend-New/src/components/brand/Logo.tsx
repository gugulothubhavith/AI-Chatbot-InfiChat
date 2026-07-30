import { motion } from "framer-motion";

/**
 * InfiChat brand mark — renders /logo-icon.svg as a CSS mask so it
 * inherits the current foreground color (black in light mode, white
 * in dark mode) and stays crisp at any size.
 */
export function LogoMark({
  size = 24,
  className = "",
  animated = false,
}: {
  size?: number;
  className?: string;
  animated?: boolean;
}) {
  const w = size * (500 / 237);
  const h = size;
  const style = {
    width: w,
    height: h,
    WebkitMaskImage: "url(/logo-icon.svg)",
    maskImage: "url(/logo-icon.svg)",
    WebkitMaskRepeat: "no-repeat",
    maskRepeat: "no-repeat",
    WebkitMaskPosition: "center",
    maskPosition: "center",
    WebkitMaskSize: "contain",
    maskSize: "contain",
  } as const;

  if (animated) {
    return (
      <motion.span
        aria-hidden="true"
        className={`inline-block bg-foreground shrink-0 ${className}`}
        style={style}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.9, ease: "easeOut" }}
      />
    );
  }

  return (
    <span
      aria-hidden="true"
      className={`inline-block bg-foreground shrink-0 ${className}`}
      style={style}
    />
  );
}

export function Logo({
  size = 22,
  className = "",
  animated = false,
  showWord = true,
}: {
  size?: number;
  className?: string;
  animated?: boolean;
  showWord?: boolean;
}) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <LogoMark size={size} animated={animated} />
      {showWord && (
        <span
          className="select-none font-bold text-foreground leading-none"
          style={{
            fontSize: size * 1.05,
            letterSpacing: "-0.01em",
            fontFamily:
              "'Söhne', 'Inter', 'Geist', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', sans-serif",
          }}
        >
          InfiChat
        </span>
      )}
    </div>
  );
}

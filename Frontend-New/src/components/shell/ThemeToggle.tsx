import { Sun, Moon, Monitor } from "lucide-react";
import { motion } from "framer-motion";
import { useSettingsStore, type Theme } from "@/stores/settings";
import { cn } from "@/lib/utils";

const OPTIONS: { id: Theme; label: string; icon: typeof Sun }[] = [
  { id: "light", label: "Light", icon: Sun },
  { id: "dark", label: "Dark", icon: Moon },
  { id: "system", label: "System", icon: Monitor },
];

/**
 * Segmented Light / Dark / System control.
 *
 * Used on the auth routes, where the full settings dialog isn't reachable
 * yet. Writes through the same store as Settings → Appearance, so the choice
 * persists to localStorage and carries into the app after sign-in.
 */
export function ThemeToggle({ className }: { className?: string }) {
  const theme = useSettingsStore((s) => s.theme);
  const setSetting = useSettingsStore((s) => s.set);

  return (
    <div
      role="radiogroup"
      aria-label="Color theme"
      className={cn(
        "border-border bg-surface/60 inline-flex items-center gap-0.5 rounded-full border p-0.5 backdrop-blur-sm",
        className,
      )}
    >
      {OPTIONS.map(({ id, label, icon: Icon }) => {
        const active = theme === id;
        return (
          <button
            key={id}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={label}
            title={label}
            onClick={() => setSetting("theme", id)}
            className={cn(
              "relative flex h-7 w-7 items-center justify-center rounded-full outline-none transition-colors",
              "focus-visible:ring-brand/50 focus-visible:ring-2",
              active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
            )}
          >
            {active && (
              <motion.span
                layoutId="theme-toggle-active"
                transition={{ type: "spring", stiffness: 420, damping: 34 }}
                className="bg-accent absolute inset-0 rounded-full"
              />
            )}
            <Icon className="relative h-3.5 w-3.5" />
          </button>
        );
      })}
    </div>
  );
}

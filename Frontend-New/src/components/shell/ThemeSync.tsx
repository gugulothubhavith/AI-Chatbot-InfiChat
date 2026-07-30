import { useEffect } from "react";
import { useSettingsStore, ACCENTS, type Theme } from "@/stores/settings";

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  const isDark =
    theme === "dark" ||
    (theme === "system" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);

  // The pre-paint script in __root.tsx already set the correct class, so on a
  // normal load this is a no-op. Bailing out early avoids a pointless
  // transition-suppression cycle on every unrelated store update.
  if (root.classList.contains("dark") === isDark) return;

  // Suppress CSS transitions during the swap to avoid flashing on elements
  // with transition-colors (selected chat/history items).
  root.classList.add("theme-switching");
  root.classList.toggle("dark", isDark);
  root.style.colorScheme = isDark ? "dark" : "light";
  // Force reflow, then remove on next frame so transitions resume.
  void root.offsetHeight;
  requestAnimationFrame(() => {
    requestAnimationFrame(() => root.classList.remove("theme-switching"));
  });
}

export function ThemeSync() {
  const accent = useSettingsStore((s) => s.accent);

  // Subscribe imperatively rather than reading `theme` through a selector.
  // A selector value is captured at render time, so an effect reading it can
  // run with a stale theme and strip the class the pre-paint script set.
  useEffect(() => {
    applyTheme(useSettingsStore.getState().theme);
    return useSettingsStore.subscribe((s, prev) => {
      if (s.theme !== prev.theme) applyTheme(s.theme);
    });
  }, []);

  // Follow the OS preference only while "system" is selected.
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      if (useSettingsStore.getState().theme === "system") applyTheme("system");
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    useSettingsStore.getState().hydrate();
    import("@/stores/billing").then((m) => m.useBillingStore.getState().hydrate());
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.style.setProperty("--brand", ACCENTS[accent].oklch);
    root.style.setProperty("--ring", ACCENTS[accent].oklch);
  }, [accent]);

  return null;
}

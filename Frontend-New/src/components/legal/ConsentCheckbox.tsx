import { useId } from "react";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

/**
 * The consent row, shared by registration and the re-consent modal.
 *
 * Both surfaces collect the same two affirmative acts and must look and behave
 * identically doing it — a box that is unticked in one place and pre-ticked in
 * the other is the sort of drift that turns into a compliance finding. One
 * implementation makes that impossible rather than merely unlikely.
 */

/** Link styling for policy links sitting inside a consent label. */
export const consentLinkClass =
  "text-foreground font-medium underline decoration-border underline-offset-2 transition-colors hover:decoration-foreground";

/** Name the boxes that are still empty, so the message says what to do rather
 *  than only that something is wrong. */
export function consentGapMessage(terms: boolean, privacy: boolean): string | null {
  if (terms && privacy) return null;
  if (!terms && !privacy) {
    return "Please accept the Terms of Service and the Privacy Policy to continue.";
  }
  return terms
    ? "Please accept the Privacy Policy to continue."
    : "Please accept the Terms of Service to continue.";
}

/**
 * One consent row: an unticked box plus a label containing live links.
 *
 * The label is a real `<label htmlFor>`, so clicking the wording toggles the
 * box. Clicking a link inside it navigates instead, and does not tick anything:
 * a label's activation behaviour is defined to do nothing for clicks targeting
 * an interactive descendant, and an anchor with an `href` is interactive
 * content. Reading the policy must never be mistaken for accepting it.
 */
export function ConsentCheckbox({
  checked,
  onChange,
  invalid,
  disabled,
  describedBy,
  children,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  invalid?: boolean;
  disabled?: boolean;
  describedBy?: string;
  children: React.ReactNode;
}) {
  const id = useId();

  return (
    <div className="flex items-start gap-2.5">
      <Checkbox
        id={id}
        checked={checked}
        // Radix reports `boolean | "indeterminate"`; these boxes are binary.
        onCheckedChange={(value) => onChange(value === true)}
        disabled={disabled}
        aria-required
        aria-invalid={invalid || undefined}
        aria-describedby={describedBy}
        className={cn(
          "mt-0.5 shrink-0",
          invalid && "border-destructive data-[state=unchecked]:border-destructive",
        )}
      />
      <label
        htmlFor={id}
        className="text-muted-foreground cursor-pointer text-[12.5px] leading-[1.55] select-none"
      >
        {children}
      </label>
    </div>
  );
}

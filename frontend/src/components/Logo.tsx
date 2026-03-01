
interface LogoProps {
    /** Height of the icon in pixels. Defaults to 40. */
    iconSize?: number;
    /** Height of the app name text image in px. Defaults to 20px. */
    nameSize?: number;
    /** Layout direction. Defaults to 'row' (icon + text side by side). */
    direction?: "row" | "col";
    /** Gap between icon and name in px. Defaults to 8. */
    gap?: number;
    /** Whether to show just the icon without the app name. */
    iconOnly?: boolean;
    /** Whether to hide the icon. */
    hideIcon?: boolean;
    className?: string;
}

export function Logo({
    iconSize = 40,
    nameSize = 20,
    direction = "row",
    gap = 8,
    iconOnly = false,
    hideIcon = false,
    className = "",
}: LogoProps) {
    return (
        <div
            role="img"
            aria-label="InfiChat"
            className={`flex items-center ${className}`}
            style={{
                flexDirection: direction === "col" ? "column" : "row",
                gap: `${gap}px`,
                userSelect: "none",
            }}
        >
            {!hideIcon && (
                <img
                    src="/logo_icon.png"
                    alt=""
                    aria-hidden="true"
                    style={{ height: `${iconSize}px`, width: "auto" }}
                    className="object-contain drop-shadow-md flex-shrink-0"
                    draggable={false}
                />
            )}
            {!iconOnly && (
                <img
                    src="/app_name.png"
                    alt=""
                    aria-hidden="true"
                    style={{ height: `${nameSize}px`, width: "auto" }}
                    className="object-contain flex-shrink-0"
                    draggable={false}
                />
            )}
        </div>
    );
}

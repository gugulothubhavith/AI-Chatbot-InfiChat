import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/stores/auth";
import { useSettingsDialog } from "./settings-context";
import { useNavigate } from "@tanstack/react-router";
import { ChevronsUpDown, LogOut, Settings, CreditCard } from "lucide-react";

export function UserMenu() {
  const user = useAuthStore((s) => s.user);
  const signOut = useAuthStore((s) => s.signOut);
  const { setOpen } = useSettingsDialog();
  const nav = useNavigate();

  const initial = (user?.name ?? "?").charAt(0).toUpperCase();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex w-full items-center gap-2.5 rounded-lg border border-border/60 bg-surface/60 p-2 text-left elevated hover:bg-surface-2">
          <div className="flex h-8 w-8 overflow-hidden items-center justify-center rounded-md bg-gradient-to-br from-brand to-brand/70 text-xs font-medium text-brand-foreground">
            {user?.avatar ? (
              <img src={user.avatar} alt={user.name} referrerPolicy="no-referrer" className="h-full w-full object-cover" />
            ) : (
              initial
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="truncate text-[13px] font-medium">{user?.name ?? "Guest"}</div>
            <div className="truncate text-[11px] text-muted-foreground">{user?.email ?? "—"}</div>
          </div>
          <ChevronsUpDown className="h-3.5 w-3.5 text-muted-foreground" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel className="text-xs text-muted-foreground">Account</DropdownMenuLabel>
        <DropdownMenuItem onClick={() => setOpen(true)}>
          <Settings className="mr-2 h-3.5 w-3.5" /> Settings
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => nav({ to: "/billing" })}>
          <CreditCard className="mr-2 h-3.5 w-3.5" /> Billing
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => {
            signOut();
            nav({ to: "/login" });
          }}
          className="text-destructive focus:text-destructive"
        >
          <LogOut className="mr-2 h-3.5 w-3.5" /> Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

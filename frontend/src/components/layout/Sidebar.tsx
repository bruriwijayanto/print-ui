import { NavLink } from "react-router-dom";
import { LayoutDashboard, Printer, Send, ListChecks, Settings, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/printers", label: "Printers", icon: Printer },
  { to: "/print", label: "Print", icon: Send },
  { to: "/jobs", label: "Jobs", icon: ListChecks },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  return (
    <aside className="hidden w-60 shrink-0 border-r border-sidebar-border bg-sidebar md:block">
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-sidebar-accent text-sidebar-accent-foreground">
          <Zap className="h-4 w-4" />
        </span>
        <span className="text-sm font-semibold text-sidebar-foreground">CUPS Print Manager</span>
      </div>
      <nav className="flex flex-col gap-1 p-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-lg border-l-2 px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "border-sidebar-accent bg-white/10 text-white"
                  : "border-transparent text-sidebar-muted hover:bg-white/5 hover:text-sidebar-foreground",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

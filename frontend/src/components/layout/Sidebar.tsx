import { NavLink } from "react-router-dom";
import { LayoutDashboard, Printer, Send, ListChecks, Settings } from "lucide-react";
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
    <aside className="hidden w-56 shrink-0 border-r border-border bg-card md:block">
      <div className="flex h-14 items-center border-b border-border px-4">
        <span className="text-sm font-semibold">CUPS Print Manager</span>
      </div>
      <nav className="flex flex-col gap-1 p-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive ? "bg-primary text-primary-foreground" : "text-foreground hover:bg-accent",
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

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

export function MobileNav() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-card md:hidden">
      {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          className={({ isActive }) =>
            cn(
              "flex flex-1 flex-col items-center gap-1 py-2 text-[11px] font-medium",
              isActive ? "text-primary" : "text-muted-foreground",
            )
          }
        >
          <Icon className="h-5 w-5" />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}

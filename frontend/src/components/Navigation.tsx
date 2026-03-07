import { NavLink } from "react-router-dom";
import { Home, ClipboardList, TrendingUp, X } from "lucide-react";

const navItems = [
  { to: "/", icon: Home, label: "Главная" },
  { to: "/tasks", icon: ClipboardList, label: "Задания" },
  { to: "/progress", icon: TrendingUp, label: "Прогресс" },
];

export default function Navigation() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-surface-card border-t border-surface-tertiary z-50">
      <div className="flex justify-around items-center h-16 max-w-lg mx-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 px-3 py-1 transition-colors ${
                isActive
                  ? "text-meridian-600"
                  : "text-ink-muted hover:text-ink-secondary"
              }`
            }
          >
            <Icon size={22} strokeWidth={1.8} />
            <span className="text-[11px] font-medium">{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}

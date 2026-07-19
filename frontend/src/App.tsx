import { NavLink, Route, Routes } from "react-router-dom";
import Extract from "./pages/Extract";
import Tasks from "./pages/Tasks";
import Integrations from "./pages/Integrations";

const navItems = [
  { to: "/", label: "Extract", icon: "🧠", end: true },
  { to: "/tasks", label: "Tasks", icon: "✅", end: false },
  { to: "/integrations", label: "Integrations", icon: "🔗", end: false },
];

export default function App() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-60 shrink-0 border-r border-edge bg-panel/60 px-5 py-6">
        <div className="text-xl font-semibold tracking-tight text-white">InboxIQ</div>
        <div className="mt-1 text-xs text-slate-500">Email action-item extraction</div>
        <nav className="mt-8 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                  isActive
                    ? "bg-accent/20 text-white"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="flex-1 px-8 py-10">
        <div className="mx-auto max-w-5xl">
          <Routes>
            <Route path="/" element={<Extract />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/integrations" element={<Integrations />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

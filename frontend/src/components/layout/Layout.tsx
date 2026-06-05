import { Outlet, NavLink } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/patients", label: "Patients" },
  { to: "/cases", label: "Cases" },
  { to: "/hospitals", label: "Hospitals" },
  { to: "/funding", label: "Funding" },
  { to: "/follow-ups", label: "Follow-Ups" },
  { to: "/ai-assistant", label: "AI Assistant" },
  { to: "/settings", label: "Settings" },
];

const adminNavItems = [
  { to: "/admin/users", label: "Users" },
  { to: "/admin/audit-log", label: "Audit Log" },
];

export default function Layout() {
  const { user, logout, isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-lg font-bold text-blue-700">Patient Navigator</h1>
          <p className="text-xs text-gray-500 mt-1">Care Coordination Platform</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}

          {user?.role === "admin" && (
            <div className="pt-4 mt-4 border-t border-gray-200">
              <p className="px-3 text-xs font-semibold text-gray-400 uppercase mb-2">Admin</p>
              {adminNavItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive ? "bg-blue-50 text-blue-700" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          )}
        </nav>

        {isAuthenticated && user && (
          <div className="p-4 border-t border-gray-200">
            <div className="text-sm">
              <p className="font-medium text-gray-900">{user.full_name}</p>
              <p className="text-gray-500 text-xs">{user.role}</p>
            </div>
            <button
              onClick={logout}
              className="mt-2 text-xs text-red-600 hover:text-red-800"
            >
              Sign out
            </button>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

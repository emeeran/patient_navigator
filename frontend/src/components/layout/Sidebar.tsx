import { useState, useEffect, useCallback, useRef } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard", icon: "🏠" },
  { to: "/patients", label: "Patients", icon: "👤" },
  { to: "/cases", label: "Cases", icon: "📋" },
  { to: "/hospitals", label: "Hospitals", icon: "🏥" },
  { to: "/doctors", label: "Doctors", icon: "🩺" },
  { to: "/funding", label: "Funding", icon: "💰" },
  { to: "/follow-ups", label: "Follow-Ups", icon: "📅" },
  { to: "/ai-assistant", label: "AI Assistant", icon: "🤖" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

const adminNavItems = [
  { to: "/admin/users", label: "Users", icon: "👥" },
  { to: "/admin/data-scraper", label: "Data Scraper", icon: "🔍" },
  { to: "/admin/audit-log", label: "Audit Log", icon: "📊" },
];

const MIN_WIDTH = 200;
const MAX_WIDTH = 400;
const COLLAPSED_WIDTH = 64;
const DEFAULT_WIDTH = 256;

export default function Sidebar() {
  const { user, logout, isAuthenticated } = useAuth();
  const [collapsed, setCollapsed] = useState<boolean>(
    () => localStorage.getItem("sidebar_collapsed") === "true"
  );
  const [width, setWidth] = useState<number>(
    () => Number(localStorage.getItem("sidebar_width")) || DEFAULT_WIDTH
  );
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLElement>(null);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("sidebar_collapsed", String(next));
      return next;
    });
  }, []);

  // Keyboard shortcut: Ctrl/Cmd + B
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "b") {
        e.preventDefault();
        toggleCollapsed();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [toggleCollapsed]);

  // Resize drag logic
  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, e.clientX));
      setWidth(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      setWidth((w) => {
        localStorage.setItem("sidebar_width", String(w));
        return w;
      });
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizing]);

  const currentWidth = collapsed ? COLLAPSED_WIDTH : width;

  return (
    <aside
      ref={sidebarRef}
      className="bg-white border-r border-gray-200 flex flex-col flex-shrink-0 relative"
      style={{
        width: currentWidth,
        transition: isResizing ? "none" : "width 200ms ease-in-out",
      }}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Brand */}
      <div className="border-b border-gray-200 flex items-center h-16 px-4">
        <span className="text-xl shrink-0">🩺</span>
        {!collapsed && (
          <div className="ml-3 overflow-hidden whitespace-nowrap">
            <h1 className="text-base font-bold text-blue-700 leading-tight">Patient Navigator</h1>
            <p className="text-[10px] text-gray-500 leading-tight">Care Coordination Platform</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-2 overflow-y-auto overflow-x-hidden" aria-label="Primary">
        <ul className="space-y-0.5 px-2">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-2.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`
                }
                title={collapsed ? item.label : undefined}
              >
                <span className="text-base shrink-0 w-6 text-center">{item.icon}</span>
                {!collapsed && (
                  <span className="truncate">{item.label}</span>
                )}
              </NavLink>
            </li>
          ))}
        </ul>

        {user?.role === "admin" && (
          <div className="pt-3 mt-3 mx-2 border-t border-gray-200">
            {!collapsed && (
              <p className="px-2.5 text-[10px] font-semibold text-gray-400 uppercase mb-1.5 tracking-wider">Admin</p>
            )}
            <ul className="space-y-0.5">
              {adminNavItems.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-2.5 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-blue-50 text-blue-700"
                          : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                      }`
                    }
                    title={collapsed ? item.label : undefined}
                  >
                    <span className="text-base shrink-0 w-6 text-center">{item.icon}</span>
                    {!collapsed && (
                      <span className="truncate">{item.label}</span>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        )}
      </nav>

      {/* User footer */}
      {isAuthenticated && user && (
        <div className="border-t border-gray-200 p-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-bold shrink-0">
              {user.full_name?.charAt(0)?.toUpperCase() || "?"}
            </div>
            {!collapsed && (
              <div className="overflow-hidden min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user.full_name}</p>
                <p className="text-gray-500 text-[10px] capitalize truncate">{user.role}</p>
              </div>
            )}
          </div>
          {!collapsed && (
            <button
              onClick={logout}
              className="mt-2 text-xs text-red-600 hover:text-red-800 transition-colors"
              aria-label="Sign out"
            >
              Sign out
            </button>
          )}
        </div>
      )}

      {/* Collapse toggle */}
      <button
        onClick={toggleCollapsed}
        className="absolute -right-3 top-7 w-6 h-6 bg-white border border-gray-200 rounded-full flex items-center justify-center shadow-sm hover:bg-gray-50 transition-colors z-10"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        title={collapsed ? "Expand sidebar (Ctrl+B)" : "Collapse sidebar (Ctrl+B)"}
      >
        <svg
          className={`w-3.5 h-3.5 text-gray-500 transition-transform duration-200 ${collapsed ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      {/* Resize handle */}
      {!collapsed && (
        <div
          onMouseDown={() => setIsResizing(true)}
          className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-200 active:bg-blue-400 transition-colors z-10"
          title="Drag to resize"
        />
      )}
    </aside>
  );
}

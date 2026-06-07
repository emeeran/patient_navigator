import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { patientsApi, casesApi, hospitalsApi, doctorsApi, fundingApi, followUpsApi } from "../api";

interface CardData {
  label: string;
  href: string;
  color: string;
  icon: string;
  count: number;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [cards, setCards] = useState<CardData[]>([]);

  useEffect(() => {
    async function loadCounts() {
      const [p, c, h, d, f, fu] = await Promise.allSettled([
        patientsApi.list({ per_page: 1 }),
        casesApi.list({ per_page: 1 }),
        hospitalsApi.list({ per_page: 1 }),
        doctorsApi.list({ per_page: 1 }),
        fundingApi.list({ per_page: 1 }),
        followUpsApi.upcoming({ per_page: 1 }),
      ]);

      const count = (r: PromiseSettledResult<{ data: { total: number } }>) =>
        r.status === "fulfilled" ? r.value.data.total : 0;

      setCards([
        { label: "Patients", href: "/patients", color: "bg-blue-500", icon: "👤", count: count(p) },
        { label: "Cases", href: "/cases", color: "bg-green-500", icon: "📋", count: count(c) },
        { label: "Hospitals", href: "/hospitals", color: "bg-purple-500", icon: "🏥", count: count(h) },
        { label: "Doctors", href: "/doctors", color: "bg-teal-500", icon: "🩺", count: count(d) },
        { label: "Funding", href: "/funding", color: "bg-pink-500", icon: "💰", count: count(f) },
        { label: "Follow-Ups", href: "/follow-ups", color: "bg-indigo-500", icon: "📅", count: count(fu) },
        { label: "AI Assistant", href: "/ai-assistant", color: "bg-cyan-500", icon: "🤖", count: 0 },
      ]);
    }
    loadCounts();
  }, []);

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900">
          Welcome back, {user?.full_name?.split(" ")[0] || "User"}
        </h2>
        <p className="text-gray-500 mt-1">
          Here's an overview of your care coordination workspace.
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-4">
        {cards.map((card) => (
          <Link
            key={card.label}
            to={card.href}
            className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className={`w-10 h-10 ${card.color} rounded-lg flex items-center justify-center text-white text-lg`}>
                {card.icon}
              </div>
            </div>
            <h3 className="font-semibold text-gray-900">{card.label}</h3>
            {card.label !== "AI Assistant" && (
              <p className="text-2xl font-bold text-gray-700 mt-1">{card.count}</p>
            )}
            {card.label === "AI Assistant" && (
              <p className="text-sm text-gray-500 mt-1">Open tools</p>
            )}
          </Link>
        ))}
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-4">
        <p className="text-sm text-blue-800">
          <strong>AI Assistant:</strong> Use the Cases section to generate AI
          medical summaries, explain terms, and get specialist recommendations.
        </p>
      </div>

      {/* Funding stats */}
      {cards.length > 0 && cards.find((c) => c.label === "Funding") && (
        <FundingStats />
      )}
    </div>
  );
}

function FundingStats() {
  const [stats, setStats] = useState<{ active: number; avgMax: number; expiringSoon: number; expired: number } | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const { data } = await fundingApi.list({ per_page: 100, is_active: true });
        const programs = data.items;
        const now = Date.now();
        const active = programs.length;
        const avgMax = programs.length
          ? Math.round(programs.reduce((sum, p) => sum + (p.max_amount || 0), 0) / programs.length)
          : 0;
        const expiringSoon = programs.filter((p) => {
          if (!p.deadline) return false;
          const days = Math.ceil((new Date(p.deadline).getTime() - now) / 86400000);
          return days >= 0 && days <= 30;
        }).length;
        const expired = programs.filter((p) => {
          if (!p.deadline) return false;
          return new Date(p.deadline).getTime() < now;
        }).length;
        setStats({ active, avgMax, expiringSoon, expired });
      } catch { /* ok */ }
    }
    load();
  }, []);

  if (!stats) return null;

  return (
    <div className="mt-6 bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">Funding Overview</h3>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div>
          <p className="text-2xl font-bold text-gray-900">{stats.active}</p>
          <p className="text-xs text-gray-500">Active Programs</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">₹{stats.avgMax.toLocaleString()}</p>
          <p className="text-xs text-gray-500">Avg Max Amount</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-amber-600">{stats.expiringSoon}</p>
          <p className="text-xs text-gray-500">Expiring Soon</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-red-600">{stats.expired}</p>
          <p className="text-xs text-gray-500">Expired</p>
        </div>
      </div>
    </div>
  );
}
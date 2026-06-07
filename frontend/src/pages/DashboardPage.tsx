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
    </div>
  );
}

import { useAuth } from "../contexts/AuthContext";

export default function DashboardPage() {
  const { user } = useAuth();

  const cards = [
    { label: "Patients", href: "/patients", color: "bg-blue-500" },
    { label: "Cases", href: "/cases", color: "bg-green-500" },
    { label: "Documents", href: "/cases", color: "bg-yellow-500" },
    { label: "Hospitals", href: "/hospitals", color: "bg-purple-500" },
    { label: "Funding", href: "/funding", color: "bg-pink-500" },
    { label: "Follow-Ups", href: "/follow-ups", color: "bg-indigo-500" },
  ];

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

      <div className="grid grid-cols-3 gap-4">
        {cards.map((card) => (
          <a
            key={card.label}
            href={card.href}
            className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            <div className={`w-10 h-10 ${card.color} rounded-lg mb-3`} />
            <h3 className="font-semibold text-gray-900">{card.label}</h3>
            <p className="text-sm text-gray-500 mt-1">View and manage</p>
          </a>
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

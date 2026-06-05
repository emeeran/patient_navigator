import { useState, useEffect } from "react";
import { casesApi } from "../api";
import type { Case } from "../types";

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    setLoading(true);
    try {
      const { data } = await casesApi.list({ per_page: 20 });
      setCases(data.items);
      setTotal(data.total);
    } catch {
      /* handled by interceptor */
    } finally {
      setLoading(false);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "new":
        return "bg-blue-100 text-blue-700";
      case "under_review":
        return "bg-yellow-100 text-yellow-700";
      case "in_treatment":
        return "bg-green-100 text-green-700";
      case "closed":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const priorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "text-red-600";
      case "medium":
        return "text-yellow-600";
      case "low":
        return "text-green-600";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Cases</h2>
        <span className="text-sm text-gray-500">{total} total</span>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="space-y-3">
          {cases.map((c) => (
            <div
              key={c.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {c.diagnosis}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Case ID: {c.id.slice(0, 8)}...
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex px-2.5 py-1 text-xs font-medium rounded-full ${statusColor(c.status)}`}
                  >
                    {c.status.replace("_", " ")}
                  </span>
                  <span
                    className={`text-xs font-medium capitalize ${priorityColor(c.priority)}`}
                  >
                    {c.priority}
                  </span>
                </div>
              </div>
              {c.notes && (
                <p className="text-sm text-gray-600 mt-2">{c.notes}</p>
              )}
            </div>
          ))}
          {cases.length === 0 && (
            <p className="text-center text-gray-500 py-8">No cases found</p>
          )}
        </div>
      )}
    </div>
  );
}

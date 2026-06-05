import { useState, useEffect } from "react";
import { followUpsApi } from "../api";
import type { FollowUp } from "../types";

export default function FollowUpsPage() {
  const [items, setItems] = useState<FollowUp[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await followUpsApi.upcoming({ per_page: 20 });
      setItems(data.items);
      setTotal(data.total);
    } catch {
      /* handled */
    } finally {
      setLoading(false);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "scheduled":
        return "bg-blue-100 text-blue-700";
      case "completed":
        return "bg-green-100 text-green-700";
      case "overdue":
        return "bg-red-100 text-red-700";
      case "cancelled":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Follow-Ups</h2>
        <span className="text-sm text-gray-500">{total} upcoming</span>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="space-y-3">
          {items.map((fu) => (
            <div
              key={fu.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900 capitalize">
                    {fu.follow_up_type.replace("_", " ")}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Scheduled:{" "}
                    {new Date(fu.scheduled_date).toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <span
                  className={`inline-flex px-2.5 py-1 text-xs font-medium rounded-full ${statusColor(fu.status)}`}
                >
                  {fu.status}
                </span>
              </div>
              {fu.notes && (
                <p className="text-sm text-gray-600 mt-2">{fu.notes}</p>
              )}
            </div>
          ))}
          {items.length === 0 && (
            <p className="text-center text-gray-500 py-8">
              No upcoming follow-ups
            </p>
          )}
        </div>
      )}
    </div>
  );
}

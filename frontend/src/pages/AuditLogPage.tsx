import { useState, useEffect } from "react";
import api from "../api/client";
import { useAuth } from "../contexts/AuthContext";

interface AuditEntry {
  id: string; user_id: string; action: string; entity_type: string | null;
  entity_id: string | null; description: string | null; ip_address: string | null; created_at: string;
}

export default function AuditLogPage() {
  const { user } = useAuth();
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState("");

  const loadLog = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/admin/audit-log", {
        params: { action_filter: actionFilter || undefined, per_page: 50 },
      });
      setEntries(data.items);
      setTotal(data.total);
    } catch { /* interceptor */ }
    setLoading(false);
  };

  useEffect(() => { loadLog(); }, [actionFilter]);

  if (user?.role !== "admin") {
    return <div className="p-8 text-center text-gray-500">Admin access required.</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Audit Log</h2>
        <span className="text-sm text-gray-500">{total} entries</span>
      </div>

      <input type="text" placeholder="Filter by action..." value={actionFilter}
        onChange={(e) => setActionFilter(e.target.value)}
        className="w-full px-4 py-2 mb-4 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />

      {loading ? <p className="text-gray-500">Loading...</p> : (
        <div className="space-y-2">
          {entries.map((e) => (
            <div key={e.id} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{e.action}</p>
                  {e.description && <p className="text-sm text-gray-600 mt-0.5">{e.description}</p>}
                  <div className="flex gap-3 mt-1 text-xs text-gray-400">
                    {e.entity_type && <span>{e.entity_type}</span>}
                    {e.ip_address && <span>IP: {e.ip_address}</span>}
                  </div>
                </div>
                <span className="text-xs text-gray-400 whitespace-nowrap">
                  {new Date(e.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
          {entries.length === 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
              No audit log entries.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

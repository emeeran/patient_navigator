import { useState, useEffect } from "react";
import { hospitalsApi } from "../api";
import type { Hospital } from "../types";

export default function HospitalsPage() {
  const [items, setItems] = useState<Hospital[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
  }, [search]);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await hospitalsApi.list({
        search: search || undefined,
        per_page: 20,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch {
      /* handled */
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Hospital Directory</h2>
        <span className="text-sm text-gray-500">{total} hospitals</span>
      </div>

      <input
        type="text"
        placeholder="Search hospitals..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2 mb-4 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
      />

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          {items.map((h) => (
            <div
              key={h.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
            >
              <h3 className="font-semibold text-gray-900">{h.name}</h3>
              <p className="text-sm text-gray-500 mt-1">
                {h.city}
                {h.state ? `, ${h.state}` : ""}
              </p>
              {h.specialties && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {h.specialties.split(",").map((s) => (
                    <span
                      key={s}
                      className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full"
                    >
                      {s.trim()}
                    </span>
                  ))}
                </div>
              )}
              <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
                {h.phone && <span>{h.phone}</span>}
                {h.has_financial_assistance && (
                  <span className="text-green-600 font-medium">
                    Financial aid
                  </span>
                )}
                {h.rating && <span>Rating: {h.rating}/5</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import { useState, useEffect } from "react";
import { fundingApi } from "../api";
import type { FundingProgram } from "../types";

export default function FundingPage() {
  const [items, setItems] = useState<FundingProgram[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
  }, [search]);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await fundingApi.list({
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
        <h2 className="text-2xl font-bold text-gray-900">Funding Programs</h2>
        <span className="text-sm text-gray-500">{total} programs</span>
      </div>

      <input
        type="text"
        placeholder="Search funding programs..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2 mb-4 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
      />

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="space-y-3">
          {items.map((f) => (
            <div
              key={f.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{f.name}</h3>
                  {f.provider && (
                    <p className="text-sm text-gray-500">{f.provider}</p>
                  )}
                </div>
                <div className="text-right">
                  {f.max_amount && (
                    <p className="text-sm font-medium text-green-600">
                      Up to ${f.max_amount.toLocaleString()}
                    </p>
                  )}
                  {f.program_type && (
                    <span className="text-xs text-gray-500 capitalize">
                      {f.program_type.replace("_", " ")}
                    </span>
                  )}
                </div>
              </div>
              {f.description && (
                <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                  {f.description}
                </p>
              )}
              {f.eligibility_criteria && (
                <p className="text-xs text-gray-500 mt-2">
                  <strong>Eligibility:</strong> {f.eligibility_criteria}
                </p>
              )}
              <div className="flex gap-3 mt-3">
                {f.application_url && (
                  <a
                    href={f.application_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline"
                  >
                    Apply →
                  </a>
                )}
                {f.contact_email && (
                  <a
                    href={`mailto:${f.contact_email}`}
                    className="text-xs text-gray-500 hover:underline"
                  >
                    Contact
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

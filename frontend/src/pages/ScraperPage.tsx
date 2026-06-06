import { useState } from "react";
import { adminApi } from "../api/index";
import { useAuth } from "../contexts/AuthContext";
import type { ScrapedHospital, ScrapedNgo, ScrapedDoctor, BulkImportResponse } from "../types";

type EntityType = "hospitals" | "ngos" | "doctors";

export default function ScraperPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  // Search inputs
  const [city, setCity] = useState("");
  const [stateInput, setStateInput] = useState("");
  const [entityType, setEntityType] = useState<EntityType>("hospitals");

  // Results state
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState<ScrapedHospital[] | ScrapedNgo[] | ScrapedDoctor[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");
  const [importResult, setImportResult] = useState<BulkImportResponse | null>(null);
  const [importing, setImporting] = useState(false);

  const handleScrape = async () => {
    if (!city.trim()) return;
    setLoading(true);
    setError("");
    setRecords([]);
    setSelectedIndices(new Set());
    setImportResult(null);

    try {
      const { data } = await adminApi.scrapeCity(
        city.trim(),
        entityType,
        stateInput.trim() || undefined,
      );
      setRecords(data.records);
      setSelectedIndices(new Set(data.records.map((_, i: number) => i)));
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to scrape. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    const toImport = records.filter((_, i) => selectedIndices.has(i));
    if (toImport.length === 0) return;

    setImporting(true);
    setError("");
    try {
      const { data } =
        entityType === "hospitals"
          ? await adminApi.importHospitals(toImport as ScrapedHospital[])
          : entityType === "doctors"
          ? await adminApi.importDoctors(toImport as ScrapedDoctor[])
          : await adminApi.importNgos(toImport as ScrapedNgo[]);
      setImportResult(data);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to import.");
    } finally {
      setImporting(false);
    }
  };

  const toggleRecord = (idx: number) => {
    setSelectedIndices((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  const selectAll = () => setSelectedIndices(new Set(records.map((_, i) => i)));
  const deselectAll = () => setSelectedIndices(new Set());

  if (!isAdmin) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg">Access Denied</p>
        <p className="text-sm mt-1">Only administrators can access the Data Scraper.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Data Scraper</h2>
        <p className="text-sm text-gray-500 mt-1">
          Scrape hospitals or NGOs by city name from public web sources, then import to your database.
        </p>
      </div>

      {/* Search Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Search</h3>

        {/* Entity Type Toggle */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Entity Type</label>
          <div className="flex rounded-lg border border-gray-300 overflow-hidden w-fit">
            <button
              onClick={() => { setEntityType("hospitals"); setRecords([]); setImportResult(null); }}
              className={`px-5 py-2 text-sm font-medium transition-colors ${
                entityType === "hospitals"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              🏥 Hospitals
            </button>
            <button
              onClick={() => { setEntityType("doctors"); setRecords([]); setImportResult(null); }}
              className={`px-5 py-2 text-sm font-medium transition-colors ${
                entityType === "doctors"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              👨‍⚕️ Doctors
            </button>
            <button
              onClick={() => { setEntityType("ngos"); setRecords([]); setImportResult(null); }}
              className={`px-5 py-2 text-sm font-medium transition-colors ${
                entityType === "ngos"
                  ? "bg-blue-600 text-white"
                  : "bg-white text-gray-600 hover:bg-gray-50"
              }`}
            >
              🤝 NGOs / Funding
            </button>
          </div>
        </div>

        {/* City + State inputs */}
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              City <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="e.g. Chennai, Coimbatore, Mumbai"
              onKeyDown={(e) => e.key === "Enter" && handleScrape()}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="w-64">
            <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
            <input
              type="text"
              value={stateInput}
              onChange={(e) => setStateInput(e.target.value)}
              placeholder="e.g. Tamil Nadu"
              onKeyDown={(e) => e.key === "Enter" && handleScrape()}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg mb-3">{error}</div>
        )}

        <button
          onClick={handleScrape}
          disabled={!city.trim() || loading}
          className="px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Scraping...
            </span>
          ) : (
            "🔍 Scrape"
          )}
        </button>
      </div>

      {/* Results */}
      {records.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-semibold text-gray-900">
                Results for {city.trim().replace(/\b\w/g, (c) => c.toUpperCase())}
              </h3>
              <span className="px-2.5 py-0.5 bg-blue-50 text-blue-700 text-xs font-medium rounded-full">
                {records.length} found
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={selectAll} className="px-3 py-1.5 text-xs text-blue-600 hover:bg-blue-50 rounded-lg">
                Select All
              </button>
              <button onClick={deselectAll} className="px-3 py-1.5 text-xs text-gray-500 hover:bg-gray-100 rounded-lg">
                Deselect All
              </button>
              <button
                onClick={handleImport}
                disabled={importing || selectedIndices.size === 0}
                className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {importing ? "Importing..." : `Import Selected (${selectedIndices.size})`}
              </button>
            </div>
          </div>

          <p className="text-sm text-gray-500 mb-3">
            {selectedIndices.size} of {records.length} selected
          </p>

          <div className="overflow-auto max-h-96 border border-gray-200 rounded-lg">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 sticky top-0 z-10">
                <tr>
                  <th className="px-3 py-2.5 w-10"></th>
                  {entityType === "hospitals" ? (
                    <>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Name</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">City</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Phone</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Email</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Specialties</th>
                    </>
                  ) : entityType === "doctors" ? (
                    <>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Name</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Specialty</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Phone</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Hospital / Clinic</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Type</th>
                    </>
                  ) : (
                    <>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Name</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Type</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Email</th>
                      <th className="text-left px-3 py-2.5 font-medium text-gray-600">Phone</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {entityType === "hospitals"
                  ? (records as ScrapedHospital[]).map((r, i) => (
                      <tr
                        key={i}
                        className={`hover:bg-gray-50 cursor-pointer ${
                          selectedIndices.has(i) ? "bg-blue-50" : ""
                        }`}
                        onClick={() => toggleRecord(i)}
                      >
                        <td className="px-3 py-2.5">
                          <input
                            type="checkbox"
                            checked={selectedIndices.has(i)}
                            onChange={() => toggleRecord(i)}
                            className="rounded border-gray-300"
                            onClick={(e) => e.stopPropagation()}
                          />
                        </td>
                        <td className="px-3 py-2.5 text-gray-900 font-medium">{r.name}</td>
                        <td className="px-3 py-2.5 text-gray-600">{r.city}</td>
                        <td className="px-3 py-2.5 text-gray-600">{r.phone || "—"}</td>
                        <td className="px-3 py-2.5 text-gray-600 truncate max-w-[180px]">{r.email || "—"}</td>
                        <td className="px-3 py-2.5 text-gray-500 text-xs truncate max-w-[200px]">
                          {r.specialties || "—"}
                        </td>
                      </tr>
                    ))
                  : entityType === "doctors"
                  ? (records as ScrapedDoctor[]).map((r, i) => (
                      <tr
                        key={i}
                        className={`hover:bg-gray-50 cursor-pointer ${
                          selectedIndices.has(i) ? "bg-blue-50" : ""
                        }`}
                        onClick={() => toggleRecord(i)}
                      >
                        <td className="px-3 py-2.5">
                          <input
                            type="checkbox"
                            checked={selectedIndices.has(i)}
                            onChange={() => toggleRecord(i)}
                            className="rounded border-gray-300"
                            onClick={(e) => e.stopPropagation()}
                          />
                        </td>
                        <td className="px-3 py-2.5 text-gray-900 font-medium">{r.name}</td>
                        <td className="px-3 py-2.5 text-gray-600 truncate max-w-[180px]">{r.specialty || "—"}</td>
                        <td className="px-3 py-2.5 text-gray-600">{r.phone || "—"}</td>
                        <td className="px-3 py-2.5 text-gray-500 text-xs truncate max-w-[180px]">
                          {r.hospital_name || "—"}
                        </td>
                        <td className="px-3 py-2.5">
                          <span className={`px-2 py-0.5 text-xs rounded-full ${
                            r.practice_type === "government"
                              ? "bg-green-100 text-green-700"
                              : "bg-blue-100 text-blue-700"
                          }`}>
                            {r.practice_type || "private"}
                          </span>
                        </td>
                      </tr>
                    ))
                  : (records as ScrapedNgo[]).map((r, i) => (
                      <tr
                        key={i}
                        className={`hover:bg-gray-50 cursor-pointer ${
                          selectedIndices.has(i) ? "bg-blue-50" : ""
                        }`}
                        onClick={() => toggleRecord(i)}
                      >
                        <td className="px-3 py-2.5">
                          <input
                            type="checkbox"
                            checked={selectedIndices.has(i)}
                            onChange={() => toggleRecord(i)}
                            className="rounded border-gray-300"
                            onClick={(e) => e.stopPropagation()}
                          />
                        </td>
                        <td className="px-3 py-2.5 text-gray-900 font-medium">{r.name}</td>
                        <td className="px-3 py-2.5 text-gray-600 capitalize">
                          {(r.program_type || "ngo").replace("_", " ")}
                        </td>
                        <td className="px-3 py-2.5 text-gray-600 truncate max-w-[180px]">
                          {r.contact_email || "—"}
                        </td>
                        <td className="px-3 py-2.5 text-gray-600">{r.contact_phone || "—"}</td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>

          {/* Import Result */}
          {importResult && (
            <div
              className={`p-4 rounded-lg mt-4 ${
                importResult.errors.length > 0
                  ? "bg-amber-50 border border-amber-200"
                  : "bg-green-50 border border-green-200"
              }`}
            >
              <p className="font-medium text-sm">
                <span className={importResult.errors.length > 0 ? "text-amber-800" : "text-green-800"}>
                  ✅ Imported: {importResult.imported} &nbsp;|&nbsp; ⏭️ Skipped (duplicates): {importResult.skipped}
                </span>
              </p>
              {importResult.errors.length > 0 && (
                <ul className="mt-2 text-xs text-amber-700 list-disc list-inside">
                  {importResult.errors.slice(0, 5).map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                  {importResult.errors.length > 5 && (
                    <li>...and {importResult.errors.length - 5} more errors</li>
                  )}
                </ul>
              )}
            </div>
          )}
        </div>
      )}

      {/* Empty state after scrape */}
      {!loading && records.length === 0 && error === "" && city && (
        <div className="text-center py-8 text-gray-400 text-sm">
          Enter a city name and click Scrape to find {entityType === "ngos" ? "NGOs" : entityType}.
        </div>
      )}
    </div>
  );
}

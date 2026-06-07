import { useState, useEffect, useCallback, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { hospitalsApi, adminApi } from "../api";
import type { Hospital } from "../types";
import Modal from "../components/Modal";
import MapView from "../components/MapView";
import type { MapMarker } from "../components/MapView";
import Pagination from "../components/Pagination";
import { useAuth } from "../contexts/AuthContext";

const emptyForm = {
  name: "",
  city: "",
  state: "",
  address: "",
  phone: "",
  email: "",
  website: "",
  specialties: "",
  has_financial_assistance: false,
  rating: "",
};

export default function HospitalsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Hospital[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editingItem, setEditingItem] = useState<Hospital | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [confirmArchive, setConfirmArchive] = useState<string | null>(null);
  const [dedupMsg, setDedupMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [deduping, setDeduping] = useState(false);
  const [showDedupConfirm, setShowDedupConfirm] = useState(false);
  const [viewMode, setViewMode] = useState<"table" | "cards" | "map">("table");
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await hospitalsApi.list({ search: search || undefined, per_page: 20, page });
      setItems(data.items);
      setTotal(data.total);
    } catch { /* handled */ } finally { setLoading(false); }
  }, [search, page]);

  useEffect(() => { setPage(1); }, [search]);
  useEffect(() => { load(); }, [search, page]);

  // Auto-dismiss dedup message after 5s
  useEffect(() => {
    if (!dedupMsg) return;
    const t = setTimeout(() => setDedupMsg(null), 5000);
    return () => clearTimeout(t);
  }, [dedupMsg]);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      if (editingItem) {
        await hospitalsApi.update(editingItem.id, {
          name: form.name, city: form.city,
          state: form.state || undefined, address: form.address || undefined,
          phone: form.phone || undefined, email: form.email || undefined,
          website: form.website || undefined, specialties: form.specialties || undefined,
          has_financial_assistance: form.has_financial_assistance,
          rating: form.rating ? Number(form.rating) : undefined,
        });
        setEditingItem(null);
      } else {
        await hospitalsApi.create({
          name: form.name, city: form.city,
          state: form.state || undefined, address: form.address || undefined,
          phone: form.phone || undefined, email: form.email || undefined,
          website: form.website || undefined, specialties: form.specialties || undefined,
          has_financial_assistance: form.has_financial_assistance,
          rating: form.rating ? Number(form.rating) : undefined,
        });
        setShowAdd(false);
      }
      setForm(emptyForm);
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(msg || "Failed to save hospital");
    } finally { setSaving(false); }
  };

  const openEdit = (e: React.MouseEvent, h: Hospital) => {
    e.stopPropagation();
    setEditingItem(h);
    setForm({
      name: h.name, city: h.city, state: h.state || "",
      address: h.address || "", phone: h.phone || "",
      email: h.email || "", website: h.website || "",
      specialties: h.specialties || "",
      has_financial_assistance: h.has_financial_assistance,
      rating: h.rating?.toString() || "",
    });
    setFormError("");
  };

  const handleArchive = async (id: string) => {
    try {
      await hospitalsApi.archive(id);
      setConfirmArchive(null);
      load();
    } catch { /* handled */ }
  };

  const handleDedup = async () => {
    setDeduping(true);
    setDedupMsg(null);
    try {
      const { data } = await adminApi.dedupHospitals();
      if (data.removed === 0) {
        setDedupMsg({ type: "success", text: "No duplicates found. Directory is clean." });
      } else {
        setDedupMsg({ type: "success", text: `Removed ${data.removed} duplicate${data.removed !== 1 ? "s" : ""}. ${data.kept} unique hospitals remain.` });
      }
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setDedupMsg({ type: "error", text: msg || "Dedup failed." });
    } finally { setDeduping(false); }
  };

  const modalTitle = editingItem ? `Edit: ${editingItem.name}` : "Add Hospital";
  const showModal = showAdd || editingItem !== null;
  const closeModal = () => { setShowAdd(false); setEditingItem(null); setForm(emptyForm); };
  const colCount = isAdmin ? 8 : 7;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Hospital Directory</h2>
        <div className="flex items-center gap-3">
          {/* View toggle */}
          <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
            <button onClick={() => setViewMode("table")}
              className={`px-3 py-1.5 text-xs font-medium ${viewMode === "table" ? "bg-purple-50 text-purple-700" : "text-gray-500 hover:bg-gray-50"}`}>
              Table
            </button>
            <button onClick={() => setViewMode("cards")}
              className={`px-3 py-1.5 text-xs font-medium ${viewMode === "cards" ? "bg-purple-50 text-purple-700" : "text-gray-500 hover:bg-gray-50"}`}>
              Cards
            </button>
            <button onClick={() => setViewMode("map")}
              className={`px-3 py-1.5 text-xs font-medium ${viewMode === "map" ? "bg-purple-50 text-purple-700" : "text-gray-500 hover:bg-gray-50"}`}>
              Map
            </button>
          </div>
          <span className="text-sm text-gray-500">{total} hospitals</span>
          {isAdmin && (
            <button onClick={() => setShowDedupConfirm(true)} disabled={deduping}
              className="px-4 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-colors inline-flex items-center gap-1.5">
              {deduping && <span className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />}
              {deduping ? "Deduplicating…" : "🔧 Deduplicate"}
            </button>
          )}
          {isAdmin && (
            <button onClick={() => { setFormError(""); setShowAdd(true); }}
              className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors">
              + Add Hospital
            </button>
          )}
        </div>
      </div>

      {dedupMsg && (
        <div className={`p-3 text-sm rounded-lg mb-4 flex items-center justify-between ${dedupMsg.type === "success" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          <span>{dedupMsg.text}</span>
          <button onClick={() => setDedupMsg(null)} className="ml-3 opacity-60 hover:opacity-100 text-lg leading-none">&times;</button>
        </div>
      )}

      <input type="text" placeholder="Search hospitals…" value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2 mb-4 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />

      {loading ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">City</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">State</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Phone</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Specialties</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Rating</th>
                {isAdmin && <th className="px-4 py-3"></th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: colCount }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-gray-100 rounded animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : viewMode === "table" ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 min-w-[180px]">Name</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 min-w-[100px]">City</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">State</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 min-w-[120px]">Phone</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 min-w-[140px]">Specialties</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Rating</th>
                  {isAdmin && <th className="px-4 py-3 w-24"></th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((h) => (
                  <tr key={h.id} className="hover:bg-blue-50/50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/hospitals/${h.id}`)}>
                    <td className="px-4 py-3 font-medium text-gray-900">{h.name}</td>
                    <td className="px-4 py-3 text-gray-600">{h.city}</td>
                    <td className="px-4 py-3 text-gray-600">{h.state || "—"}</td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">{h.phone || "—"}</td>
                    <td className="px-4 py-3">
                      {h.specialties ? (
                        <div className="flex flex-wrap gap-1">
                          {h.specialties.split(",").map((s) => (
                            <span key={s} className="px-1.5 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">{s.trim()}</span>
                          ))}
                        </div>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-3">
                      {h.has_financial_assistance ? (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">Govt</span>
                      ) : (
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full font-medium">Pvt</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{h.rating ? `${h.rating}/5` : "—"}</td>
                    {isAdmin && (
                      <td className="px-4 py-3 space-x-2" onClick={(e) => e.stopPropagation()}>
                        <button onClick={(e) => openEdit(e, h)} className="text-xs text-blue-600 hover:underline">Edit</button>
                        <button onClick={() => setConfirmArchive(h.id)} className="text-xs text-red-600 hover:underline">Delete</button>
                      </td>
                    )}
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={colCount} className="text-center py-12">
                      <p className="text-gray-400 text-sm">No hospitals found.</p>
                      {search && <p className="text-gray-400 text-xs mt-1">Try a different search term.</p>}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* Card view */}
      {!loading && items.length > 0 && viewMode === "cards" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((h) => (
            <div key={h.id}
              className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md cursor-pointer transition-shadow"
              onClick={() => navigate(`/hospitals/${h.id}`)}>
              <div className="flex items-start justify-between mb-2">
                <h3 className="font-semibold text-gray-900">{h.name}</h3>
                {h.has_financial_assistance ? (
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium shrink-0">Govt</span>
                ) : (
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full font-medium shrink-0">Pvt</span>
                )}
              </div>
              <p className="text-sm text-gray-500 mb-2">{h.city}{h.state ? `, ${h.state}` : ""}</p>
              {h.specialties && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {h.specialties.split(",").map((s) => (
                    <span key={s} className="px-1.5 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">{s.trim()}</span>
                  ))}
                </div>
              )}
              <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                <span>{h.phone || ""}</span>
                {h.rating != null && <span className="text-amber-600 font-medium">★ {h.rating}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Map view */}
      {!loading && items.length > 0 && viewMode === "map" && (() => {
        const markers: MapMarker[] = items
          .filter((h) => h.latitude != null && h.longitude != null)
          .map((h) => ({
            id: h.id, lat: h.latitude!, lng: h.longitude!,
            label: h.name, popup: `${h.city}${h.specialties ? ` — ${h.specialties.split(",").slice(0, 3).join(", ")}` : ""}`,
          }));
        return markers.length > 0 ? (
          <div>
            <p className="text-xs text-gray-500 mb-2">{markers.length} of {items.length} hospitals have location data</p>
            <MapView markers={markers} onMarkerClick={(id) => navigate(`/hospitals/${id}`)} />
          </div>
        ) : (
          <p className="text-center text-gray-400 py-12">No hospitals with location data available.</p>
        );
      })()}

      {!loading && total > 0 && viewMode !== "map" && (
        <Pagination page={page} total={total} perPage={20} onChange={setPage} />
      )}

      {/* Add/Edit Modal */}
      <Modal open={showModal} onClose={closeModal} title={modalTitle}>
        {formError && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{formError}</div>}
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input type="text" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
              <input type="text" required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <input type="text" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rating</label>
              <input type="number" min={0} max={5} step={0.1} value={form.rating}
                onChange={(e) => setForm({ ...form, rating: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input type="text" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
            <input type="url" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" placeholder="https://…" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Specialties</label>
            <input type="text" value={form.specialties} onChange={(e) => setForm({ ...form, specialties: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" placeholder="Oncology, Cardiology, …" />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="hosp_fin" checked={form.has_financial_assistance}
              onChange={(e) => setForm({ ...form, has_financial_assistance: e.target.checked })} className="rounded border-gray-300" />
            <label htmlFor="hosp_fin" className="text-sm text-gray-700">Offers financial assistance</label>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button type="submit" disabled={saving}
              className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50">
              {saving ? "Saving…" : editingItem ? "Save Changes" : "Add Hospital"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Archive Confirmation */}
      {confirmArchive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmArchive(null)} />
          <div className="relative bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Delete Hospital?</h3>
            <p className="text-sm text-gray-600 mb-4">This hospital will be removed from the directory. You can restore it later.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmArchive(null)} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
              <button onClick={() => handleArchive(confirmArchive)}
                className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700">Delete</button>
            </div>
          </div>
        </div>
      )}

      {/* Dedup Confirmation */}
      {showDedupConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowDedupConfirm(false)} />
          <div className="relative bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Deduplicate Hospitals?</h3>
            <p className="text-sm text-gray-600 mb-4">
              This will find hospitals with the same <span className="font-medium text-gray-800">name + city</span> and keep only the most complete record. Duplicates will be soft-deleted.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowDedupConfirm(false)} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
              <button onClick={() => { setShowDedupConfirm(false); handleDedup(); }}
                className="px-4 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600">
                Run Dedup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

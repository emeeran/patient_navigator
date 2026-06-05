import { useState, useEffect, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { hospitalsApi } from "../api";
import type { Hospital } from "../types";
import Modal from "../components/Modal";
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
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editingItem, setEditingItem] = useState<Hospital | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [confirmArchive, setConfirmArchive] = useState<string | null>(null);
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  useEffect(() => { load(); }, [search]);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await hospitalsApi.list({ search: search || undefined, per_page: 20 });
      setItems(data.items);
      setTotal(data.total);
    } catch { /* handled */ } finally { setLoading(false); }
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      if (editingItem) {
        await hospitalsApi.update(editingItem.id, {
          name: form.name,
          city: form.city,
          state: form.state || undefined,
          address: form.address || undefined,
          phone: form.phone || undefined,
          email: form.email || undefined,
          website: form.website || undefined,
          specialties: form.specialties || undefined,
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

  const modalTitle = editingItem ? `Edit: ${editingItem.name}` : "Add Hospital";
  const showModal = showAdd || editingItem !== null;
  const closeModal = () => { setShowAdd(false); setEditingItem(null); setForm(emptyForm); };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Hospital Directory</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{total} hospitals</span>
          {isAdmin && (
            <button onClick={() => { setFormError(""); setShowAdd(true); }}
              className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors">
              + Add Hospital
            </button>
          )}
        </div>
      </div>

      <input type="text" placeholder="Search hospitals..." value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2 mb-4 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />

      {loading ? <p className="text-gray-500">Loading...</p> : (
        <div className="grid grid-cols-2 gap-4">
          {items.map((h) => (
            <div key={h.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow cursor-pointer relative group"
              onClick={() => navigate(`/hospitals/${h.id}`)}>
              {isAdmin && (
                <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => e.stopPropagation()}>
                  <button onClick={(e) => openEdit(e, h)}
                    className="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded">Edit</button>
                  <button onClick={() => setConfirmArchive(h.id)}
                    className="px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded">Delete</button>
                </div>
              )}
              <h3 className="font-semibold text-gray-900">{h.name}</h3>
              <p className="text-sm text-gray-500 mt-1">{h.city}{h.state ? `, ${h.state}` : ""}</p>
              {h.specialties && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {h.specialties.split(",").map((s) => (
                    <span key={s} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">{s.trim()}</span>
                  ))}
                </div>
              )}
              <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
                {h.phone && <span>{h.phone}</span>}
                {h.has_financial_assistance && <span className="text-green-600 font-medium">Financial aid</span>}
                {h.rating && <span>Rating: {h.rating}/5</span>}
              </div>
            </div>
          ))}
          {items.length === 0 && (
            <p className="col-span-2 text-center text-gray-500 py-8">No hospitals found.</p>
          )}
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal open={showModal} onClose={closeModal} title={modalTitle}>
        {formError && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{formError}</div>}
        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input type="text" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
              <input type="text" required value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <input type="text" value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rating</label>
              <input type="number" min={0} max={5} step={0.1} value={form.rating}
                onChange={(e) => setForm({ ...form, rating: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input type="text" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input type="tel" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
            <input type="url" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" placeholder="https://..." />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Specialties</label>
            <input type="text" value={form.specialties} onChange={(e) => setForm({ ...form, specialties: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" placeholder="Oncology, Cardiology, ..." />
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
              {saving ? "Saving..." : editingItem ? "Save Changes" : "Add Hospital"}
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
    </div>
  );
}

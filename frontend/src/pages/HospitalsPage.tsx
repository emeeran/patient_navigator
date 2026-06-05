import { useState, useEffect, type FormEvent } from "react";
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
  const [items, setItems] = useState<Hospital[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const { user } = useAuth();

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

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      await hospitalsApi.create({
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
      setShowAdd(false);
      setForm(emptyForm);
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(msg || "Failed to create hospital");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Hospital Directory</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{total} hospitals</span>
          <button
            onClick={() => { setFormError(""); setShowAdd(true); }}
            className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors"
            style={{ display: user?.role === "admin" ? undefined : "none" }}
          >
            + Add Hospital
          </button>
        </div>
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
                  <span className="text-green-600 font-medium">Financial aid</span>
                )}
                {h.rating && <span>Rating: {h.rating}/5</span>}
              </div>
            </div>
          ))}
          {items.length === 0 && (
            <p className="col-span-2 text-center text-gray-500 py-8">
              No hospitals found. Click "Add Hospital" to create one.
            </p>
          )}
        </div>
      )}

      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Add Hospital">
        {formError && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{formError}</div>
        )}
        <form onSubmit={handleAdd} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
              <input
                type="text"
                required
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <input
                type="text"
                value={form.state}
                onChange={(e) => setForm({ ...form, state: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Rating</label>
              <input
                type="number"
                min={0}
                max={5}
                step={0.1}
                value={form.rating}
                onChange={(e) => setForm({ ...form, rating: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input
              type="text"
              value={form.address}
              onChange={(e) => setForm({ ...form, address: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
            <input
              type="url"
              value={form.website}
              onChange={(e) => setForm({ ...form, website: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              placeholder="https://..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Specialties</label>
            <input
              type="text"
              value={form.specialties}
              onChange={(e) => setForm({ ...form, specialties: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              placeholder="Oncology, Cardiology, ..."
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="has_financial_assistance"
              checked={form.has_financial_assistance}
              onChange={(e) => setForm({ ...form, has_financial_assistance: e.target.checked })}
              className="rounded border-gray-300"
            />
            <label htmlFor="has_financial_assistance" className="text-sm text-gray-700">
              Offers financial assistance
            </label>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => setShowAdd(false)}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
            >
              {saving ? "Saving..." : "Add Hospital"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

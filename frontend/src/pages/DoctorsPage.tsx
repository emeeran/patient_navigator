import { useState, useEffect, useCallback, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { doctorsApi } from "../api";
import type { Doctor } from "../types";
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
  specialty: "",
  qualification: "",
  registration_number: "",
  medical_council: "",
  hospital_name: "",
  practice_type: "",
};

export default function DoctorsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<Doctor[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [filterCity, setFilterCity] = useState("");
  const [filterSpecialty, setFilterSpecialty] = useState("");
  const [filterType, setFilterType] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editingItem, setEditingItem] = useState<Doctor | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [confirmArchive, setConfirmArchive] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"table" | "cards" | "map">("table");
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await doctorsApi.list({
        search: search || undefined,
        city: filterCity || undefined,
        specialty: filterSpecialty || undefined,
        practice_type: filterType || undefined,
        per_page: 20,
        page,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch { /* handled */ } finally { setLoading(false); }
  }, [search, filterCity, filterSpecialty, filterType, page]);

  useEffect(() => { setPage(1); }, [search, filterCity, filterSpecialty, filterType]);
  useEffect(() => { load(); }, [search, filterCity, filterSpecialty, filterType, page]);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      const payload = {
        ...form,
        practice_type: form.practice_type || undefined,
      };
      if (editingItem) {
        await doctorsApi.update(editingItem.id, payload);
      } else {
        await doctorsApi.create(payload);
      }
      setShowAdd(false);
      setEditingItem(null);
      setForm(emptyForm);
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(msg || "Failed to save doctor.");
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async (id: string) => {
    try { await doctorsApi.archive(id); load(); } catch { /* handled */ }
    setConfirmArchive(null);
  };

  const openEdit = (d: Doctor) => {
    setEditingItem(d);
    setForm({
      name: d.name, city: d.city, state: d.state || "", address: d.address || "",
      phone: d.phone || "", email: d.email || "", website: d.website || "",
      specialty: d.specialty || "", qualification: d.qualification || "",
      registration_number: d.registration_number || "", medical_council: d.medical_council || "",
      hospital_name: d.hospital_name || "", practice_type: d.practice_type || "",
    });
    setFormError("");
    setShowAdd(true);
  };

  const pages = Math.ceil(total / 20);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Doctors</h2>
          <p className="text-sm text-gray-500 mt-1">{total} doctor{total !== 1 ? "s" : ""} found</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
            <button onClick={() => setViewMode("table")}
              className={`px-3 py-1.5 text-xs font-medium ${viewMode === "table" ? "bg-teal-50 text-teal-700" : "text-gray-500 hover:bg-gray-50"}`}>
              Table
            </button>
            <button onClick={() => setViewMode("map")}
              className={`px-3 py-1.5 text-xs font-medium ${viewMode === "map" ? "bg-teal-50 text-teal-700" : "text-gray-500 hover:bg-gray-50"}`}>
              Map
            </button>
          </div>
          {isAdmin && (
          <button onClick={async () => {
            try {
              const { data } = await doctorsApi.list({ per_page: 1000 });
              const headers = ["Name", "City", "Specialty", "Qualification", "Practice Type", "Hospital", "Phone", "Email"];
              const rows = data.items.map((d) => [d.name, d.city, d.specialty, d.qualification, d.practice_type, d.hospital_name, d.phone, d.email]);
              const csv = [headers.join(","), ...rows.map((r) => r.map((v) => `"${(v ?? "").replace(/"/g, '""')}"`).join(","))].join("\n");
              const a = document.createElement("a");
              a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
              a.download = "doctors.csv"; a.click();
            } catch { /* handled */ }
          }}
            className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200">
            Export CSV
          </button>
        )}
          {isAdmin && (
          <button onClick={() => { setForm(emptyForm); setFormError(""); setEditingItem(null); setShowAdd(true); }}
            className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700">
            Add Doctor
          </button>
        )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input value={search} onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name..."
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm flex-1 min-w-[200px]" />
        <input value={filterCity} onChange={(e) => setFilterCity(e.target.value)}
          placeholder="City..."
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm w-36" />
        <input value={filterSpecialty} onChange={(e) => setFilterSpecialty(e.target.value)}
          placeholder="Specialty..."
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm w-40" />
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm">
          <option value="">All Types</option>
          <option value="government">Government</option>
          <option value="private">Private</option>
        </select>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-14 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="text-center text-gray-500 py-12">No doctors found.</p>
      ) : viewMode === "map" ? (() => {
        const markers: MapMarker[] = items
          .filter((d) => d.latitude != null && d.longitude != null)
          .map((d) => ({
            id: d.id, lat: d.latitude!, lng: d.longitude!,
            label: d.name, popup: `${d.specialty || "Doctor"}${d.hospital_name ? ` — ${d.hospital_name}` : ""}`,
          }));
        return markers.length > 0 ? (
          <div>
            <p className="text-xs text-gray-500 mb-2">{markers.length} of {items.length} doctors have location data</p>
            <MapView markers={markers} onMarkerClick={(id) => navigate(`/doctors/${id}`)} />
          </div>
        ) : (
          <p className="text-center text-gray-400 py-12">No doctors with location data available.</p>
        );
      })() : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">City</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Specialty</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Hospital</th>
                {isAdmin && <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map((d) => (
                <tr key={d.id} className="hover:bg-gray-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/doctors/${d.id}`)}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{d.name}</div>
                    {d.qualification && <div className="text-xs text-gray-500">{d.qualification}</div>}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{d.city}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{d.specialty || "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                      d.practice_type === "government"
                        ? "bg-green-100 text-green-700"
                        : d.practice_type === "private"
                          ? "bg-blue-100 text-blue-700"
                          : "bg-gray-100 text-gray-500"
                    }`}>
                      {d.practice_type === "government" ? "Govt" : d.practice_type === "private" ? "Private" : "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{d.hospital_name || "—"}</td>
                  {isAdmin && (
                    <td className="px-4 py-3 text-right space-x-2" onClick={(e) => e.stopPropagation()}>
                      <button onClick={() => openEdit(d)}
                        className="px-3 py-1 text-xs font-medium text-teal-700 bg-teal-50 rounded hover:bg-teal-100">
                        Edit
                      </button>
                      <button onClick={() => setConfirmArchive(d.id)}
                        className="px-3 py-1 text-xs font-medium text-red-700 bg-red-50 rounded hover:bg-red-100">
                        Delete
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pages > 1 && viewMode !== "map" && (
        <Pagination page={page} total={total} perPage={20} onChange={setPage} />
      )}

      {/* Add/Edit Modal */}
      <Modal open={showAdd} onClose={() => { setShowAdd(false); setEditingItem(null); }}
        title={editingItem ? "Edit Doctor" : "Add Doctor"}>
        <form onSubmit={handleSave} className="space-y-4">
          {formError && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">{formError}</p>}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">City *</label>
              <input value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Specialty</label>
              <input value={form.specialty} onChange={(e) => setForm({ ...form, specialty: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Practice Type</label>
              <select value={form.practice_type} onChange={(e) => setForm({ ...form, practice_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="">—</option>
                <option value="government">Government</option>
                <option value="private">Private</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
              <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Hospital/Clinic</label>
              <input value={form.hospital_name} onChange={(e) => setForm({ ...form, hospital_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Qualification</label>
              <input value={form.qualification} onChange={(e) => setForm({ ...form, qualification: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
              <input value={form.state} onChange={(e) => setForm({ ...form, state: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Website</label>
              <input type="url" value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Registration #</label>
              <input value={form.registration_number} onChange={(e) => setForm({ ...form, registration_number: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Medical Council</label>
              <input value={form.medical_council} onChange={(e) => setForm({ ...form, medical_council: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
            <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => { setShowAdd(false); setEditingItem(null); }}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button type="submit" disabled={saving}
              className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 disabled:opacity-50">
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Archive confirmation */}
      <Modal open={!!confirmArchive} onClose={() => setConfirmArchive(null)} title="Archive Doctor">
        <p className="text-sm text-gray-600 mb-4">Are you sure you want to archive this doctor?</p>
        <div className="flex justify-end gap-3">
          <button onClick={() => setConfirmArchive(null)}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
          <button onClick={() => confirmArchive && handleArchive(confirmArchive)}
            className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700">
            Archive
          </button>
        </div>
      </Modal>
    </div>
  );
}

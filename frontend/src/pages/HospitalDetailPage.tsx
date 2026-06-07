import { useState, useEffect, type FormEvent } from "react";
import { useParams, Link } from "react-router-dom";
import { hospitalsApi } from "../api";
import type { Hospital } from "../types";

export default function HospitalDetailPage() {
  const { hospitalId } = useParams<{ hospitalId: string }>();
  const [hospital, setHospital] = useState<Hospital | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "", city: "", state: "", address: "", phone: "", email: "",
    website: "", specialties: "", has_financial_assistance: false, rating: "",
  });

  const loadHospital = async () => {
    setLoading(true);
    try {
      const { data } = await hospitalsApi.get(hospitalId!);
      setHospital(data);
      setForm({
        name: data.name, city: data.city, state: data.state || "",
        address: data.address || "", phone: data.phone || "", email: data.email || "",
        website: data.website || "", specialties: data.specialties || "",
        has_financial_assistance: data.has_financial_assistance,
        rating: data.rating ? String(data.rating) : "",
      });
    } catch { /* interceptor */ }
    setLoading(false);
  };

  useEffect(() => { loadHospital(); }, [hospitalId]);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await hospitalsApi.update(hospitalId!, {
        name: form.name, city: form.city, state: form.state || undefined,
        address: form.address || undefined, phone: form.phone || undefined,
        email: form.email || undefined, website: form.website || undefined,
        specialties: form.specialties || undefined,
        has_financial_assistance: form.has_financial_assistance,
        rating: form.rating ? Number(form.rating) : undefined,
      });
      setEditing(false);
      loadHospital();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to save");
    } finally { setSaving(false); }
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!hospital) return <p className="text-red-500">Hospital not found.</p>;

  return (
    <div className="space-y-6">
      <Link to="/hospitals" className="text-sm text-blue-600 hover:underline">← Back to Hospitals</Link>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{hospital.name}</h2>
            <p className="text-gray-500 mt-1">{hospital.city}{hospital.state ? `, ${hospital.state}` : ""}</p>
          </div>
          {!editing && (
            <button onClick={() => setEditing(true)}
              className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700">
              Edit
            </button>
          )}
        </div>
      </div>

      {editing ? (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Edit Hospital</h3>
          {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}
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
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Specialties</label>
              <input type="text" value={form.specialties} onChange={(e) => setForm({ ...form, specialties: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" checked={form.has_financial_assistance}
                onChange={(e) => setForm({ ...form, has_financial_assistance: e.target.checked })} className="rounded border-gray-300" />
              <label className="text-sm text-gray-700">Offers financial assistance</label>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => setEditing(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
              <button type="submit" disabled={saving}
                className="px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50">
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Contact</h3>
            <dl className="space-y-2 text-sm">
              {hospital.address && <><dt className="text-gray-500">Address</dt><dd className="text-gray-900">{hospital.address}</dd></>}
              {hospital.phone && <><dt className="text-gray-500">Phone</dt><dd className="text-gray-900">{hospital.phone}</dd></>}
              {hospital.email && <><dt className="text-gray-500">Email</dt><dd className="text-gray-900">{hospital.email}</dd></>}
              {hospital.website && <><dt className="text-gray-500">Website</dt><dd><a href={hospital.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{hospital.website}</a></dd></>}
            </dl>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Details</h3>
            <dl className="space-y-2 text-sm">
              {hospital.specialties && <><dt className="text-gray-500">Specialties</dt><dd className="text-gray-900">{hospital.specialties}</dd></>}
              {hospital.rating && <><dt className="text-gray-500">Rating</dt><dd className="text-gray-900">{hospital.rating}/5</dd></>}
              <dt className="text-gray-500">Financial Assistance</dt>
              <dd className={hospital.has_financial_assistance ? "text-green-600 font-medium" : "text-gray-500"}>
                {hospital.has_financial_assistance ? "Available" : "Not available"}
              </dd>
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}

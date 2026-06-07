import { useState, useEffect, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { patientsApi } from "../api";
import type { Patient } from "../types";
import Modal from "../components/Modal";

const emptyForm = {
  full_name: "",
  age: "",
  gender: "" as string,
  phone: "",
  email: "",
  address: "",
  emergency_contact_name: "",
  emergency_contact_phone: "",
};

export default function PatientsPage() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const loadPatients = async () => {
    setLoading(true);
    try {
      const { data } = await patientsApi.list({
        search: search || undefined,
        per_page: 20,
      });
      setPatients(data.items);
      setTotal(data.total);
    } catch {
      /* handled by interceptor */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatients();
  }, [search]);

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      await patientsApi.create({
        full_name: form.full_name,
        age: Number(form.age),
        gender: form.gender,
        phone: form.phone || undefined,
        email: form.email || undefined,
        address: form.address || undefined,
        emergency_contact_name: form.emergency_contact_name || undefined,
        emergency_contact_phone: form.emergency_contact_phone || undefined,
      });
      setShowAdd(false);
      setForm(emptyForm);
      loadPatients();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(msg || "Failed to create patient");
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async (e: React.MouseEvent, patientId: string, name: string) => {
    e.stopPropagation();
    if (!confirm(`Archive patient "${name}"? This will soft-delete the record.`)) return;
    try {
      await patientsApi.archive(patientId);
      loadPatients();
    } catch {
      /* interceptor */
    }
  };

  const handleDelete = async (e: React.MouseEvent, patientId: string, name: string) => {
    e.stopPropagation();
    if (!confirm(`PERMANENTLY DELETE "${name}"?\n\nThis will remove the patient and ALL related records (cases, documents, medical profile). This cannot be undone.`)) return;
    try {
      await patientsApi.hardDelete(patientId);
      loadPatients();
    } catch {
      /* interceptor */
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Patients</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{total} total</span>
          <button
            onClick={() => { setFormError(""); setShowAdd(true); }}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Add Patient
          </button>
        </div>
      </div>

      <div className="mb-4">
        <input
          type="text"
          placeholder="Search patients..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Age</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Gender</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Phone</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {patients.map((p) => (
                <tr key={p.id} className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/patients/${p.id}`)}>
                  <td className="px-4 py-3 font-medium text-gray-900">{p.full_name}</td>
                  <td className="px-4 py-3 text-gray-600">{p.age}</td>
                  <td className="px-4 py-3 text-gray-600 capitalize">{p.gender}</td>
                  <td className="px-4 py-3 text-gray-600">{p.phone || "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                        p.status === "active"
                          ? "bg-green-100 text-green-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {p.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {p.status === "active" && (
                      <button
                        onClick={(e) => handleArchive(e, p.id, p.full_name)}
                        className="px-3 py-1 text-xs font-medium bg-red-50 text-red-600 rounded-lg hover:bg-red-100"
                      >
                        Archive
                      </button>
                    )}
                    <button
                      onClick={(e) => handleDelete(e, p.id, p.full_name)}
                      className="ml-2 px-3 py-1 text-xs font-medium bg-gray-50 text-gray-500 rounded-lg hover:bg-gray-100"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {patients.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">
                    No patients found. Click "Add Patient" to create one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Add Patient">
        {formError && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{formError}</div>
        )}
        <form onSubmit={handleAdd} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
            <input
              type="text"
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Age *</label>
              <input
                type="number"
                required
                min={0}
                max={150}
                value={form.age}
                onChange={(e) => setForm({ ...form, age: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Gender *</label>
              <select
                required
                value={form.gender}
                onChange={(e) => setForm({ ...form, gender: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select...</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="prefer_not_to_say">Prefer not to say</option>
              </select>
            </div>
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
              <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact</label>
              <input
                type="text"
                placeholder="Name"
                value={form.emergency_contact_name}
                onChange={(e) => setForm({ ...form, emergency_contact_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">&nbsp;</label>
              <input
                type="tel"
                placeholder="Phone"
                value={form.emergency_contact_phone}
                onChange={(e) => setForm({ ...form, emergency_contact_phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
              />
            </div>
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
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {saving ? "Saving..." : "Add Patient"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

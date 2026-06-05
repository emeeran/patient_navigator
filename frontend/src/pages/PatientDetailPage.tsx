import { useState, useEffect, type FormEvent } from "react";
import { useParams, Link } from "react-router-dom";
import { patientsApi, casesApi } from "../api";
import type { Patient, Case } from "../types";

export default function PatientDetailPage() {
  const { patientId } = useParams<{ patientId: string }>();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    full_name: "",
    age: "",
    gender: "",
    phone: "",
    email: "",
    address: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
  });
  const [error, setError] = useState("");

  useEffect(() => {
    loadPatient();
  }, [patientId]);

  const loadPatient = async () => {
    setLoading(true);
    try {
      const [pRes, cRes] = await Promise.all([
        patientsApi.get(patientId!),
        casesApi.listForPatient(patientId!, { per_page: 100 }),
      ]);
      setPatient(pRes.data);
      setCases(cRes.data.items);
      const p = pRes.data;
      setForm({
        full_name: p.full_name,
        age: String(p.age),
        gender: p.gender,
        phone: p.phone || "",
        email: p.email || "",
        address: p.address || "",
        emergency_contact_name: p.emergency_contact_name || "",
        emergency_contact_phone: p.emergency_contact_phone || "",
      });
    } catch { /* interceptor */ }
    setLoading(false);
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await patientsApi.update(patientId!, {
        full_name: form.full_name,
        age: Number(form.age),
        gender: form.gender,
        phone: form.phone || undefined,
        email: form.email || undefined,
        address: form.address || undefined,
        emergency_contact_name: form.emergency_contact_name || undefined,
        emergency_contact_phone: form.emergency_contact_phone || undefined,
      });
      setEditing(false);
      loadPatient();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleArchive = async () => {
    if (!confirm("Archive this patient? This will soft-delete the record.")) return;
    try {
      await patientsApi.archive(patientId!);
      window.history.back();
    } catch { /* interceptor */ }
  };

  const statusColor = (status: string) => {
    const map: Record<string, string> = {
      new: "bg-blue-100 text-blue-700",
      under_review: "bg-yellow-100 text-yellow-700",
      in_treatment: "bg-green-100 text-green-700",
      closed: "bg-gray-100 text-gray-600",
    };
    return map[status] || "bg-gray-100 text-gray-600";
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!patient) return <p className="text-red-500">Patient not found.</p>;

  return (
    <div className="space-y-6">
      <Link to="/patients" className="text-sm text-blue-600 hover:underline">← Back to Patients</Link>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{patient.full_name}</h2>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              <span>Age: {patient.age}</span>
              <span className="capitalize">Gender: {patient.gender}</span>
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                patient.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
              }`}>
                {patient.status}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
              >
                Edit
              </button>
            )}
            {patient.status === "active" && (
              <button
                onClick={handleArchive}
                className="px-4 py-2 bg-red-50 text-red-600 text-sm font-medium rounded-lg hover:bg-red-100"
              >
                Archive
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Edit Form */}
      {editing && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Edit Patient</h3>
          {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name *</label>
                <input type="text" required value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Age *</label>
                  <input type="number" required min={0} max={150} value={form.age}
                    onChange={(e) => setForm({ ...form, age: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Gender *</label>
                  <select required value={form.gender}
                    onChange={(e) => setForm({ ...form, gender: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                    <option value="prefer_not_to_say">Prefer not to say</option>
                  </select>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input type="tel" value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
              <input type="text" value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact Name</label>
                <input type="text" value={form.emergency_contact_name}
                  onChange={(e) => setForm({ ...form, emergency_contact_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact Phone</label>
                <input type="tel" value={form.emergency_contact_phone}
                  onChange={(e) => setForm({ ...form, emergency_contact_phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => setEditing(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
              <button type="submit" disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Contact Info */}
      {!editing && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Contact Information</h3>
            <dl className="space-y-2 text-sm">
              {patient.phone && <><dt className="text-gray-500">Phone</dt><dd className="text-gray-900">{patient.phone}</dd></>}
              {patient.email && <><dt className="text-gray-500">Email</dt><dd className="text-gray-900">{patient.email}</dd></>}
              {patient.address && <><dt className="text-gray-500">Address</dt><dd className="text-gray-900">{patient.address}</dd></>}
            </dl>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Emergency Contact</h3>
            <dl className="space-y-2 text-sm">
              {patient.emergency_contact_name && <><dt className="text-gray-500">Name</dt><dd className="text-gray-900">{patient.emergency_contact_name}</dd></>}
              {patient.emergency_contact_phone && <><dt className="text-gray-500">Phone</dt><dd className="text-gray-900">{patient.emergency_contact_phone}</dd></>}
              {(!patient.emergency_contact_name && !patient.emergency_contact_phone) && <dd className="text-gray-400">Not provided</dd>}
            </dl>
          </div>
        </div>
      )}

      {/* Cases */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Cases ({cases.length})</h3>
        {cases.length === 0 ? (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
            No cases for this patient.
          </div>
        ) : (
          <div className="space-y-2">
            {cases.map((c) => (
              <Link key={c.id} to={`/cases/${c.id}`}
                className="block bg-white rounded-xl border border-gray-200 p-4 hover:shadow-sm transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{c.diagnosis}</p>
                    <p className="text-xs text-gray-500">Created {new Date(c.created_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColor(c.status)}`}>
                    {c.status.replace("_", " ")}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

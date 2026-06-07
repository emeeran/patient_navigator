import { useState, useEffect, type FormEvent } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { doctorsApi } from "../api";
import type { Doctor } from "../types";
import { useAuth } from "../contexts/AuthContext";

export default function DoctorDetailPage() {
  const { doctorId } = useParams<{ doctorId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    name: "", city: "", state: "", address: "", phone: "", email: "", website: "",
    specialty: "", qualification: "", registration_number: "", medical_council: "",
    hospital_name: "", practice_type: "",
  });

  const loadDoctor = async () => {
    setLoading(true);
    try {
      const { data } = await doctorsApi.get(doctorId!);
      setDoctor(data);
      setForm({
        name: data.name, city: data.city, state: data.state || "", address: data.address || "",
        phone: data.phone || "", email: data.email || "", website: data.website || "",
        specialty: data.specialty || "", qualification: data.qualification || "",
        registration_number: data.registration_number || "", medical_council: data.medical_council || "",
        hospital_name: data.hospital_name || "", practice_type: data.practice_type || "",
      });
    } catch { navigate("/doctors"); }
    setLoading(false);
  };

  useEffect(() => { loadDoctor(); }, [doctorId]);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await doctorsApi.update(doctorId!, form);
      setEditing(false);
      loadDoctor();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to update doctor.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;
  if (!doctor) return null;

  const F = (label: string, field: string, type = "text") => (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input type={type} value={(form as Record<string, string>)[field]}
        onChange={(e) => setForm({ ...form, [field]: e.target.value })}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
    </div>
  );

  return (
    <div>
      {/* Back link */}
      <button onClick={() => navigate("/doctors")}
        className="text-sm text-teal-600 hover:text-teal-800 mb-4 inline-flex items-center gap-1">
        ← Back to Doctors
      </button>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold text-gray-900">{doctor.name}</h2>
          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
            doctor.practice_type === "government" ? "bg-green-100 text-green-700"
              : doctor.practice_type === "private" ? "bg-blue-100 text-blue-700"
              : "bg-gray-100 text-gray-500"
          }`}>
            {doctor.practice_type === "government" ? "Government" : doctor.practice_type === "private" ? "Private" : ""}
          </span>
        </div>
        {isAdmin && !editing && (
          <button onClick={() => setEditing(true)}
            className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700">
            Edit
          </button>
        )}
      </div>

      {editing ? (
        <form onSubmit={handleSave} className="space-y-4 bg-white p-6 rounded-xl border border-gray-200">
          {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded">{error}</p>}
          <div className="grid grid-cols-2 gap-4">
            {F("Name *", "name")}
            {F("City *", "city")}
            {F("Specialty", "specialty")}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Practice Type</label>
              <select value={form.practice_type} onChange={(e) => setForm({ ...form, practice_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="">—</option>
                <option value="government">Government</option>
                <option value="private">Private</option>
              </select>
            </div>
            {F("Phone", "phone", "tel")}
            {F("Email", "email", "email")}
            {F("Hospital/Clinic", "hospital_name")}
            {F("Qualification", "qualification")}
            {F("State", "state")}
            {F("Website", "website", "url")}
            {F("Registration #", "registration_number")}
            {F("Medical Council", "medical_council")}
          </div>
          {F("Address", "address")}
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setEditing(false)}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button type="submit" disabled={saving}
              className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700 disabled:opacity-50">
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </form>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Contact & Location */}
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">Contact & Location</h3>
            <dl className="space-y-3">
              {[
                ["Address", doctor.address],
                ["City", doctor.city + (doctor.state ? `, ${doctor.state}` : "")],
                ["Phone", doctor.phone],
                ["Email", doctor.email],
                ["Website", doctor.website],
              ].map(([label, value]) => (
                <div key={label as string}>
                  <dt className="text-xs font-medium text-gray-500">{label}</dt>
                  <dd className="text-sm text-gray-900 mt-0.5">
                    {label === "Email" && value ? (
                      <a href={`mailto:${value}`} className="text-teal-600 hover:underline">{value}</a>
                    ) : label === "Website" && value ? (
                      <a href={value as string} target="_blank" rel="noopener noreferrer" className="text-teal-600 hover:underline">{value}</a>
                    ) : value || "—"}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          {/* Professional Details */}
          <div className="bg-white p-6 rounded-xl border border-gray-200">
            <h3 className="text-sm font-semibold text-gray-500 uppercase mb-4">Professional Details</h3>
            <dl className="space-y-3">
              {[
                ["Specialty", doctor.specialty],
                ["Qualification", doctor.qualification],
                ["Registration #", doctor.registration_number],
                ["Medical Council", doctor.medical_council],
                ["Hospital/Clinic", doctor.hospital_name],
                ["Practice Type", doctor.practice_type === "government" ? "Government" : doctor.practice_type === "private" ? "Private" : null],
              ].map(([label, value]) => (
                <div key={label as string}>
                  <dt className="text-xs font-medium text-gray-500">{label}</dt>
                  <dd className="text-sm text-gray-900 mt-0.5">{value || "—"}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}

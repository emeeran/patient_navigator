import { useState, useEffect, type KeyboardEvent } from "react";
import { useParams, Link } from "react-router-dom";
import { patientsApi, casesApi, medicalProfilesApi } from "../api";
import type { Patient, Case, MedicalProfile } from "../types";

// ── Tag-input helper ───────────────────────────────────
function TagInput({
  label,
  tags,
  onChange,
  placeholder,
}: {
  label: string;
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
}) {
  const [input, setInput] = useState("");

  const add = () => {
    const val = input.trim();
    if (val && !tags.includes(val)) {
      onChange([...tags, val]);
    }
    setInput("");
  };

  const remove = (idx: number) => onChange(tags.filter((_, i) => i !== idx));

  const handleKey = (e: KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      add();
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <div className="flex flex-wrap gap-1.5 mb-1.5">
        {tags.map((t, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full"
          >
            {t}
            <button
              type="button"
              onClick={() => remove(i)}
              className="text-blue-400 hover:text-blue-600"
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="flex gap-1.5">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder={placeholder || "Type and press Enter"}
          className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={add}
          className="px-3 py-1.5 text-sm text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50"
        >
          Add
        </button>
      </div>
    </div>
  );
}

// ── Family history sub-form ─────────────────────────────
function FamilyHistoryInput({
  items,
  onChange,
}: {
  items: { relation: string; condition: string }[];
  onChange: (items: { relation: string; condition: string }[]) => void;
}) {
  const [rel, setRel] = useState("");
  const [cond, setCond] = useState("");

  const add = () => {
    const r = rel.trim();
    const c = cond.trim();
    if (r && c) {
      onChange([...items, { relation: r, condition: c }]);
      setRel("");
      setCond("");
    }
  };

  const remove = (idx: number) => onChange(items.filter((_, i) => i !== idx));

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">Family Medical History</label>
      {items.length > 0 && (
        <div className="space-y-1 mb-2">
          {items.map((item, i) => (
            <span
              key={i}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-50 text-purple-700 text-xs rounded-full mr-1.5"
            >
              {item.relation}: {item.condition}
              <button
                type="button"
                onClick={() => remove(i)}
                className="text-purple-400 hover:text-purple-600"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-1.5">
        <select
          value={rel}
          onChange={(e) => setRel(e.target.value)}
          className="px-2 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Relation…</option>
          <option value="father">Father</option>
          <option value="mother">Mother</option>
          <option value="brother">Brother</option>
          <option value="sister">Sister</option>
          <option value="grandfather">Grandfather</option>
          <option value="grandmother">Grandmother</option>
          <option value="other">Other</option>
        </select>
        <input
          type="text"
          value={cond}
          onChange={(e) => setCond(e.target.value)}
          placeholder="Condition"
          className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={add}
          className="px-3 py-1.5 text-sm text-blue-600 border border-blue-300 rounded-lg hover:bg-blue-50"
        >
          Add
        </button>
      </div>
    </div>
  );
}

// ── Empty form state ────────────────────────────────────
interface MedFormState {
  date_of_birth: string;
  height_cm: string;
  weight_kg: string;
  blood_type: string;
  chronic_conditions: string[];
  current_medications: string[];
  allergies: string[];
  past_medical_history: string[];
  family_medical_history: { relation: string; condition: string }[];
  notes: string;
}

const emptyMedForm: MedFormState = {
  date_of_birth: "",
  height_cm: "",
  weight_kg: "",
  blood_type: "",
  chronic_conditions: [],
  current_medications: [],
  allergies: [],
  past_medical_history: [],
  family_medical_history: [],
  notes: "",
};

function medFormFromProfile(p: MedicalProfile): MedFormState {
  return {
    date_of_birth: p.date_of_birth || "",
    height_cm: p.height_cm != null ? String(p.height_cm) : "",
    weight_kg: p.weight_kg != null ? String(p.weight_kg) : "",
    blood_type: p.blood_type || "",
    chronic_conditions: p.chronic_conditions || [],
    current_medications: p.current_medications || [],
    allergies: p.allergies || [],
    past_medical_history: p.past_medical_history || [],
    family_medical_history: p.family_medical_history || [],
    notes: p.notes || "",
  };
}

// ── Main Component ──────────────────────────────────────
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

  // Medical profile state
  const [medProfile, setMedProfile] = useState<MedicalProfile | null>(null);
  const [medEditing, setMedEditing] = useState(false);
  const [medSaving, setMedSaving] = useState(false);
  const [medForm, setMedForm] = useState<MedFormState>(emptyMedForm);
  const [medError, setMedError] = useState("");

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

      // Load medical profile
      try {
        const mpRes = await medicalProfilesApi.get(patientId!);
        setMedProfile(mpRes.data);
      } catch {
        // 404 = no profile yet, that's fine
        setMedProfile(null);
      }
    } catch {
      /* interceptor */
    }
    setLoading(false);
  };

  useEffect(() => {
    loadPatient();
  }, [patientId]);

  const handleSave = async (e: { preventDefault: () => void }) => {
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
    } catch {
      /* interceptor */
    }
  };

  // ── Medical profile save ─────────────────────────────
  const buildMedPayload = () => ({
    date_of_birth: medForm.date_of_birth || undefined,
    height_cm: medForm.height_cm ? Number(medForm.height_cm) : undefined,
    weight_kg: medForm.weight_kg ? Number(medForm.weight_kg) : undefined,
    blood_type: medForm.blood_type || undefined,
    chronic_conditions: medForm.chronic_conditions.length ? medForm.chronic_conditions : undefined,
    current_medications: medForm.current_medications.length ? medForm.current_medications : undefined,
    allergies: medForm.allergies.length ? medForm.allergies : undefined,
    past_medical_history: medForm.past_medical_history.length ? medForm.past_medical_history : undefined,
    family_medical_history: medForm.family_medical_history.length ? medForm.family_medical_history : undefined,
    notes: medForm.notes || undefined,
  });

  const handleMedSave = async (e: { preventDefault: () => void }) => {
    e.preventDefault();
    setMedSaving(true);
    setMedError("");
    try {
      const payload = buildMedPayload();
      if (medProfile) {
        const res = await medicalProfilesApi.update(patientId!, payload);
        setMedProfile(res.data);
      } else {
        const res = await medicalProfilesApi.create(patientId!, payload);
        setMedProfile(res.data);
      }
      setMedEditing(false);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMedError(msg || "Failed to save medical profile");
    } finally {
      setMedSaving(false);
    }
  };

  const startMedEdit = () => {
    setMedForm(medProfile ? medFormFromProfile(medProfile) : emptyMedForm);
    setMedEditing(true);
    setMedError("");
  };

  const handleDeleteProfile = async () => {
    if (!confirm("Delete this medical profile? This cannot be undone.")) return;
    try {
      await medicalProfilesApi.remove(patientId!);
      setMedProfile(null);
    } catch {
      /* interceptor */
    }
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
      <Link to="/patients" className="text-sm text-blue-600 hover:underline">
        ← Back to Patients
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{patient.full_name}</h2>
            <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
              <span>Age: {patient.age}</span>
              <span className="capitalize">Gender: {patient.gender}</span>
              <span
                className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                  patient.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                }`}
              >
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact Name</label>
                <input
                  type="text"
                  value={form.emergency_contact_name}
                  onChange={(e) => setForm({ ...form, emergency_contact_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact Phone</label>
                <input
                  type="tel"
                  value={form.emergency_contact_phone}
                  onChange={(e) => setForm({ ...form, emergency_contact_phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
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
              {patient.phone && (
                <>
                  <dt className="text-gray-500">Phone</dt>
                  <dd className="text-gray-900">{patient.phone}</dd>
                </>
              )}
              {patient.email && (
                <>
                  <dt className="text-gray-500">Email</dt>
                  <dd className="text-gray-900">{patient.email}</dd>
                </>
              )}
              {patient.address && (
                <>
                  <dt className="text-gray-500">Address</dt>
                  <dd className="text-gray-900">{patient.address}</dd>
                </>
              )}
            </dl>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Emergency Contact</h3>
            <dl className="space-y-2 text-sm">
              {patient.emergency_contact_name && (
                <>
                  <dt className="text-gray-500">Name</dt>
                  <dd className="text-gray-900">{patient.emergency_contact_name}</dd>
                </>
              )}
              {patient.emergency_contact_phone && (
                <>
                  <dt className="text-gray-500">Phone</dt>
                  <dd className="text-gray-900">{patient.emergency_contact_phone}</dd>
                </>
              )}
              {!patient.emergency_contact_name && !patient.emergency_contact_phone && (
                <dd className="text-gray-400">Not provided</dd>
              )}
            </dl>
          </div>
        </div>
      )}

      {/* Medical Profile */}
      {!editing && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Medical Profile</h3>
            {!medEditing && (
              <div className="flex gap-2">
                <button
                  onClick={startMedEdit}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
                >
                  {medProfile ? "Edit" : "Add Medical Profile"}
                </button>
                {medProfile && (
                  <button
                    onClick={handleDeleteProfile}
                    className="px-4 py-2 border border-gray-300 text-gray-600 text-sm font-medium rounded-lg hover:bg-gray-50"
                  >
                    Delete
                  </button>
                )}
              </div>
            )}
          </div>

          {medEditing ? (
            /* ── Medical Profile Form ── */
            <form onSubmit={handleMedSave} className="space-y-4">
              {medError && <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{medError}</div>}

              {/* Vitals row */}
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                  <input
                    type="date"
                    value={medForm.date_of_birth}
                    onChange={(e) => setMedForm({ ...medForm, date_of_birth: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Height (cm)</label>
                  <input
                    type="number"
                    min={1}
                    max={300}
                    step="0.1"
                    value={medForm.height_cm}
                    onChange={(e) => setMedForm({ ...medForm, height_cm: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg)</label>
                  <input
                    type="number"
                    min={1}
                    max={500}
                    step="0.1"
                    value={medForm.weight_kg}
                    onChange={(e) => setMedForm({ ...medForm, weight_kg: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Blood Type</label>
                  <select
                    value={medForm.blood_type}
                    onChange={(e) => setMedForm({ ...medForm, blood_type: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Unknown</option>
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                  </select>
                </div>
              </div>

              {/* List fields */}
              <TagInput
                label="Chronic Conditions"
                tags={medForm.chronic_conditions}
                onChange={(tags) => setMedForm({ ...medForm, chronic_conditions: tags })}
                placeholder="e.g. Hypertension, Type 2 Diabetes"
              />
              <TagInput
                label="Current Medications"
                tags={medForm.current_medications}
                onChange={(tags) => setMedForm({ ...medForm, current_medications: tags })}
                placeholder="e.g. Metformin 500mg, Lisinopril 10mg"
              />
              <TagInput
                label="Allergies"
                tags={medForm.allergies}
                onChange={(tags) => setMedForm({ ...medForm, allergies: tags })}
                placeholder="e.g. Penicillin, Latex"
              />
              <TagInput
                label="Past Medical History"
                tags={medForm.past_medical_history}
                onChange={(tags) => setMedForm({ ...medForm, past_medical_history: tags })}
                placeholder="e.g. Appendectomy 2018, Pneumonia 2020"
              />
              <FamilyHistoryInput
                items={medForm.family_medical_history}
                onChange={(items) => setMedForm({ ...medForm, family_medical_history: items })}
              />

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={medForm.notes}
                  onChange={(e) => setMedForm({ ...medForm, notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  placeholder="Navigator observations about patient health"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setMedEditing(false)}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={medSaving}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {medSaving ? "Saving..." : medProfile ? "Update Profile" : "Create Profile"}
                </button>
              </div>
            </form>
          ) : medProfile ? (
            /* ── Medical Profile Display ── */
            <div className="space-y-4">
              {/* Vitals row */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
                {medProfile.date_of_birth && (
                  <div>
                    <p className="text-xs text-gray-500">DOB</p>
                    <p className="text-sm font-medium text-gray-900">
                      {new Date(medProfile.date_of_birth).toLocaleDateString()}
                    </p>
                  </div>
                )}
                {medProfile.height_cm != null && (
                  <div>
                    <p className="text-xs text-gray-500">Height</p>
                    <p className="text-sm font-medium text-gray-900">{medProfile.height_cm} cm</p>
                  </div>
                )}
                {medProfile.weight_kg != null && (
                  <div>
                    <p className="text-xs text-gray-500">Weight</p>
                    <p className="text-sm font-medium text-gray-900">{medProfile.weight_kg} kg</p>
                  </div>
                )}
                {medProfile.bmi != null && (
                  <div>
                    <p className="text-xs text-gray-500">BMI</p>
                    <span
                      className={`inline-block px-2 py-0.5 text-xs font-medium rounded-full ${
                        medProfile.bmi < 18.5
                          ? "bg-blue-100 text-blue-700"
                          : medProfile.bmi < 25
                            ? "bg-green-100 text-green-700"
                            : medProfile.bmi < 30
                              ? "bg-yellow-100 text-yellow-700"
                              : "bg-red-100 text-red-700"
                      }`}
                    >
                      {medProfile.bmi}
                    </span>
                  </div>
                )}
                {medProfile.blood_type && (
                  <div>
                    <p className="text-xs text-gray-500">Blood Type</p>
                    <p className="text-sm font-medium text-gray-900">{medProfile.blood_type}</p>
                  </div>
                )}
              </div>

              {/* Chronic conditions */}
              {medProfile.chronic_conditions?.length ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Chronic Conditions</p>
                  <div className="flex flex-wrap gap-1.5">
                    {medProfile.chronic_conditions.map((c, i) => (
                      <span key={i} className="px-2 py-0.5 bg-orange-50 text-orange-700 text-xs rounded-full">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Current medications */}
              {medProfile.current_medications?.length ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Current Medications</p>
                  <div className="flex flex-wrap gap-1.5">
                    {medProfile.current_medications.map((m, i) => (
                      <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">
                        {m}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Allergies */}
              {medProfile.allergies?.length ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Allergies</p>
                  <div className="flex flex-wrap gap-1.5">
                    {medProfile.allergies.map((a, i) => (
                      <span key={i} className="px-2 py-0.5 bg-red-50 text-red-700 text-xs rounded-full">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Past medical history */}
              {medProfile.past_medical_history?.length ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Past Medical History</p>
                  <ul className="list-disc list-inside text-sm text-gray-700 space-y-0.5">
                    {medProfile.past_medical_history.map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {/* Family medical history */}
              {medProfile.family_medical_history?.length ? (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Family Medical History</p>
                  <div className="flex flex-wrap gap-1.5">
                    {medProfile.family_medical_history.map((f, i) => (
                      <span key={i} className="px-2 py-0.5 bg-purple-50 text-purple-700 text-xs rounded-full">
                        {f.relation}: {f.condition}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {/* Notes */}
              {medProfile.notes && (
                <div>
                  <p className="text-xs text-gray-500 mb-1">Notes</p>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{medProfile.notes}</p>
                </div>
              )}
            </div>
          ) : (
            /* ── Empty state ── */
            <p className="text-sm text-gray-400">
              No medical profile recorded yet. Click "Add Medical Profile" to add patient health data.
            </p>
          )}
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
              <Link
                key={c.id}
                to={`/cases/${c.id}`}
                className="block bg-white rounded-xl border border-gray-200 p-4 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{c.diagnosis}</p>
                    <p className="text-xs text-gray-500">
                      Created {new Date(c.created_at).toLocaleDateString()}
                    </p>
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

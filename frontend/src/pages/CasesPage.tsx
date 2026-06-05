import { useState, useEffect, type FormEvent } from "react";
import { casesApi, patientsApi } from "../api";
import type { Case, Patient } from "../types";
import Modal from "../components/Modal";

const emptyForm = {
  patient_id: "",
  diagnosis: "",
  priority: "medium" as string,
  notes: "",
};

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [patients, setPatientsList] = useState<Patient[]>([]);

  useEffect(() => {
    loadCases();
  }, []);

  const loadCases = async () => {
    setLoading(true);
    try {
      const { data } = await casesApi.list({ per_page: 20 });
      setCases(data.items);
      setTotal(data.total);
    } catch {
      /* handled by interceptor */
    } finally {
      setLoading(false);
    }
  };

  const openAdd = async () => {
    setForm(emptyForm);
    setFormError("");
    setShowAdd(true);
    try {
      const { data } = await patientsApi.list({ per_page: 100 });
      setPatientsList(data.items);
    } catch {
      /* handled */
    }
  };

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");
    try {
      await casesApi.create(form.patient_id, {
        diagnosis: form.diagnosis,
        priority: form.priority,
        notes: form.notes || undefined,
      });
      setShowAdd(false);
      setForm(emptyForm);
      loadCases();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(msg || "Failed to create case");
    } finally {
      setSaving(false);
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "new":
        return "bg-blue-100 text-blue-700";
      case "under_review":
        return "bg-yellow-100 text-yellow-700";
      case "in_treatment":
        return "bg-green-100 text-green-700";
      case "closed":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  const priorityColor = (priority: string) => {
    switch (priority) {
      case "high":
        return "text-red-600";
      case "medium":
        return "text-yellow-600";
      case "low":
        return "text-green-600";
      case "critical":
        return "text-red-800";
      default:
        return "text-gray-600";
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Cases</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{total} total</span>
          <button
            onClick={openAdd}
            className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors"
          >
            + New Case
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : (
        <div className="space-y-3">
          {cases.map((c) => (
            <div
              key={c.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{c.diagnosis}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Case ID: {c.id.slice(0, 8)}...
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex px-2.5 py-1 text-xs font-medium rounded-full ${statusColor(c.status)}`}
                  >
                    {c.status.replace("_", " ")}
                  </span>
                  <span
                    className={`text-xs font-medium capitalize ${priorityColor(c.priority)}`}
                  >
                    {c.priority}
                  </span>
                </div>
              </div>
              {c.notes && (
                <p className="text-sm text-gray-600 mt-2">{c.notes}</p>
              )}
            </div>
          ))}
          {cases.length === 0 && (
            <p className="text-center text-gray-500 py-8">
              No cases found. Click "New Case" to create one.
            </p>
          )}
        </div>
      )}

      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="New Case">
        {formError && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{formError}</div>
        )}
        <form onSubmit={handleAdd} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Patient *</label>
            <select
              required
              value={form.patient_id}
              onChange={(e) => setForm({ ...form, patient_id: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select patient...</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.full_name} (Age: {p.age})
                </option>
              ))}
            </select>
            {patients.length === 0 && (
              <p className="text-xs text-gray-400 mt-1">
                No patients found — add a patient first.
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Diagnosis *</label>
            <input
              type="text"
              required
              value={form.diagnosis}
              onChange={(e) => setForm({ ...form, diagnosis: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select
              value={form.priority}
              onChange={(e) => setForm({ ...form, priority: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              rows={3}
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            />
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
              className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              {saving ? "Saving..." : "Create Case"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

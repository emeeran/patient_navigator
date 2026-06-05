import { useState, useEffect, type FormEvent } from "react";
import { followUpsApi, casesApi } from "../api";
import type { FollowUp, Case } from "../types";
import Modal from "../components/Modal";

const emptyForm = { case_id: "", scheduled_date: "", follow_up_type: "" as string, notes: "" };

const FOLLOW_UP_TYPES = [
  { value: "appointment", label: "Appointment" },
  { value: "checkup", label: "Checkup" },
  { value: "lab_test", label: "Lab Test" },
  { value: "imaging", label: "Imaging" },
  { value: "referral", label: "Referral" },
];

export default function FollowUpsPage() {
  const [items, setItems] = useState<FollowUp[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editingItem, setEditingItem] = useState<FollowUp | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [cases, setCasesList] = useState<Case[]>([]);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);

  useEffect(() => { load(); }, []);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await followUpsApi.upcoming({ per_page: 20 });
      setItems(data.items);
      setTotal(data.total);
    } catch { /* handled */ } finally { setLoading(false); }
  };

  const openAdd = async () => {
    setForm(emptyForm); setFormError(""); setShowAdd(true);
    try { const { data } = await casesApi.list({ per_page: 100 }); setCasesList(data.items); } catch { /* */ }
  };

  const openEdit = async (fu: FollowUp) => {
    setEditingItem(fu);
    setForm({
      case_id: fu.case_id,
      scheduled_date: fu.scheduled_date ? fu.scheduled_date.slice(0, 16) : "",
      follow_up_type: fu.follow_up_type,
      notes: fu.notes || "",
    });
    setFormError("");
  };

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true); setFormError("");
    try {
      if (editingItem) {
        await followUpsApi.update(editingItem.id, {
          scheduled_date: form.scheduled_date,
          follow_up_type: form.follow_up_type,
          notes: form.notes || undefined,
        });
        setEditingItem(null);
      } else {
        await followUpsApi.create(form.case_id, {
          scheduled_date: form.scheduled_date,
          follow_up_type: form.follow_up_type,
          notes: form.notes || undefined,
        });
        setShowAdd(false);
      }
      setForm(emptyForm);
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(msg || "Failed to save follow-up");
    } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    try {
      await followUpsApi.cancel(id);
      setConfirmDelete(null);
      load();
    } catch { /* handled */ }
  };

  const modalTitle = editingItem ? `Edit: ${editingItem.follow_up_type.replace("_", " ")}` : "Schedule Follow-Up";
  const showModal = showAdd || editingItem !== null;
  const closeModal = () => { setShowAdd(false); setEditingItem(null); setForm(emptyForm); };

  const statusColor = (status: string) => {
    switch (status) {
      case "scheduled": return "bg-blue-100 text-blue-700";
      case "completed": return "bg-green-100 text-green-700";
      case "overdue": return "bg-red-100 text-red-700";
      case "cancelled": return "bg-gray-100 text-gray-600";
      default: return "bg-gray-100 text-gray-600";
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Follow-Ups</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{total} upcoming</span>
          <button onClick={openAdd}
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors">
            + Schedule Follow-Up
          </button>
        </div>
      </div>

      {loading ? <p className="text-gray-500">Loading...</p> : (
        <div className="space-y-3">
          {items.map((fu) => (
            <div key={fu.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow relative group">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900 capitalize">{fu.follow_up_type.replace("_", " ")}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Scheduled: {new Date(fu.scheduled_date).toLocaleDateString("en-US", {
                      weekday: "short", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-flex px-2.5 py-1 text-xs font-medium rounded-full ${statusColor(fu.status)}`}>
                    {fu.status}
                  </span>
                  {fu.status !== "completed" && fu.status !== "cancelled" && (
                    <button onClick={() => openEdit(fu)}
                      className="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                      Edit
                    </button>
                  )}
                  <button onClick={() => setConfirmDelete(fu.id)}
                    className="px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                    Delete
                  </button>
                </div>
              </div>
              {fu.notes && <p className="text-sm text-gray-600 mt-2">{fu.notes}</p>}
            </div>
          ))}
          {items.length === 0 && <p className="text-center text-gray-500 py-8">No upcoming follow-ups.</p>}
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal open={showModal} onClose={closeModal} title={modalTitle}>
        {formError && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{formError}</div>}
        <form onSubmit={handleSave} className="space-y-4">
          {!editingItem && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Case *</label>
              <select required value={form.case_id}
                onChange={(e) => setForm({ ...form, case_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
                <option value="">Select case...</option>
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>{c.diagnosis} ({c.id.slice(0, 8)}...)</option>
                ))}
              </select>
              {cases.length === 0 && <p className="text-xs text-gray-400 mt-1">No cases found — create a case first.</p>}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Type *</label>
            <select required value={form.follow_up_type}
              onChange={(e) => setForm({ ...form, follow_up_type: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
              <option value="">Select type...</option>
              {FOLLOW_UP_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Scheduled Date & Time *</label>
            <input type="datetime-local" required value={form.scheduled_date}
              onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea rows={3} value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button type="submit" disabled={saving}
              className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              {saving ? "Saving..." : editingItem ? "Save Changes" : "Schedule"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmDelete(null)} />
          <div className="relative bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Delete Follow-Up?</h3>
            <p className="text-sm text-gray-600 mb-4">This follow-up will be permanently removed.</p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setConfirmDelete(null)} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
              <button onClick={() => handleDelete(confirmDelete)}
                className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700">Delete</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

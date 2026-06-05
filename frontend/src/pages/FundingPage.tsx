import { useState, useEffect, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { fundingApi } from "../api";
import type { FundingProgram } from "../types";
import Modal from "../components/Modal";
import { useAuth } from "../contexts/AuthContext";

const emptyForm = {
  name: "", description: "", provider: "", program_type: "",
  eligibility_criteria: "", max_amount: "", application_url: "",
  deadline: "", contact_email: "", contact_phone: "",
};

export default function FundingPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<FundingProgram[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editingItem, setEditingItem] = useState<FundingProgram | null>(null);
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
      const { data } = await fundingApi.list({ search: search || undefined, per_page: 20 });
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
        await fundingApi.update(editingItem.id, {
          name: form.name, description: form.description || undefined,
          provider: form.provider || undefined, program_type: form.program_type || undefined,
          eligibility_criteria: form.eligibility_criteria || undefined,
          max_amount: form.max_amount ? Number(form.max_amount) : undefined,
          application_url: form.application_url || undefined,
          deadline: form.deadline || undefined,
          contact_email: form.contact_email || undefined,
          contact_phone: form.contact_phone || undefined,
        });
        setEditingItem(null);
      } else {
        await fundingApi.create({
          name: form.name, description: form.description || undefined,
          provider: form.provider || undefined, program_type: form.program_type || undefined,
          eligibility_criteria: form.eligibility_criteria || undefined,
          max_amount: form.max_amount ? Number(form.max_amount) : undefined,
          application_url: form.application_url || undefined,
          deadline: form.deadline || undefined,
          contact_email: form.contact_email || undefined,
          contact_phone: form.contact_phone || undefined,
        });
        setShowAdd(false);
      }
      setForm(emptyForm);
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFormError(msg || "Failed to save program");
    } finally { setSaving(false); }
  };

  const openEdit = (e: React.MouseEvent, f: FundingProgram) => {
    e.stopPropagation();
    setEditingItem(f);
    setForm({
      name: f.name, description: f.description || "", provider: f.provider || "",
      program_type: f.program_type || "", eligibility_criteria: f.eligibility_criteria || "",
      max_amount: f.max_amount?.toString() || "", application_url: f.application_url || "",
      deadline: f.deadline ? f.deadline.slice(0, 10) : "",
      contact_email: f.contact_email || "", contact_phone: f.contact_phone || "",
    });
    setFormError("");
  };

  const handleArchive = async (id: string) => {
    try { await fundingApi.archive(id); setConfirmArchive(null); load(); } catch { /* handled */ }
  };

  const modalTitle = editingItem ? `Edit: ${editingItem.name}` : "Add Funding Program";
  const showModal = showAdd || editingItem !== null;
  const closeModal = () => { setShowAdd(false); setEditingItem(null); setForm(emptyForm); };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Funding Programs</h2>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{total} programs</span>
          {isAdmin && (
            <button onClick={() => { setFormError(""); setShowAdd(true); }}
              className="px-4 py-2 bg-pink-600 text-white text-sm font-medium rounded-lg hover:bg-pink-700 transition-colors">
              + Add Program
            </button>
          )}
        </div>
      </div>

      <input type="text" placeholder="Search funding programs..." value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2 mb-4 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />

      {loading ? <p className="text-gray-500">Loading...</p> : (
        <div className="space-y-3">
          {items.map((f) => (
            <div key={f.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-sm transition-shadow cursor-pointer relative group"
              onClick={() => navigate(`/funding/${f.id}`)}>
              {isAdmin && (
                <div className="absolute top-3 right-3 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => e.stopPropagation()}>
                  <button onClick={(e) => openEdit(e, f)}
                    className="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded">Edit</button>
                  <button onClick={() => setConfirmArchive(f.id)}
                    className="px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded">Delete</button>
                </div>
              )}
              <div className="flex justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{f.name}</h3>
                  {f.provider && <p className="text-sm text-gray-500">{f.provider}</p>}
                </div>
                <div className="text-right">
                  {f.max_amount && <p className="text-sm font-medium text-green-600">Up to ${f.max_amount.toLocaleString()}</p>}
                  {f.program_type && <span className="text-xs text-gray-500 capitalize">{f.program_type.replace("_", " ")}</span>}
                </div>
              </div>
              {f.description && <p className="text-sm text-gray-600 mt-2 line-clamp-2">{f.description}</p>}
              {f.eligibility_criteria && (
                <p className="text-xs text-gray-500 mt-2"><strong>Eligibility:</strong> {f.eligibility_criteria}</p>
              )}
              <div className="flex gap-3 mt-3">
                {f.application_url && (
                  <a href={f.application_url} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline">Apply →</a>
                )}
                {f.contact_email && (
                  <a href={`mailto:${f.contact_email}`} className="text-xs text-gray-500 hover:underline">Contact</a>
                )}
              </div>
            </div>
          ))}
          {items.length === 0 && <p className="text-center text-gray-500 py-8">No funding programs found.</p>}
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal open={showModal} onClose={closeModal} title={modalTitle}>
        {formError && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{formError}</div>}
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Program Name *</label>
            <input type="text" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
              <input type="text" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Program Type</label>
              <input type="text" value={form.program_type} onChange={(e) => setForm({ ...form, program_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" placeholder="grant, insurance, charity..." />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Eligibility Criteria</label>
            <textarea rows={2} value={form.eligibility_criteria}
              onChange={(e) => setForm({ ...form, eligibility_criteria: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Amount ($)</label>
              <input type="number" min={0} value={form.max_amount}
                onChange={(e) => setForm({ ...form, max_amount: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Deadline</label>
              <input type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Application URL</label>
            <input type="url" value={form.application_url}
              onChange={(e) => setForm({ ...form, application_url: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" placeholder="https://..." />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Contact Email</label>
              <input type="email" value={form.contact_email}
                onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Contact Phone</label>
              <input type="tel" value={form.contact_phone}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button type="submit" disabled={saving}
              className="px-4 py-2 bg-pink-600 text-white text-sm font-medium rounded-lg hover:bg-pink-700 disabled:opacity-50">
              {saving ? "Saving..." : editingItem ? "Save Changes" : "Add Program"}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      {confirmArchive && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setConfirmArchive(null)} />
          <div className="relative bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Delete Program?</h3>
            <p className="text-sm text-gray-600 mb-4">This program will be permanently removed.</p>
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

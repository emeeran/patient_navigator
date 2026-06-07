import { useState, useEffect, useCallback, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { fundingApi, adminApi } from "../api";
import type { FundingProgram } from "../types";
import Modal from "../components/Modal";
import Pagination from "../components/Pagination";
import { useAuth } from "../contexts/AuthContext";

const emptyForm = {
  name: "", description: "", provider: "", program_type: "",
  eligibility_criteria: "", max_amount: "", application_url: "",
  deadline: "", contact_email: "", contact_phone: "",
};

function deadlineStatus(deadline: string | null): { label: string; className: string } {
  if (!deadline) return { label: "No deadline", className: "text-gray-400" };
  const daysLeft = Math.ceil((new Date(deadline).getTime() - Date.now()) / 86400000);
  if (daysLeft < 0) return { label: "Expired", className: "bg-red-100 text-red-700" };
  if (daysLeft <= 30) return { label: `${daysLeft}d left`, className: "bg-amber-100 text-amber-700" };
  return { label: `${daysLeft}d left`, className: "bg-green-100 text-green-700" };
}

export default function FundingPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState<FundingProgram[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editingItem, setEditingItem] = useState<FundingProgram | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [confirmArchive, setConfirmArchive] = useState<string | null>(null);
  const [dedupMsg, setDedupMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [deduping, setDeduping] = useState(false);
  const [showDedupConfirm, setShowDedupConfirm] = useState(false);
  const [viewMode, setViewMode] = useState<"table" | "cards">("table");
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  useEffect(() => { setPage(1); }, [search]);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await fundingApi.list({ search: search || undefined, per_page: 20, is_active: true, page });
      setItems(data.items);
      setTotal(data.total);
    } catch { /* handled */ } finally { setLoading(false); }
  }, [search, page]);

  useEffect(() => { load(); }, [search, page]);

  // Auto-dismiss dedup message after 5s
  useEffect(() => {
    if (!dedupMsg) return;
    const t = setTimeout(() => setDedupMsg(null), 5000);
    return () => clearTimeout(t);
  }, [dedupMsg]);

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

  const handleDedup = async () => {
    setDeduping(true);
    setDedupMsg(null);
    try {
      const { data } = await adminApi.dedupFunding();
      if (data.removed === 0) {
        setDedupMsg({ type: "success", text: "No duplicates found. Directory is clean." });
      } else {
        setDedupMsg({ type: "success", text: `Removed ${data.removed} duplicate${data.removed !== 1 ? "s" : ""}. ${data.kept} unique programs remain.` });
      }
      load();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setDedupMsg({ type: "error", text: msg || "Dedup failed." });
    } finally { setDeduping(false); }
  };

  const modalTitle = editingItem ? `Edit: ${editingItem.name}` : "Add Funding Program";
  const showModal = showAdd || editingItem !== null;
  const closeModal = () => { setShowAdd(false); setEditingItem(null); setForm(emptyForm); };
  const colCount = isAdmin ? 7 : 6;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Funding Programs</h2>
        <div className="flex items-center gap-3">
          <div className="flex items-center border border-gray-300 rounded-lg overflow-hidden">
            <button onClick={() => setViewMode("table")}
              className={`px-3 py-1.5 text-xs font-medium ${viewMode === "table" ? "bg-pink-50 text-pink-700" : "text-gray-500 hover:bg-gray-50"}`}>
              Table
            </button>
            <button onClick={() => setViewMode("cards")}
              className={`px-3 py-1.5 text-xs font-medium ${viewMode === "cards" ? "bg-pink-50 text-pink-700" : "text-gray-500 hover:bg-gray-50"}`}>
              Cards
            </button>
          </div>
          <span className="text-sm text-gray-500">{total} programs</span>
          {isAdmin && (
            <button onClick={() => setShowDedupConfirm(true)} disabled={deduping}
              className="px-4 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-colors inline-flex items-center gap-1.5">
              {deduping && <span className="w-3.5 h-3.5 border-2 border-white/40 border-t-white rounded-full animate-spin" />}
              {deduping ? "Deduplicating…" : "🔧 Deduplicate"}
            </button>
          )}
          {isAdmin && (
            <button onClick={async () => {
              try {
                const { data } = await fundingApi.list({ per_page: 1000 });
                const headers = ["Name", "Provider", "Type", "Max Amount", "Deadline", "Contact Email", "Contact Phone"];
                const rows = data.items.map((f) => [f.name, f.provider, f.program_type, String(f.max_amount ?? ""), f.deadline ? new Date(f.deadline).toLocaleDateString() : "", f.contact_email, f.contact_phone]);
                const csv = [headers.join(","), ...rows.map((r) => r.map((v) => `"${(v ?? "").replace(/"/g, '""')}"`).join(","))].join("\n");
                const a = document.createElement("a");
                a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
                a.download = "funding.csv"; a.click();
              } catch { /* handled */ }
            }}
              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200">
              Export CSV
            </button>
          )}
          {isAdmin && (
            <button onClick={() => { setFormError(""); setShowAdd(true); }}
              className="px-4 py-2 bg-pink-600 text-white text-sm font-medium rounded-lg hover:bg-pink-700 transition-colors">
              + Add Program
            </button>
          )}
        </div>
      </div>

      {dedupMsg && (
        <div className={`p-3 text-sm rounded-lg mb-4 flex items-center justify-between ${dedupMsg.type === "success" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          <span>{dedupMsg.text}</span>
          <button onClick={() => setDedupMsg(null)} className="ml-3 opacity-60 hover:opacity-100 text-lg leading-none">&times;</button>
        </div>
      )}

      <input type="text" placeholder="Search funding programs…" value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2 mb-4 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />

      {loading ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Provider</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Max Amount</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Deadline</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Contact</th>
                {isAdmin && <th className="px-4 py-3"></th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: colCount }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-gray-100 rounded animate-pulse" style={{ width: `${60 + Math.random() * 40}%` }} />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : viewMode === "table" ? (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 min-w-[180px]">Name</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 min-w-[120px]">Provider</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Type</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Max Amount</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Deadline</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 min-w-[140px]">Contact</th>
                  {isAdmin && <th className="px-4 py-3 w-24"></th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((f) => (
                  <tr key={f.id} className="hover:bg-blue-50/50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/funding/${f.id}`)}>
                    <td className="px-4 py-3 font-medium text-gray-900">{f.name}</td>
                    <td className="px-4 py-3 text-gray-600">{f.provider || "—"}</td>
                    <td className="px-4 py-3">
                      {f.program_type ? (
                        <span className="px-2 py-0.5 bg-purple-50 text-purple-700 text-xs rounded-full capitalize font-medium">{f.program_type.replace("_", " ")}</span>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {f.max_amount ? `₹${f.max_amount.toLocaleString()}` : "—"}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {f.deadline ? (() => {
                        const s = deadlineStatus(f.deadline);
                        return <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${s.className}`}>
                          {new Date(f.deadline).toLocaleDateString()} ({s.label})
                        </span>;
                      })() : <span className="text-xs text-gray-400">No deadline</span>}
                    </td>
                    <td className="px-4 py-3">
                      {f.contact_email ? (
                        <a href={`mailto:${f.contact_email}`} onClick={(e) => e.stopPropagation()} className="text-xs text-blue-600 hover:underline">{f.contact_email}</a>
                      ) : f.contact_phone || "—"}
                    </td>
                    {isAdmin && (
                      <td className="px-4 py-3 space-x-2" onClick={(e) => e.stopPropagation()}>
                        <button onClick={(e) => openEdit(e, f)} className="text-xs text-blue-600 hover:underline">Edit</button>
                        <button onClick={() => setConfirmArchive(f.id)} className="text-xs text-red-600 hover:underline">Delete</button>
                      </td>
                    )}
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={colCount} className="text-center py-12">
                      <p className="text-gray-400 text-sm">No funding programs found.</p>
                      {search && <p className="text-gray-400 text-xs mt-1">Try a different search term.</p>}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {/* Card view */}
      {!loading && items.length > 0 && viewMode === "cards" && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((f) => (
            <div key={f.id}
              className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md cursor-pointer transition-shadow"
              onClick={() => navigate(`/funding/${f.id}`)}>
              <div className="flex items-start justify-between mb-1">
                <h3 className="font-semibold text-gray-900">{f.name}</h3>
                {f.program_type && (
                  <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full font-medium capitalize shrink-0">
                    {f.program_type}
                  </span>
                )}
              </div>
              {f.provider && <p className="text-sm text-gray-500 mb-2">{f.provider}</p>}
              <div className="flex items-center justify-between text-sm mt-3">
                <span className="text-gray-900 font-medium">
                  {f.max_amount ? `₹${Number(f.max_amount).toLocaleString()}` : "—"}
                </span>
                {f.deadline ? (() => {
                  const s = deadlineStatus(f.deadline);
                  return <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${s.className}`}>
                    {s.label}
                  </span>;
                })() : (
                  <span className="text-xs text-gray-400">No deadline</span>
                )}
              </div>
              {(f.contact_email || f.contact_phone) && (
                <p className="text-xs text-gray-400 mt-2 truncate">{f.contact_email || f.contact_phone}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && total > 0 && (
        <Pagination page={page} total={total} perPage={20} onChange={setPage} />
      )}

      {/* Add/Edit Modal */}
      <Modal open={showModal} onClose={closeModal} title={modalTitle}>
        {formError && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{formError}</div>}
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Program Name *</label>
            <input type="text" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
              <input type="text" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Program Type</label>
              <input type="text" value={form.program_type} onChange={(e) => setForm({ ...form, program_type: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" placeholder="grant, insurance, charity…" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Eligibility Criteria</label>
            <textarea rows={2} value={form.eligibility_criteria}
              onChange={(e) => setForm({ ...form, eligibility_criteria: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Amount (₹)</label>
              <input type="number" min={0} value={form.max_amount}
                onChange={(e) => setForm({ ...form, max_amount: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Deadline</label>
              <input type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Application URL</label>
            <input type="url" value={form.application_url}
              onChange={(e) => setForm({ ...form, application_url: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" placeholder="https://…" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Contact Email</label>
              <input type="email" value={form.contact_email}
                onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Contact Phone</label>
              <input type="tel" value={form.contact_phone}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none" />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button type="submit" disabled={saving}
              className="px-4 py-2 bg-pink-600 text-white text-sm font-medium rounded-lg hover:bg-pink-700 disabled:opacity-50">
              {saving ? "Saving…" : editingItem ? "Save Changes" : "Add Program"}
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

      {/* Dedup Confirmation */}
      {showDedupConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowDedupConfirm(false)} />
          <div className="relative bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-6">
            <h3 className="text-lg font-semibold mb-2">Deduplicate Funding Programs?</h3>
            <p className="text-sm text-gray-600 mb-4">
              This will find programs with the same <span className="font-medium text-gray-800">name</span> and keep only the most complete record. Duplicates will be soft-deleted.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowDedupConfirm(false)} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
              <button onClick={() => { setShowDedupConfirm(false); handleDedup(); }}
                className="px-4 py-2 bg-amber-500 text-white text-sm font-medium rounded-lg hover:bg-amber-600">
                Run Dedup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

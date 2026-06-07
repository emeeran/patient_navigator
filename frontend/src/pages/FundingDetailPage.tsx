import { useState, useEffect, type FormEvent } from "react";
import { useParams, Link } from "react-router-dom";
import { fundingApi } from "../api";
import type { FundingProgram } from "../types";

export default function FundingDetailPage() {
  const { fundingId } = useParams<{ fundingId: string }>();
  const [program, setProgram] = useState<FundingProgram | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "", description: "", provider: "", program_type: "",
    eligibility_criteria: "", max_amount: "", application_url: "",
    deadline: "", contact_email: "", contact_phone: "",
  });

  const loadProgram = async () => {
    setLoading(true);
    try {
      const { data } = await fundingApi.get(fundingId!);
      setProgram(data);
      setForm({
        name: data.name, description: data.description || "", provider: data.provider || "",
        program_type: data.program_type || "", eligibility_criteria: data.eligibility_criteria || "",
        max_amount: data.max_amount ? String(data.max_amount) : "",
        application_url: data.application_url || "", deadline: data.deadline ? data.deadline.split("T")[0] : "",
        contact_email: data.contact_email || "", contact_phone: data.contact_phone || "",
      });
    } catch { /* interceptor */ }
    setLoading(false);
  };

  useEffect(() => { loadProgram(); }, [fundingId]);

  const handleSave = async (e: FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await fundingApi.update(fundingId!, {
        name: form.name, description: form.description || undefined, provider: form.provider || undefined,
        program_type: form.program_type || undefined, eligibility_criteria: form.eligibility_criteria || undefined,
        max_amount: form.max_amount ? Number(form.max_amount) : undefined,
        application_url: form.application_url || undefined, deadline: form.deadline || undefined,
        contact_email: form.contact_email || undefined, contact_phone: form.contact_phone || undefined,
      });
      setEditing(false);
      loadProgram();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to save");
    } finally { setSaving(false); }
  };

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!program) return <p className="text-red-500">Program not found.</p>;

  return (
    <div className="space-y-6">
      <Link to="/funding" className="text-sm text-blue-600 hover:underline">← Back to Funding</Link>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{program.name}</h2>
            {program.provider && <p className="text-gray-500 mt-1">{program.provider}</p>}
            {program.max_amount && <p className="text-lg font-semibold text-green-600 mt-1">Up to ${program.max_amount.toLocaleString()}</p>}
          </div>
          {!editing && (
            <button onClick={() => setEditing(true)}
              className="px-4 py-2 bg-pink-600 text-white text-sm font-medium rounded-lg hover:bg-pink-700">
              Edit
            </button>
          )}
        </div>
      </div>

      {editing ? (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="text-lg font-semibold mb-4">Edit Program</h3>
          {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
              <input type="text" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
            </div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                <input type="text" value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Program Type</label>
                <input type="text" value={form.program_type} onChange={(e) => setForm({ ...form, program_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" /></div>
            </div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Eligibility</label>
              <textarea rows={2} value={form.eligibility_criteria} onChange={(e) => setForm({ ...form, eligibility_criteria: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Max Amount ($)</label>
                <input type="number" min={0} value={form.max_amount} onChange={(e) => setForm({ ...form, max_amount: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Deadline</label>
                <input type="date" value={form.deadline} onChange={(e) => setForm({ ...form, deadline: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" /></div>
            </div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Application URL</label>
              <input type="url" value={form.application_url} onChange={(e) => setForm({ ...form, application_url: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Contact Email</label>
                <input type="email" value={form.contact_email} onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" /></div>
              <div><label className="block text-sm font-medium text-gray-700 mb-1">Contact Phone</label>
                <input type="tel" value={form.contact_phone} onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" /></div>
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button type="button" onClick={() => setEditing(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
              <button type="submit" disabled={saving}
                className="px-4 py-2 bg-pink-600 text-white text-sm font-medium rounded-lg hover:bg-pink-700 disabled:opacity-50">
                {saving ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Program Details</h3>
            <dl className="space-y-2 text-sm">
              {program.description && <><dt className="text-gray-500">Description</dt><dd className="text-gray-900">{program.description}</dd></>}
              {program.eligibility_criteria && <><dt className="text-gray-500">Eligibility</dt><dd className="text-gray-900">{program.eligibility_criteria}</dd></>}
              {program.program_type && <><dt className="text-gray-500">Type</dt><dd className="text-gray-900 capitalize">{program.program_type.replace("_", " ")}</dd></>}
              {program.deadline && <><dt className="text-gray-500">Deadline</dt><dd className="text-gray-900">{new Date(program.deadline).toLocaleDateString()}</dd></>}
            </dl>
          </div>
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Contact & Application</h3>
            <dl className="space-y-2 text-sm">
              {program.application_url && <><dt className="text-gray-500">Apply</dt><dd><a href={program.application_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{program.application_url}</a></dd></>}
              {program.contact_email && <><dt className="text-gray-500">Email</dt><dd><a href={`mailto:${program.contact_email}`} className="text-blue-600 hover:underline">{program.contact_email}</a></dd></>}
              {program.contact_phone && <><dt className="text-gray-500">Phone</dt><dd className="text-gray-900">{program.contact_phone}</dd></>}
            </dl>
          </div>
        </div>
      )}
    </div>
  );
}

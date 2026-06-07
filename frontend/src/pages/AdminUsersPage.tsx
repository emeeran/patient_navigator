import { useState, useEffect } from "react";
import api from "../api/client";
import { useAuth } from "../contexts/AuthContext";

interface UserItem {
  id: string; email: string; full_name: string; phone: string | null;
  role: string; is_active: boolean; last_login_at: string | null;
}

export default function AdminUsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<UserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [editingUser, setEditingUser] = useState<UserItem | null>(null);
  const [editForm, setEditForm] = useState({ full_name: "", role: "", is_active: true, phone: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadUsers = async () => {
    setLoading(true);
    try {
      const { data } = await api.get("/admin/users", { params: { search: search || undefined, per_page: 100 } });
      setUsers(data.items ?? []);
      setTotal(data.total);
    } catch { /* interceptor */ }
    setLoading(false);
  };

  useEffect(() => { loadUsers(); }, [search]);

  const openEdit = (u: UserItem) => {
    setEditingUser(u);
    setEditForm({ full_name: u.full_name, role: u.role, is_active: u.is_active, phone: u.phone || "" });
    setError("");
  };

  const handleSave = async () => {
    if (!editingUser) return;
    setSaving(true);
    setError("");
    try {
      await api.patch(`/admin/users/${editingUser.id}`, {
        full_name: editForm.full_name || undefined,
        role: editForm.role !== editingUser.role ? editForm.role : undefined,
        is_active: editForm.is_active !== editingUser.is_active ? editForm.is_active : undefined,
        phone: editForm.phone || undefined,
      });
      setEditingUser(null);
      loadUsers();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to update user");
    } finally { setSaving(false); }
  };

  if (currentUser?.role !== "admin") {
    return <div className="p-8 text-center text-gray-500">Admin access required.</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">User Management</h2>
        <span className="text-sm text-gray-500">{total} users</span>
      </div>

      <input type="text" placeholder="Search users..." value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2 mb-4 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />

      {loading ? <p className="text-gray-500">Loading...</p> : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Name</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Email</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Role</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Status</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Last Login</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{u.full_name}</td>
                  <td className="px-4 py-3 text-gray-600">{u.email}</td>
                  <td className="px-4 py-3"><span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full capitalize">{u.role}</span></td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${u.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                      {u.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3">
                    <button onClick={() => openEdit(u)} className="text-xs text-blue-600 hover:underline">Edit</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit Modal */}
      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setEditingUser(null)} />
          <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Edit User: {editingUser.email}</h3>
              <button onClick={() => setEditingUser(null)} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div className="p-6 space-y-4">
              {error && <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input type="text" value={editForm.full_name}
                  onChange={(e) => setEditForm({ ...editForm, full_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select value={editForm.role} onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
                  <option value="admin">Admin</option>
                  <option value="navigator">Navigator</option>
                  <option value="clinician">Clinician</option>
                  <option value="volunteer">Volunteer</option>
                  <option value="patient">Patient</option>
                </select>
              </div>
              <div className="flex items-center gap-2">
                <input type="checkbox" checked={editForm.is_active}
                  onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })} className="rounded border-gray-300" />
                <label className="text-sm text-gray-700">Active</label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input type="tel" value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
              </div>
              {editForm.role !== editingUser.role && (
                <p className="text-xs text-amber-700 bg-amber-50 p-2 rounded">⚠️ Changing role will force the user to re-login.</p>
              )}
              <div className="flex justify-end gap-3 pt-2">
                <button onClick={() => setEditingUser(null)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
                <button onClick={handleSave} disabled={saving}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

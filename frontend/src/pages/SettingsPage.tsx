import { useState, useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { authApi } from "../api/auth";
import { adminApi } from "../api/index";
import type { UserListItem, SettingItem, ServiceHealthResponse } from "../types";

type Tab = "profile" | "password" | "users" | "configuration";

const TABS: { key: Tab; label: string; adminOnly: boolean }[] = [
  { key: "profile", label: "My Profile", adminOnly: false },
  { key: "password", label: "Change Password", adminOnly: false },
  { key: "users", label: "User Management", adminOnly: true },
  { key: "configuration", label: "Configuration", adminOnly: true },
];

const ROLES = ["admin", "navigator", "clinician", "volunteer", "patient"];

export default function SettingsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>("profile");

  const visibleTabs = TABS.filter((t) => !t.adminOnly || user?.role === "admin");
  const isAdmin = user?.role === "admin";

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Settings</h2>

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {visibleTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === tab.key
                ? "bg-blue-50 text-blue-700 border-b-2 border-blue-700"
                : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "profile" && <ProfileSection />}
      {activeTab === "password" && <PasswordSection />}
      {activeTab === "users" && isAdmin && <UserManagementSection />}
      {activeTab === "configuration" && isAdmin && <ConfigurationSection />}
    </div>
  );
}

// ── Profile Section ────────────────────────────────────

function ProfileSection() {
  const { user, updateUser } = useAuth();
  const [full_name, setFullName] = useState(user?.full_name || "");
  const [phone, setPhone] = useState(user?.phone || "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const { data } = await authApi.updateProfile({
        full_name: full_name || undefined,
        phone: phone || undefined,
      });
      updateUser(data);
      setMessage({ type: "success", text: "Profile updated successfully." });
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMessage({ type: "error", text: msg || "Failed to update profile." });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-lg">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h3>

      {message && (
        <div className={`p-3 text-sm rounded-lg mb-4 ${message.type === "success" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          {message.text}
        </div>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input type="email" value={user?.email || ""} disabled
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
          <input type="text" value={user?.role || ""} disabled
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-gray-50 text-gray-500 capitalize" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
          <input type="text" value={full_name} onChange={(e) => setFullName(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
          <input type="tel" value={phone} onChange={(e) => setPhone(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
        </div>
      </div>

      <button onClick={handleSave} disabled={saving}
        className="mt-6 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
        {saving ? "Saving..." : "Save Changes"}
      </button>
    </div>
  );
}

// ── Password Section ───────────────────────────────────

function PasswordSection() {
  const { logout } = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleSave = async () => {
    setError("");
    if (newPassword !== confirmPassword) {
      setError("New passwords do not match.");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setSaving(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      setSuccess(true);
      setTimeout(() => {
        logout();
        window.location.href = "/login";
      }, 2000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || "Failed to change password.");
    } finally {
      setSaving(false);
    }
  };

  if (success) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-lg">
        <div className="p-4 bg-green-50 text-green-700 rounded-lg">
          <p className="font-medium">Password changed successfully!</p>
          <p className="text-sm mt-1">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-lg">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Change Password</h3>

      {error && <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg mb-4">{error}</div>}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
          <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">New Password</label>
          <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
          <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
        </div>
        <p className="text-xs text-gray-500">
          Password must be at least 8 characters with uppercase, lowercase, digit, and special character.
        </p>
      </div>

      <button onClick={handleSave} disabled={saving}
        className="mt-6 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
        {saving ? "Changing..." : "Change Password"}
      </button>
    </div>
  );
}

// ── User Management Section ────────────────────────────

function UserManagementSection() {
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  // Edit modal state
  const [editingUser, setEditingUser] = useState<UserListItem | null>(null);
  const [editForm, setEditForm] = useState({ full_name: "", role: "", is_active: true, phone: "" });
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");

  // Create modal state
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ email: "", password: "", full_name: "", role: "navigator", phone: "" });
  const [createSaving, setCreateSaving] = useState(false);
  const [createError, setCreateError] = useState("");

  // Reset password modal state
  const [resettingUser, setResettingUser] = useState<UserListItem | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [confirmNewPassword, setConfirmNewPassword] = useState("");
  const [resetSaving, setResetSaving] = useState(false);
  const [resetError, setResetError] = useState("");
  const [resetSuccess, setResetSuccess] = useState(false);

  useEffect(() => { loadUsers(); }, [search]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const { data } = await adminApi.listUsers({ search: search || undefined, per_page: 100 });
      setUsers(data.items);
      setTotal(data.total);
    } catch { /* interceptor handles 401 */ }
    setLoading(false);
  };

  // ── Edit handlers ──
  const openEdit = (u: UserListItem) => {
    setEditingUser(u);
    setEditForm({ full_name: u.full_name, role: u.role, is_active: u.is_active, phone: u.phone || "" });
    setEditError("");
  };

  const handleEditSave = async () => {
    if (!editingUser) return;
    setEditSaving(true);
    setEditError("");
    try {
      await adminApi.updateUser(editingUser.id, {
        full_name: editForm.full_name || undefined,
        role: editForm.role !== editingUser.role ? editForm.role : undefined,
        is_active: editForm.is_active !== editingUser.is_active ? editForm.is_active : undefined,
        phone: editForm.phone || undefined,
      });
      setEditingUser(null);
      loadUsers();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setEditError(msg || "Failed to update user.");
    } finally {
      setEditSaving(false);
    }
  };

  // ── Create handlers ──
  const openCreate = () => {
    setCreateForm({ email: "", password: "", full_name: "", role: "navigator", phone: "" });
    setCreateError("");
    setShowCreate(true);
  };

  const handleCreate = async () => {
    setCreateSaving(true);
    setCreateError("");
    try {
      await adminApi.createUser(createForm);
      setShowCreate(false);
      loadUsers();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setCreateError(msg || "Failed to create user.");
    } finally {
      setCreateSaving(false);
    }
  };

  // ── Reset password handlers ──
  const openResetPassword = (u: UserListItem) => {
    setResettingUser(u);
    setNewPassword("");
    setConfirmNewPassword("");
    setResetError("");
    setResetSuccess(false);
    // Close edit modal if open
    setEditingUser(null);
  };

  const handleResetPassword = async () => {
    if (!resettingUser) return;
    setResetError("");
    if (newPassword !== confirmNewPassword) {
      setResetError("Passwords do not match.");
      return;
    }
    setResetSaving(true);
    try {
      await adminApi.resetUserPassword(resettingUser.id, newPassword);
      setResetSuccess(true);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setResetError(msg || "Failed to reset password.");
    } finally {
      setResetSaving(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-gray-500">{total} users</span>
        <button onClick={openCreate}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700">
          + Create User
        </button>
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
                  <td className="px-4 py-3">
                    <span className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full capitalize">{u.role}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${u.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                      {u.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="px-4 py-3 space-x-2">
                    <button onClick={() => openEdit(u)} className="text-xs text-blue-600 hover:underline">Edit</button>
                    <button onClick={() => openResetPassword(u)} className="text-xs text-amber-600 hover:underline">Reset PW</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Modal */}
      {showCreate && (
        <Modal onClose={() => setShowCreate(false)} title="Create New User">
          {createError && <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg mb-4">{createError}</div>}
          <div className="space-y-4">
            <InputField label="Full Name" value={createForm.full_name} onChange={(v) => setCreateForm({ ...createForm, full_name: v })} />
            <InputField label="Email" type="email" value={createForm.email} onChange={(v) => setCreateForm({ ...createForm, email: v })} />
            <InputField label="Password" type="password" value={createForm.password} onChange={(v) => setCreateForm({ ...createForm, password: v })} />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select value={createForm.role} onChange={(e) => setCreateForm({ ...createForm, role: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
                {ROLES.map((r) => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
              </select>
            </div>
            <InputField label="Phone (optional)" type="tel" value={createForm.phone} onChange={(v) => setCreateForm({ ...createForm, phone: v })} />
            <p className="text-xs text-gray-500">
              Password: min 8 chars, uppercase, lowercase, digit, special character.
            </p>
          </div>
          <div className="flex justify-end gap-3 pt-4 mt-4 border-t border-gray-200">
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button onClick={handleCreate} disabled={createSaving}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {createSaving ? "Creating..." : "Create User"}
            </button>
          </div>
        </Modal>
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <Modal onClose={() => setEditingUser(null)} title={`Edit User: ${editingUser.email}`}>
          {editError && <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg mb-4">{editError}</div>}
          <div className="space-y-4">
            <InputField label="Full Name" value={editForm.full_name} onChange={(v) => setEditForm({ ...editForm, full_name: v })} />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <select value={editForm.role} onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500">
                {ROLES.map((r) => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" checked={editForm.is_active}
                onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })} className="rounded border-gray-300" />
              <label className="text-sm text-gray-700">Active</label>
            </div>
            <InputField label="Phone" type="tel" value={editForm.phone} onChange={(v) => setEditForm({ ...editForm, phone: v })} />
            {editForm.role !== editingUser.role && (
              <p className="text-xs text-amber-700 bg-amber-50 p-2 rounded">
                ⚠️ Changing role will force the user to re-login.
              </p>
            )}
          </div>
          <div className="flex justify-end gap-3 pt-4 mt-4 border-t border-gray-200">
            <button onClick={() => setEditingUser(null)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button onClick={handleEditSave} disabled={editSaving}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {editSaving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </Modal>
      )}

      {/* Reset Password Modal */}
      {resettingUser && (
        <Modal onClose={() => setResettingUser(null)} title={`Reset Password: ${resettingUser.email}`}>
          {resetError && <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg mb-4">{resetError}</div>}
          {resetSuccess ? (
            <div className="p-3 bg-green-50 text-green-700 text-sm rounded-lg mb-4">
              Password reset successfully. The user will need to log in again.
            </div>
          ) : (
            <>
              <div className="space-y-4">
                <InputField label="New Password" type="password" value={newPassword} onChange={setNewPassword} />
                <InputField label="Confirm New Password" type="password" value={confirmNewPassword} onChange={setConfirmNewPassword} />
                <p className="text-xs text-gray-500">
                  Password: min 8 chars, uppercase, lowercase, digit, special character.
                </p>
              </div>
              <div className="flex justify-end gap-3 pt-4 mt-4 border-t border-gray-200">
                <button onClick={() => setResettingUser(null)} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
                <button onClick={handleResetPassword} disabled={resetSaving}
                  className="px-4 py-2 bg-amber-600 text-white text-sm font-medium rounded-lg hover:bg-amber-700 disabled:opacity-50">
                  {resetSaving ? "Resetting..." : "Reset Password"}
                </button>
              </div>
            </>
          )}
        </Modal>
      )}
    </div>
  );
}

// ── Configuration Section ──────────────────────────────

const LABEL_MAP: Record<string, string> = {
  APP_NAME: "Application Name",
  APP_VERSION: "Version",
  DEBUG: "Debug Mode",
  ENVIRONMENT: "Environment",
  ACCESS_TOKEN_EXPIRE_MINUTES: "Access Token Expiry (min)",
  REFRESH_TOKEN_EXPIRE_DAYS: "Refresh Token Expiry (days)",
  BCRYPT_ROUNDS: "Bcrypt Rounds",
  LOGIN_RATE_LIMIT_MAX_ATTEMPTS: "Rate Limit (max attempts)",
  LOGIN_RATE_LIMIT_WINDOW_SECONDS: "Rate Limit Window (sec)",
  JWT_ALGORITHM: "JWT Algorithm",
  JWT_SECRET_KEY: "JWT Secret Key",
  OLLAMA_BASE_URL: "Ollama Base URL",
  DEFAULT_MODEL: "Default AI Model",
  OLLAMA_TIMEOUT: "Ollama Timeout (sec)",
  UPLOAD_DIR: "Upload Directory",
  MAX_UPLOAD_SIZE_BYTES: "Max Upload Size (MB)",
  CORS_ORIGINS: "Allowed Origins",
  DATABASE_URL: "Database URL (async)",
  DATABASE_URL_SYNC: "Database URL (sync)",
  REDIS_URL: "Redis URL",
};

const GROUP_ORDER = ["app", "auth", "ai", "files", "cors", "infra"];

function ConfigurationSection() {
  const [allSettings, setAllSettings] = useState<SettingItem[]>([]);
  const [groups, setGroups] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [health, setHealth] = useState<ServiceHealthResponse | null>(null);
  const [editedValues, setEditedValues] = useState<Record<string, string>>({});
  const [savingGroup, setSavingGroup] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => { loadSettings(); }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const { data } = await adminApi.getSettings();
      setAllSettings(data.settings);
      setGroups(data.groups);
    } catch { /* interceptor */ }
    setLoading(false);

    // Load service health in parallel
    try {
      const { data } = await adminApi.getServiceHealth();
      setHealth(data);
    } catch { /* ok to fail */ }
  };

  const handleSaveGroup = async (groupName: string) => {
    setSavingGroup(groupName);
    setMessage(null);
    const groupSettings = allSettings.filter((s) => s.group_name === groupName && s.editable);
    const updates: Record<string, string> = {};
    for (const s of groupSettings) {
      if (editedValues[s.key] !== undefined) {
        // Convert MB back to bytes for file size
        if (s.key === "MAX_UPLOAD_SIZE_BYTES") {
          const mb = parseFloat(editedValues[s.key]);
          updates[s.key] = String(Math.round(mb * 1024 * 1024));
        } else {
          updates[s.key] = editedValues[s.key];
        }
      }
    }
    if (Object.keys(updates).length === 0) {
      setSavingGroup(null);
      return;
    }
    try {
      await adminApi.updateSettings(updates);
      // Clear edited values for saved keys
      setEditedValues((prev) => {
        const next = { ...prev };
        for (const k of Object.keys(updates)) delete next[k];
        return next;
      });
      setMessage({ type: "success", text: `Saved: ${Object.keys(updates).join(", ")}` });
      loadSettings();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setMessage({ type: "error", text: msg || "Failed to save settings." });
    } finally {
      setSavingGroup(null);
    }
  };

  const getDisplayValue = (s: SettingItem): string => {
    if (editedValues[s.key] !== undefined) return editedValues[s.key];
    if (s.key === "MAX_UPLOAD_SIZE_BYTES") {
      const bytes = parseInt(s.display_value, 10);
      return isNaN(bytes) ? s.display_value : String(Math.round(bytes / (1024 * 1024)));
    }
    return s.display_value;
  };

  if (loading) return <p className="text-gray-500">Loading configuration...</p>;

  return (
    <div className="space-y-6">
      {message && (
        <div className={`p-3 text-sm rounded-lg ${message.type === "success" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          {message.text}
        </div>
      )}

      {/* Service Health Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Service Health</h3>
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "PostgreSQL", status: health?.postgres },
            { label: "Redis", status: health?.redis },
            { label: "Ollama (AI)", status: health?.ollama },
          ].map((svc) => (
            <div key={svc.label} className="text-center">
              <p className="text-sm text-gray-500 mb-1">{svc.label}</p>
              <span className={`inline-block px-3 py-1 text-xs font-medium rounded-full ${
                svc.status === "ok" ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
              }`}>
                {svc.status === "ok" ? "✓ Connected" : "✗ Unreachable"}
              </span>
            </div>
          ))}
        </div>
        {health?.ollama_models && health.ollama_models.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-2">Available Models</p>
            <div className="flex flex-wrap gap-1">
              {health.ollama_models.map((m) => (
                <span key={m} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded-full">{m}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Settings Group Cards */}
      {GROUP_ORDER.map((groupKey) => {
        const groupSettings = allSettings.filter((s) => s.group_name === groupKey);
        if (groupSettings.length === 0) return null;
        const label = groups[groupKey] || groupKey;
        const hasEdits = groupSettings.some((s) => s.editable && editedValues[s.key] !== undefined);

        return (
          <div key={groupKey} className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{label}</h3>
            <div className="space-y-3">
              {groupSettings.map((s) => (
                <div key={s.key} className="flex items-center justify-between py-1.5 gap-4">
                  <label className="text-sm font-medium text-gray-700 whitespace-nowrap min-w-0">
                    {LABEL_MAP[s.key] || s.key}
                  </label>
                  {s.sensitive ? (
                    <span className="text-sm text-gray-400 font-mono truncate">{s.display_value}</span>
                  ) : s.editable ? (
                    s.key === "CORS_ORIGINS" ? (
                      <input
                        type="text"
                        value={getDisplayValue(s)}
                        onChange={(e) => setEditedValues((prev) => ({ ...prev, [s.key]: e.target.value }))}
                        className="flex-1 max-w-md px-3 py-1.5 border border-gray-300 rounded-lg text-sm text-right focus:ring-2 focus:ring-blue-500"
                      />
                    ) : s.type === "bool" ? (
                      <input
                        type="checkbox"
                        checked={getDisplayValue(s).toLowerCase() === "true"}
                        onChange={(e) => setEditedValues((prev) => ({ ...prev, [s.key]: String(e.target.checked) }))}
                        className="rounded border-gray-300"
                      />
                    ) : (
                      <input
                        type={s.type === "int" ? "number" : "text"}
                        value={getDisplayValue(s)}
                        onChange={(e) => setEditedValues((prev) => ({ ...prev, [s.key]: e.target.value }))}
                        className="w-48 px-3 py-1.5 border border-gray-300 rounded-lg text-sm text-right focus:ring-2 focus:ring-blue-500"
                      />
                    )
                  ) : (
                    <span className="text-sm text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg truncate max-w-md">
                      {s.display_value}
                    </span>
                  )}
                </div>
              ))}
            </div>
            {groupSettings.some((s) => s.editable) && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-400">
                  {groupSettings.some((s) => s.source === "database") && "• Customized"}
                </p>
                <button
                  onClick={() => handleSaveGroup(groupKey)}
                  disabled={savingGroup === groupKey || !hasEdits}
                  className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {savingGroup === groupKey ? "Saving..." : "Save Changes"}
                </button>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Shared UI Components ───────────────────────────────

function Modal({ children, onClose, title }: { children: React.ReactNode; onClose: () => void; title: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 sticky top-0 bg-white">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}

function InputField({ label, type = "text", value, onChange }: {
  label: string; type?: string; value: string; onChange: (v: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500" />
    </div>
  );
}

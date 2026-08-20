import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { adminApi, catalogApi } from "../api";
import type { UserCreatePayload, UserSummary, UserUpdatePayload } from "../api/types";
import { Badge, Button, Card, Empty, Spinner } from "../components/ui";

const ROLE_COLOR: Record<string, string> = {
  ADMIN: "red",
  GOVERNANCE: "purple",
  REVIEWER: "amber",
  AUTHOR: "blue",
  USER: "slate",
};

const EMPTY_FORM: UserCreatePayload = {
  username: "",
  display_name: "",
  email: "",
  department: "",
  title: "",
  role: "USER",
  password: "",
};

export default function Admin() {
  const queryClient = useQueryClient();
  const { data: users, isLoading } = useQuery({ queryKey: ["admin-users"], queryFn: adminApi.users });
  const { data: catalog } = useQuery({ queryKey: ["catalog"], queryFn: catalogApi.get });
  const roles = catalog?.roles ?? ["USER", "AUTHOR", "REVIEWER", "ADMIN", "GOVERNANCE"];

  const [editing, setEditing] = useState<UserSummary | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<UserCreatePayload>(EMPTY_FORM);
  const [formError, setFormError] = useState("");

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["admin-users"] });
  };

  const createMut = useMutation({
    mutationFn: adminApi.create,
    onSuccess: () => {
      setCreating(false);
      setForm(EMPTY_FORM);
      setFormError("");
      invalidate();
    },
    onError: (e) => setFormError(e instanceof Error ? e.message : "Failed to create user"),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UserUpdatePayload }) => adminApi.update(id, data),
    onSuccess: () => {
      setEditing(null);
      invalidate();
    },
    onError: (e) => setFormError(e instanceof Error ? e.message : "Failed to update user"),
  });

  const deleteMut = useMutation({
    mutationFn: adminApi.remove,
    onSuccess: invalidate,
    onError: (e) => {
      setFormError(e instanceof Error ? e.message : "Failed to delete user");
    },
  });

  const startCreate = () => {
    setForm(EMPTY_FORM);
    setFormError("");
    setCreating(true);
    setEditing(null);
  };

  const startEdit = (u: UserSummary) => {
    setEditing(u);
    setCreating(false);
    setFormError("");
    setForm({
      username: u.username,
      display_name: u.display_name,
      email: u.email,
      department: u.department,
      title: u.title,
      role: u.role,
      password: "",
    });
  };

  const submit = () => {
    setFormError("");
    if (editing) {
      const data: UserUpdatePayload = {
        display_name: form.display_name,
        email: form.email,
        role: form.role,
        department: form.department,
        title: form.title,
      };
      if (form.password) data.password = form.password;
      updateMut.mutate({ id: editing.id, data });
    } else {
      if (!form.username.trim()) {
        setFormError("Username is required");
        return;
      }
      createMut.mutate(form);
    }
  };

  const doDelete = (u: UserSummary) => {
    if (!window.confirm(`Delete user "${u.display_name || u.username}"? This cannot be undone.`)) return;
    setFormError("");
    deleteMut.mutate(u.id);
  };

  const set = <K extends keyof UserCreatePayload>(key: K, value: UserCreatePayload[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  if (isLoading) return <Spinner label="Loading users…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Administration</h1>
          <p className="text-sm text-slate-500">Manage platform users, roles, departments and titles.</p>
        </div>
        <Button onClick={startCreate}>+ Add user</Button>
      </div>

      {(creating || editing) && (
        <Card title={editing ? `Edit user — ${editing.username}` : "Add user"}>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {!editing && (
              <Field label="Username *">
                <input
                  className={inputCls}
                  value={form.username}
                  onChange={(e) => set("username", e.target.value)}
                  placeholder="jdoe"
                />
              </Field>
            )}
            <Field label="Display name">
              <input
                className={inputCls}
                value={form.display_name}
                onChange={(e) => set("display_name", e.target.value)}
                placeholder="Jane Doe"
              />
            </Field>
            <Field label="Email">
              <input
                className={inputCls}
                value={form.email}
                onChange={(e) => set("email", e.target.value)}
                placeholder="jane.doe@example.com"
              />
            </Field>
            <Field label="Role">
              <select className={inputCls} value={form.role} onChange={(e) => set("role", e.target.value)}>
                {roles.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Department">
              <input
                className={inputCls}
                value={form.department}
                onChange={(e) => set("department", e.target.value)}
                placeholder="e.g. DATA_ANALYTICS"
              />
            </Field>
            <Field label="Title">
              <input
                className={inputCls}
                value={form.title}
                onChange={(e) => set("title", e.target.value)}
                placeholder="e.g. Senior Analyst"
              />
            </Field>
            <Field label={editing ? "New password (leave blank to keep)" : "Password"}>
              <input
                type="password"
                className={inputCls}
                value={form.password ?? ""}
                onChange={(e) => set("password", e.target.value)}
              />
            </Field>
          </div>
          {formError && <p className="mt-3 rounded-md bg-red-50 p-2 text-xs text-red-600">{formError}</p>}
          <div className="mt-4 flex gap-2">
            <Button disabled={createMut.isPending || updateMut.isPending} onClick={submit}>
              {editing ? "Save changes" : "Create user"}
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setCreating(false);
                setEditing(null);
                setFormError("");
              }}
            >
              Cancel
            </Button>
          </div>
        </Card>
      )}

      {!users || users.length === 0 ? (
        <Card>
          <Empty message="No users found." />
        </Card>
      ) : (
        <Card title={`Users (${users.length})`}>
          {formError && !editing && !creating && (
            <p className="mb-3 rounded-md bg-red-50 p-2 text-xs text-red-600">{formError}</p>
          )}
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                <th className="py-2">User</th>
                <th className="py-2">Role</th>
                <th className="py-2">Department</th>
                <th className="py-2">Title</th>
                <th className="py-2">Status</th>
                <th className="py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u: UserSummary) => (
                <tr key={u.id} className="border-b border-slate-50 last:border-0">
                  <td className="py-2">
                    <div className="font-medium text-slate-800">{u.display_name || u.username}</div>
                    <div className="text-xs text-slate-400">
                      {u.username} · {u.email}
                    </div>
                  </td>
                  <td className="py-2">
                    <Badge color={(ROLE_COLOR[u.role] ?? "slate") as "slate"}>{u.role}</Badge>
                  </td>
                  <td className="py-2 text-slate-600">{u.department || "—"}</td>
                  <td className="py-2 text-slate-600">{u.title || "—"}</td>
                  <td className="py-2">
                    {u.is_active ? (
                      <Badge color="green">Active</Badge>
                    ) : (
                      <Badge color="slate">Inactive</Badge>
                    )}
                  </td>
                  <td className="py-2">
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" className="px-2 py-1 text-xs" onClick={() => startEdit(u)}>
                        Edit
                      </Button>
                      <Button variant="ghost" className="px-2 py-1 text-xs text-red-600" onClick={() => doDelete(u)}>
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm">
      <span className="mb-0.5 block text-xs font-semibold uppercase text-slate-400">{label}</span>
      {children}
    </label>
  );
}

const inputCls = "w-full rounded-md border border-slate-300 px-2 py-1.5 text-sm focus:border-brand-500 focus:outline-none";
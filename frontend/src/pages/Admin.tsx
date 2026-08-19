import { useQuery } from "@tanstack/react-query";
import { adminApi } from "../api";
import type { UserSummary } from "../api/types";
import { Badge, Card, Empty, Spinner } from "../components/ui";

const ROLE_COLOR: Record<string, string> = {
  ADMIN: "red",
  GOVERNANCE: "purple",
  REVIEWER: "amber",
  AUTHOR: "blue",
  USER: "slate",
};

export default function Admin() {
  const { data: users, isLoading } = useQuery({ queryKey: ["admin-users"], queryFn: adminApi.users });

  if (isLoading) return <Spinner label="Loading users…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Administration</h1>
        <p className="text-sm text-slate-500">Users and roles on the platform.</p>
      </div>

      {!users || users.length === 0 ? (
        <Card>
          <Empty message="No users found." />
        </Card>
      ) : (
        <Card title={`Users (${users.length})`}>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                <th className="py-2">User</th>
                <th className="py-2">Role</th>
                <th className="py-2">Department</th>
                <th className="py-2">Title</th>
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
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
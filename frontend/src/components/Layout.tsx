import { NavLink, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { governanceApi } from "../api";
import clsx from "clsx";

const NAV = [
  { to: "/", label: "Dashboard", icon: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" },
  { to: "/library", label: "Library", icon: "M4 5a2 2 0 012-2h12a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm4 0v14M16 9H12M16 13H12" },
  { to: "/builder", label: "Prompt Builder", icon: "M12 20h9m-9-4h5m-5-4h3m-9-6L7 5l4 4L5 15h5" },
  { to: "/assistant", label: "Assistant", icon: "M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z" },
  { to: "/workflows", label: "Workflows", icon: "M5 3a2 2 0 00-2 2v6h18V5a2 2 0 00-2-2H5zm-2 12a2 2 0 002 2h4v2a2 2 0 002 2h2a2 2 0 002-2v-2h4a2 2 0 002-2v-2H3v2z" },
  { to: "/analytics", label: "Analytics", icon: "M3 3v18h18M7 15l4-5 3 3 5-7" },
  { to: "/governance", label: "Governance", icon: "M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4zm0 6v6m0 0l3-3m-3 3l-3-3" },
  { to: "/audit", label: "Audit Log", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" },
  { to: "/admin", label: "Admin", icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" },
];

export function Layout() {
  const { data: summary } = useQuery({ queryKey: ["governance-summary"], queryFn: governanceApi.summary });

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-20 flex w-60 flex-col border-r border-slate-200 bg-white">
        <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-brand-600 font-bold text-white">P</div>
          <div>
            <div className="text-sm font-semibold text-slate-900">PromptHub</div>
            <div className="text-[11px] text-slate-400">Enterprise</div>
          </div>
        </div>
        <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
          {NAV.map((item) => {
            const badge = item.to === "/governance" ? summary?.high_risk ?? 0 : 0;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  clsx(
                    "group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium",
                    isActive ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                  )
                }
              >
                <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="1.6" viewBox="0 0 24 24">
                  <path d={item.icon} strokeLinecap="round" strokeLinejoin="round" />
                </svg>
                {item.label}
                {badge ? (
                  <span className="ml-auto rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-semibold text-red-600">
                    {badge}
                  </span>
                ) : null}
              </NavLink>
            );
          })}
        </nav>
        <div className="border-t border-slate-100 p-3">
          <div className="text-xs text-slate-400">Signed in as</div>
          <div className="text-sm font-medium text-slate-700">henry (Governance)</div>
        </div>
      </aside>
      <main className="ml-60 flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { auditApi, catalogApi } from "../api";
import { Badge, Card, Empty, Spinner } from "../components/ui";
import { formatTime } from "../lib/format";

const PAGE_SIZE = 50;

export default function Audit() {
  const [eventType, setEventType] = useState("");
  const [actor, setActor] = useState("");
  const [offset, setOffset] = useState(0);

  const { data, isLoading } = useQuery({
    queryKey: ["audit", { eventType, actor, offset }],
    queryFn: () => auditApi.list({ event_type: eventType || undefined, actor: actor || undefined, limit: PAGE_SIZE, offset }),
  });
  const { data: catalog } = useQuery({ queryKey: ["catalog"], queryFn: catalogApi.get });

  if (isLoading) return <Spinner label="Loading audit log…" />;

  const total = data?.total ?? 0;
  const canPrev = offset > 0;
  const canNext = offset + PAGE_SIZE < total;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Audit Log</h1>
        <p className="text-sm text-slate-500">Immutable record of every mutation on the platform.</p>
      </div>

      <div className="flex flex-wrap gap-2">
        <select className={inputCls} value={eventType} onChange={(e) => { setEventType(e.target.value); setOffset(0); }}>
          <option value="">All event types</option>
          {(catalog?.event_types ?? []).map((t) => <option key={t}>{t}</option>)}
        </select>
        <input
          className={`${inputCls} min-w-48`}
          placeholder="Filter by actor…"
          value={actor}
          onChange={(e) => { setActor(e.target.value); setOffset(0); }}
        />
        <span className="ml-auto self-center text-sm text-slate-500">{total} events</span>
      </div>

      {!data || data.items.length === 0 ? (
        <Card>
          <Empty message="No audit events match." />
        </Card>
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                <th className="py-2 pr-2">When</th>
                <th className="py-2 pr-2">Actor</th>
                <th className="py-2 pr-2">Event</th>
                <th className="py-2 pr-2">Entity</th>
                <th className="py-2">Details</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((e) => (
                <tr key={e.id} className="border-b border-slate-50 last:border-0">
                  <td className="whitespace-nowrap py-2 pr-2 text-xs text-slate-400">{formatTime(e.created_at)}</td>
                  <td className="py-2 pr-2 font-medium text-slate-700">{e.actor}</td>
                  <td className="py-2 pr-2">
                    <Badge color={e.event_type.includes("DELETE") || e.event_type.includes("DENY") ? "red" : "blue"}>
                      {e.event_type}
                    </Badge>
                  </td>
                  <td className="py-2 pr-2 text-xs text-slate-500">
                    <div>{e.entity_name || "—"}</div>
                    <div className="text-[10px] text-slate-400">
                      {e.entity_type} {e.entity_ref ? `· ${e.entity_ref}` : ""}
                    </div>
                  </td>
                  <td className="max-w-md py-2">
                    {Object.keys(e.details ?? {}).length > 0 ? (
                      <pre className="code text-[10px] text-slate-500">{JSON.stringify(e.details).slice(0, 160)}</pre>
                    ) : (
                      <span className="text-xs text-slate-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-3 flex items-center gap-2">
            <button disabled={!canPrev} onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))} className={pageBtn}>
              ← Prev
            </button>
            <span className="text-xs text-slate-500">
              {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
            </span>
            <button disabled={!canNext} onClick={() => setOffset((o) => o + PAGE_SIZE)} className={pageBtn}>
              Next →
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}

const pageBtn = "rounded-md border border-slate-300 px-3 py-1 text-sm disabled:opacity-40";
const inputCls = "rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none";
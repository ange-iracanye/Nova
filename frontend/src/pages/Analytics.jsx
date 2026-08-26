import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, BarChart3, CheckCircle2, Clock3, MessageSquare, RefreshCw, Users, UserRoundCheck, TrendingUp } from "lucide-react";
import { useNavigate } from "react-router-dom";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

function fmt(value) { return Number(value || 0).toLocaleString(); }
function date(value) { const d = new Date(value); return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString(undefined, { month: "short", day: "numeric" }); }
function userFromStorage() { try { const raw = localStorage.getItem("nova_user"); return raw ? JSON.parse(raw) : null; } catch { return null; } }

function Card({ children, className = "" }) {
  return <section className={`rounded-3xl border border-white/[.07] bg-gradient-to-br from-white/[.035] to-white/[.01] p-5 ${className}`}>{children}</section>;
}

function Stat({ icon, label, value, detail }) {
  return <Card><div className="flex items-start justify-between"><div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[.06] bg-white/[.03] text-sky-400">{icon}</div></div><div className="mt-5 text-3xl font-bold tracking-tight">{value}</div><div className="mt-1 text-sm text-slate-400">{label}</div>{detail && <div className="mt-2 text-xs text-slate-600">{detail}</div>}</Card>;
}

export default function Analytics() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/analytics?days=${days}`, { credentials: "include", headers: { Accept: "application/json" } });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || `Analytics request failed (HTTP ${response.status})`);
      setData(payload.analytics);
    } catch (err) {
      setError(err?.message || "Unable to load analytics.");
    } finally { setLoading(false); setRefreshing(false); }
  }, [days]);

  useEffect(() => { load(false); }, [load]);

  const daily = data?.daily || [];
  const maxEvents = useMemo(() => Math.max(1, ...daily.map(item => Number(item.events || 0))), [daily]);
  const eventTypes = data?.event_types || [];

  if (loading && !data) return <div className="flex min-h-screen items-center justify-center bg-[#070b12] text-white"><div className="text-center"><BarChart3 size={40} className="mx-auto animate-pulse text-sky-400"/><p className="mt-4 text-sm text-slate-500">Loading Nova analytics...</p></div></div>;

  return <main className="min-h-screen bg-[#070b12] text-white">
    <header className="sticky top-0 z-40 border-b border-white/[.06] bg-[#070b12]/85 backdrop-blur-2xl">
      <div className="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <button onClick={() => navigate("/dashboard")} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white"><ArrowLeft size={17}/> Dashboard</button>
        <div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-xl border border-sky-500/20 bg-sky-500/10 text-sky-400"><BarChart3 size={19}/></div><div><div className="text-sm font-semibold">Nova Analytics</div><div className="text-[10px] text-slate-600">Product usage</div></div></div>
        <div className="flex items-center gap-2"><select value={days} onChange={e => setDays(Number(e.target.value))} className="rounded-xl border border-white/[.07] bg-white/[.03] px-3 py-2 text-xs text-slate-300 outline-none"><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option></select><button onClick={() => load(true)} disabled={refreshing} className="rounded-xl border border-white/[.07] bg-white/[.03] p-2 text-slate-400 hover:text-white disabled:opacity-50"><RefreshCw size={16} className={refreshing ? "animate-spin" : ""}/></button></div>
      </div>
    </header>

    <div className="mx-auto max-w-[1500px] px-4 py-8 sm:px-6 lg:px-8">
      {error && <div className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/[.05] p-4 text-sm text-red-200">{error}</div>}
      <div className="mb-8"><div className="mb-2 inline-flex items-center gap-2 rounded-full border border-sky-400/15 bg-sky-400/[.06] px-3 py-1.5 text-xs font-medium text-sky-300"><TrendingUp size={13}/> NOVA USAGE</div><h1 className="text-3xl font-bold tracking-tight sm:text-4xl">Know how Nova is being used.</h1><p className="mt-2 text-sm text-slate-500">Privacy-conscious product metrics. No conversation text is stored by this analytics system.</p></div>

      <div className="mb-6 grid grid-cols-2 gap-3 xl:grid-cols-4">
        <Stat icon={<Users size={19}/>} label="Registered users" value={fmt(data?.registered_users)} detail="Accounts in Nova"/>
        <Stat icon={<UserRoundCheck size={19}/>} label="Active today" value={fmt(data?.active_today)} detail="Unique users, last 24h"/>
        <Stat icon={<Clock3 size={19}/>} label="Active this week" value={fmt(data?.active_week)} detail="Unique users, last 7d"/>
        <Stat icon={<MessageSquare size={19}/>} label="Chat requests" value={fmt(data?.chat_requests)} detail={`Last ${data?.days || days} days`}/>
      </div>

      <div className="mb-6 grid gap-6 xl:grid-cols-[2fr_1fr]">
        <Card><div className="mb-6 flex items-center justify-between"><div><h2 className="text-sm font-semibold">Daily activity</h2><p className="mt-1 text-xs text-slate-600">Events and unique active users</p></div><BarChart3 size={18} className="text-slate-600"/></div>{daily.length ? <div className="flex h-64 items-end gap-1 overflow-x-auto pb-6">{daily.map(item => <div key={item.date} className="group flex h-full min-w-[18px] flex-1 flex-col justify-end"><div className="relative flex-1"><div className="absolute bottom-0 left-0 right-0 rounded-t-md bg-sky-500/70 transition-all group-hover:bg-sky-400" style={{ height: `${Math.max(3, Number(item.events || 0) / maxEvents * 100)}%` }}/></div><div className="mt-2 text-center text-[9px] text-slate-700">{date(item.date)}</div></div>)}</div> : <div className="flex h-64 items-center justify-center text-sm text-slate-600">No activity recorded yet.</div>}</Card>

        <Card><div className="mb-6"><h2 className="text-sm font-semibold">Usage mix</h2><p className="mt-1 text-xs text-slate-600">Tracked product events</p></div><div className="space-y-4">{eventTypes.length ? eventTypes.map(item => { const max = Math.max(1, eventTypes[0]?.count || 1); return <div key={item.event}><div className="mb-2 flex justify-between text-xs"><span className="capitalize text-slate-400">{item.event}</span><span className="text-slate-600">{fmt(item.count)}</span></div><div className="h-2 rounded-full bg-white/[.05]"><div className="h-full rounded-full bg-sky-500/70" style={{ width: `${Math.max(3, item.count / max * 100)}%` }}/></div></div> }) : <div className="text-sm text-slate-600">No events yet.</div>}</div></Card>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card><div className="flex items-center gap-3"><CheckCircle2 size={18} className="text-emerald-400"/><div><div className="text-xs text-slate-600">Active this month</div><div className="mt-1 text-2xl font-bold">{fmt(data?.active_month)}</div></div></div></Card>
        <Card><div className="flex items-center gap-3"><UserRoundCheck size={18} className="text-violet-400"/><div><div className="text-xs text-slate-600">Returning users</div><div className="mt-1 text-2xl font-bold">{fmt(data?.returning_users_30d)}</div><div className="text-[11px] text-slate-700">Active on multiple days</div></div></div></Card>
        <Card><div className="flex items-center gap-3"><BarChart3 size={18} className="text-sky-400"/><div><div className="text-xs text-slate-600">Tracked events</div><div className="mt-1 text-2xl font-bold">{fmt(data?.events)}</div><div className="text-[11px] text-slate-700">Selected period</div></div></div></Card>
      </div>
    </div>
  </main>;
}

import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, BarChart3, CalendarDays, Clock3, Globe2, MessageSquare, RefreshCw, Route as RouteIcon, Sparkles, TrendingUp, Users, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";

const PRODUCTION_API_URL = "https://nova-api-i07q.onrender.com";
const API_URL = (import.meta.env.VITE_API_URL || PRODUCTION_API_URL).replace(/\/+$/, "");

function fmt(value) { return Number(value || 0).toLocaleString(); }
function date(value) { const d = new Date(value); return Number.isNaN(d.getTime()) ? "Never" : d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }); }
function time(value) { const d = new Date(value); return Number.isNaN(d.getTime()) ? "Never" : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); }
function userFromStorage() { try { const raw = localStorage.getItem("nova_user"); return raw ? JSON.parse(raw) : null; } catch { return null; } }

function Card({ children, className = "" }) { return <section className={`relative overflow-hidden rounded-[28px] border border-white/[.07] bg-gradient-to-br from-white/[.055] via-white/[.025] to-white/[.01] p-5 shadow-[0_22px_80px_rgba(0,0,0,.22)] backdrop-blur-xl ${className}`}>{children}</section>; }
function Stat({ icon, label, value, detail, accent = "sky" }) { const iconClass = { sky: "bg-sky-400/10 text-sky-300", emerald: "bg-emerald-400/10 text-emerald-300", violet: "bg-violet-400/10 text-violet-300", amber: "bg-amber-400/10 text-amber-300" }[accent] || "bg-sky-400/10 text-sky-300"; return <Card className="analytics-card"><div className={`flex h-10 w-10 items-center justify-center rounded-xl ${iconClass}`}>{icon}</div><div className="mt-5 text-3xl font-bold tracking-tight tabular-nums">{value}</div><div className="mt-1 text-sm text-slate-400">{label}</div>{detail && <div className="mt-2 text-xs text-slate-600">{detail}</div>}</Card>; }
function SectionTitle({ icon, title, subtitle }) { return <div className="mb-6 flex items-start gap-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/[.06] bg-white/[.03] text-sky-300">{icon}</div><div><h2 className="text-sm font-semibold">{title}</h2><p className="mt-1 text-xs leading-5 text-slate-600">{subtitle}</p></div></div>; }

function ActivityChart({ daily }) {
  const values = daily.map(item => Number(item.events || 0));
  const max = Math.max(1, ...values);
  const width = 900, height = 250, pad = 18;
  const points = values.map((value, index) => { const x = pad + (index / Math.max(1, values.length - 1)) * (width - pad * 2); const y = height - pad - (value / max) * (height - pad * 2); return `${x},${y}`; }).join(" ");
  const area = values.length ? `${pad},${height-pad} ${points} ${width-pad},${height-pad}` : "";
  return values.length ? <div className="overflow-x-auto"><svg viewBox={`0 0 ${width} ${height}`} className="h-[280px] min-w-[700px] w-full" role="img" aria-label="Daily analytics activity"><defs><linearGradient id="novaAnalyticsFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="rgb(56 189 248)" stopOpacity=".28"/><stop offset="1" stopColor="rgb(56 189 248)" stopOpacity="0"/></linearGradient></defs><polygon points={area} fill="url(#novaAnalyticsFill)"/><polyline points={points} fill="none" stroke="rgb(56 189 248)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke"/>{daily.map((item, index) => { const [x,y] = points.split(" ")[index].split(","); return <g key={item.date}><circle cx={x} cy={y} r="4" fill="rgb(56 189 248)" className="chart-dot"/><title>{date(item.date)} · {fmt(item.events)} events · {fmt(item.users)} users</title></g>; })}</svg><div className="mt-[-28px] flex justify-between px-2 text-[10px] text-slate-700"><span>{date(daily[0]?.date)}</span><span>{date(daily[Math.floor(daily.length/2)]?.date)}</span><span>{date(daily[daily.length-1]?.date)}</span></div></div> : <div className="flex h-[280px] items-center justify-center text-sm text-slate-600">Nova is waiting for its first analytics events.</div>;
}

function Donut({ items }) {
  const total = items.reduce((sum, item) => sum + Number(item.count || 0), 0);
  let cursor = 0;
  const colors = ["#38bdf8", "#a78bfa", "#34d399", "#fbbf24", "#fb7185", "#60a5fa"];
  const gradient = items.length ? items.map((item, index) => { const start = cursor / Math.max(1,total) * 360; cursor += Number(item.count || 0); const end = cursor / Math.max(1,total) * 360; return `${colors[index % colors.length]} ${start}deg ${end}deg`; }).join(", ") : "rgba(255,255,255,.07) 0 360deg";
  return <div className="flex flex-col items-center gap-5 sm:flex-row"><div className="relative h-44 w-44 shrink-0 rounded-full" style={{ background: `conic-gradient(${gradient})` }}><div className="absolute inset-[18px] flex flex-col items-center justify-center rounded-full bg-[#090d16]"><strong className="text-2xl">{fmt(total)}</strong><span className="text-[10px] text-slate-600">events</span></div></div><div className="w-full space-y-3">{items.slice(0,6).map((item,index)=><div key={item.event} className="flex items-center gap-3 text-xs"><span className="h-2.5 w-2.5 rounded-full" style={{background: colors[index % colors.length]}}/><span className="flex-1 capitalize text-slate-400">{item.event}</span><strong>{fmt(item.count)}</strong></div>)}</div></div>;
}

export default function Analytics() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const user = userFromStorage();

  const load = useCallback(async (silent = false) => {
    if (silent) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/analytics?days=${days}`, { credentials: "include", headers: { Accept: "application/json" } });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || `Analytics request failed (HTTP ${response.status})`);
      setData(payload.analytics || null);
    } catch (err) { setError(err?.message || "Unable to load analytics."); }
    finally { setLoading(false); setRefreshing(false); }
  }, [days]);

  useEffect(() => { load(false); }, [load]);

  const daily = data?.daily || [];
  const eventTypes = data?.event_types || [];
  const routes = data?.routes || [];
  const hourly = data?.hourly || [];
  const weekday = data?.weekday || [];
  const maxHour = Math.max(1, ...hourly);
  const maxRoute = Math.max(1, ...routes.map(item => Number(item.count || 0)));
  const busiestHour = data?.peak_hour;
  const busiestDay = data?.peak_day;
  const registered = Number(data?.registered_users || 0);
  const adoption = registered ? Math.round(Number(data?.active_month || 0) / registered * 100) : 0;
  const weekdayNames = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];
  const periodStart = daily[0]?.date;
  const periodEnd = daily[daily.length - 1]?.date;

  if (loading && !data) return <div className="flex min-h-screen items-center justify-center bg-[#070b12] text-white"><div className="text-center"><div className="mx-auto flex h-16 w-16 animate-pulse items-center justify-center rounded-2xl border border-sky-400/20 bg-sky-400/10 text-sky-300"><BarChart3 size={28}/></div><p className="mt-5 text-sm text-slate-500">Building the Nova command center...</p></div></div>;

  return <main className="analytics-shell min-h-screen overflow-hidden bg-[#070b12] text-white">
    <style>{`@keyframes novaFloat{0%,100%{transform:translate3d(0,0,0)}50%{transform:translate3d(0,-10px,0)}}@keyframes novaPulse{0%,100%{opacity:.35;transform:scale(.96)}50%{opacity:.75;transform:scale(1.04)}}@keyframes novaRise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}.analytics-card{animation:novaRise .55s cubic-bezier(.2,.7,.2,1) both}.analytics-card:nth-child(2){animation-delay:.06s}.analytics-card:nth-child(3){animation-delay:.12s}.analytics-card:nth-child(4){animation-delay:.18s}.chart-dot{animation:novaPulse 2.8s ease-in-out infinite}.nova-orb{animation:novaFloat 8s ease-in-out infinite}.nova-grid{background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(to bottom,black,transparent 80%)}`}</style>
    <div className="pointer-events-none fixed inset-0"><div className="nova-grid absolute inset-0"/><div className="nova-orb absolute -left-40 -top-40 h-[520px] w-[520px] rounded-full bg-sky-500/[.08] blur-[130px]"/><div className="nova-orb absolute right-[-180px] top-[35%] h-[500px] w-[500px] rounded-full bg-violet-500/[.07] blur-[140px]"/></div>
    <header className="sticky top-0 z-40 border-b border-white/[.06] bg-[#070b12]/80 backdrop-blur-2xl"><div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between px-4 sm:px-6 lg:px-8"><button onClick={() => navigate("/dashboard")} className="flex items-center gap-2 text-sm text-slate-400 transition hover:text-white"><ArrowLeft size={17}/> Dashboard</button><div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-xl border border-sky-400/20 bg-sky-400/10 text-sky-300"><Sparkles size={18}/></div><div><div className="text-sm font-semibold">Nova Command Center</div><div className="text-[10px] text-slate-600">Owner analytics</div></div></div><div className="flex items-center gap-2"><select value={days} onChange={e => setDays(Number(e.target.value))} className="rounded-xl border border-white/[.07] bg-white/[.04] px-3 py-2 text-xs text-slate-300 outline-none"><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option><option value="180">180 days</option><option value="365">365 days</option></select><button onClick={() => load(true)} disabled={refreshing} className="rounded-xl border border-white/[.07] bg-white/[.04] p-2 text-slate-400 transition hover:-rotate-12 hover:text-white disabled:opacity-50"><RefreshCw size={16} className={refreshing ? "animate-spin" : ""}/></button></div></div></header>

    <div className="relative z-10 mx-auto max-w-[1600px] px-4 py-8 sm:px-6 lg:px-8">
      {error && <div className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/[.05] p-4 text-sm text-red-200">{error}</div>}
      <Card className="mb-6 border-sky-400/10 bg-gradient-to-br from-sky-500/[.12] via-violet-500/[.04] to-transparent"><div className="relative flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between"><div><div className="mb-4 inline-flex items-center gap-2 rounded-full border border-sky-400/20 bg-sky-400/[.07] px-3 py-1.5 text-[11px] font-semibold tracking-[.18em] text-sky-300"><Zap size={12}/> OWNER MODE</div><h1 className="text-4xl font-black tracking-[-.04em] sm:text-6xl">See Nova <span className="text-sky-300">think, move, grow.</span></h1><p className="mt-4 max-w-3xl text-sm leading-6 text-slate-400">A live, privacy-conscious view of how the product is being used. Analytics stores anonymous user keys, event types, routes and timestamps, never conversation text.</p></div><div className="rounded-2xl border border-white/[.07] bg-black/20 px-5 py-4 text-right backdrop-blur-xl"><div className="text-[10px] uppercase tracking-[.16em] text-slate-600">Signed in as</div><div className="mt-1 text-sm font-semibold text-slate-200">{user?.email || "Owner"}</div><div className="mt-1 text-[10px] text-emerald-400">Owner access verified</div></div></div></Card>

      <div className="mb-6 grid grid-cols-2 gap-3 xl:grid-cols-4"><Stat icon={<Users size={19}/>} label="Registered users" value={fmt(data?.registered_users)} detail="All Nova accounts"/><Stat icon={<TrendingUp size={19}/>} label="Monthly active" value={fmt(data?.active_month)} detail={`${adoption}% of registered users`}/><Stat icon={<MessageSquare size={19}/>} label="Chat requests" value={fmt(data?.chat_requests)} detail={`Selected ${days}-day window`}/><Stat icon={<BarChart3 size={19}/>} label="Total events" value={fmt(data?.events)} detail={`${fmt(data?.avg_events_per_day)} events / day`}/></div>

      <div className="mb-6 grid gap-6 xl:grid-cols-[2fr_1fr]"><Card><SectionTitle icon={<TrendingUp size={18}/>} title="Activity pulse" subtitle={`Daily event volume · ${periodStart ? `${date(periodStart)} to ${date(periodEnd)}` : "No activity yet"}`}/><ActivityChart daily={daily}/></Card><Card><SectionTitle icon={<Zap size={18}/>} title="Usage fingerprint" subtitle="What users are doing inside Nova"/>{eventTypes.length ? <Donut items={eventTypes}/> : <div className="flex h-44 items-center justify-center text-sm text-slate-600">No events yet.</div>}</Card></div>

      <div className="mb-6 grid gap-6 lg:grid-cols-3"><Stat icon={<Clock3 size={19}/>} label="Active today" value={fmt(data?.active_today)} detail="Unique users · last 24h" accent="emerald"/><Stat icon={<CalendarDays size={19}/>} label="Returning users" value={fmt(data?.returning_users_30d)} detail="Active on multiple days" accent="violet"/><Stat icon={<Users size={19}/>} label="New active users" value={fmt(data?.new_active_users)} detail="First seen in selected window" accent="amber"/></div>

      <div className="mb-6 grid gap-6 xl:grid-cols-[1.4fr_1fr]"><Card><SectionTitle icon={<Clock3 size={18}/>} title="When Nova is busiest" subtitle="Event volume by UTC hour"/><div className="flex h-52 items-end gap-1">{hourly.map((value,index)=><div key={index} className="group flex h-full min-w-0 flex-1 flex-col justify-end"><div className="relative flex-1"><div className="absolute bottom-0 left-0 right-0 rounded-t-md bg-sky-400/60 transition-all duration-700 group-hover:bg-sky-300" style={{height:`${Math.max(value ? 3 : 0, value / maxHour * 100)}%`}}><span className="pointer-events-none absolute bottom-full left-1/2 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-white/10 bg-[#111827] px-2 py-1 text-[9px] text-slate-300 opacity-0 transition group-hover:opacity-100">{index}:00 · {fmt(value)}</span></div></div><div className="mt-2 text-center text-[8px] text-slate-700">{index % 3 === 0 ? index : ""}</div></div>)}</div>{busiestHour && <div className="mt-4 rounded-xl border border-sky-400/10 bg-sky-400/[.04] p-3 text-xs text-slate-500">Peak hour: <strong className="text-sky-300">{busiestHour.hour}:00 UTC</strong> with {fmt(busiestHour.events)} events.</div>}</Card>

      <Card><SectionTitle icon={<CalendarDays size={18}/>} title="Weekly rhythm" subtitle="Which days carry the most activity"/><div className="space-y-4">{weekday.map((value,index)=><div key={index}><div className="mb-1.5 flex justify-between text-xs"><span className="text-slate-500">{weekdayNames[index]}</span><strong>{fmt(value)}</strong></div><div className="h-2 overflow-hidden rounded-full bg-white/[.05]"><div className="h-full rounded-full bg-violet-400/70 transition-all duration-700" style={{width:`${Math.max(value ? 3 : 0, value / Math.max(1,...weekday) * 100)}%`}}/></div></div>)}</div>{busiestDay && <div className="mt-6 rounded-xl border border-violet-400/10 bg-violet-400/[.04] p-3 text-xs text-slate-500">Peak day: <strong className="text-violet-300">{date(busiestDay.date)}</strong> with {fmt(busiestDay.events)} events.</div>}</Card></div>

      <div className="mb-6 grid gap-6 xl:grid-cols-2"><Card><SectionTitle icon={<RouteIcon size={18}/>} title="Product surface map" subtitle="Routes generating the most activity"/><div className="space-y-4">{routes.length ? routes.map(item=><div key={item.path}><div className="mb-2 flex items-center gap-3 text-xs"><span className="min-w-0 flex-1 truncate font-mono text-slate-400">{item.path}</span><strong>{fmt(item.count)}</strong></div><div className="h-2 rounded-full bg-white/[.05]"><div className="h-full rounded-full bg-emerald-400/60 transition-all duration-700" style={{width:`${Math.max(3, Number(item.count || 0) / maxRoute * 100)}%`}}/></div></div>) : <div className="text-sm text-slate-600">No route activity yet.</div>}</div></Card>

      <Card><SectionTitle icon={<Globe2 size={18}/>} title="Operational snapshot" subtitle="Useful signals from the analytics stream"/><div className="grid grid-cols-2 gap-3">{[["Avg events / active user",fmt(data?.avg_events_per_active_user)],["Avg events / day",fmt(data?.avg_events_per_day)],["Active this week",fmt(data?.active_week)],["Returning 30d",fmt(data?.returning_users_30d)],["First tracked event",date(data?.first_event_at)],["Latest tracked event",time(data?.last_event_at)]].map(([label,value])=><div key={label} className="rounded-2xl border border-white/[.06] bg-white/[.02] p-4"><div className="text-[10px] uppercase tracking-[.12em] text-slate-700">{label}</div><div className="mt-2 text-sm font-semibold text-slate-300">{value}</div></div>)}</div><div className="mt-5 flex items-center gap-2 text-[11px] text-slate-600"><span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400"/> Privacy-conscious first-party analytics · generated {time(data?.generated_at)}</div></Card></div>

      <div className="rounded-2xl border border-white/[.05] bg-white/[.015] p-4 text-xs leading-5 text-slate-700">Analytics is intentionally limited to product-level telemetry. It does not expose message text, passwords, IP addresses or request bodies.</div>
    </div>
  </main>;
}

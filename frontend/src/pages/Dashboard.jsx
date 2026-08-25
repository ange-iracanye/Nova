import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity, AlertCircle, AlertTriangle, ArrowLeft, ArrowRight, Award,
  BarChart3, BookOpen, Brain, CheckCircle2, ChevronDown, ChevronRight,
  Clock3, Database, Flame, Gauge, GraduationCap, Info, Layers3,
  MessageSquare, Network, RefreshCw, Search, Sparkles, Target,
  TrendingDown, TrendingUp, Trophy, X, XCircle
} from "lucide-react";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const REFRESH_MS = 60000;

function num(value, fallback = 0) { const n = Number(value); return Number.isFinite(n) ? n : fallback; }
function integer(value) { return Math.max(0, Math.round(num(value))); }
function pct(value) { return Math.min(100, Math.max(0, num(value))); }
function text(value, fallback = "") { return value === null || value === undefined || String(value).trim() === "" ? fallback : String(value); }
function fmt(value) { return integer(value).toLocaleString(); }
function percent(value) { return `${Math.round(pct(value))}%`; }
function date(value) { if (!value) return "Recently"; const d = new Date(value); return Number.isNaN(d.getTime()) ? "Recently" : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }); }
function userFromStorage() { try { const raw = localStorage.getItem("nova_user"); return raw ? JSON.parse(raw) : null; } catch { return null; } }

async function request(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    return await fetch(url, { ...options, signal: options.signal || controller.signal, credentials: "include", headers: { Accept: "application/json", ...(options.headers || {}) } });
  } finally { clearTimeout(timer); }
}

function Ring({ value, label, tone = "#38bdf8", size = 170 }) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct(value) / 100) * circumference;
  return <div className="relative shrink-0" style={{ width: size, height: size }}>
    <svg width={size} height={size} className="-rotate-90"><circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="rgba(255,255,255,.06)" strokeWidth="10"/><circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={tone} strokeWidth="10" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} style={{ transition: "stroke-dashoffset .8s ease" }}/></svg>
    <div className="absolute inset-0 flex flex-col items-center justify-center"><strong className="text-3xl font-bold">{Math.round(pct(value))}%</strong><span className="mt-1 text-xs text-slate-500">{label}</span></div>
  </div>;
}

function Bar({ value, tone = "bg-sky-500" }) { return <div className="h-2 overflow-hidden rounded-full bg-white/[.055]"><div className={`h-full rounded-full ${tone} transition-all duration-700`} style={{ width: `${pct(value)}%` }}/></div>; }

function Card({ children, className = "" }) { return <section className={`rounded-3xl border border-white/[.07] bg-gradient-to-br from-white/[.035] to-white/[.01] p-5 shadow-[0_18px_60px_rgba(0,0,0,.14)] ${className}`}>{children}</section>; }
function Header({ icon, title, subtitle, action }) { return <div className="mb-5 flex items-start justify-between gap-4"><div className="flex items-start gap-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/[.06] bg-white/[.035] text-sky-400">{icon}</div><div><h2 className="text-sm font-semibold text-white">{title}</h2>{subtitle && <p className="mt-1 text-xs leading-5 text-slate-500">{subtitle}</p>}</div></div>{action}</div>; }
function Empty({ children }) { return <div className="rounded-2xl border border-dashed border-white/[.07] bg-white/[.012] p-7 text-center text-xs leading-5 text-slate-600">{children}</div>; }

export default function Dashboard() {
  const navigate = useNavigate();
  const mounted = useRef(true);
  const [data, setData] = useState(null);
  const [user, setUser] = useState(userFromStorage());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [online, setOnline] = useState(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState("recent");
  const [showAll, setShowAll] = useState(false);
  const [selected, setSelected] = useState(null);
  const [updated, setUpdated] = useState(null);

  useEffect(() => () => { mounted.current = false; }, []);
  useEffect(() => { const sync = () => setUser(userFromStorage()); window.addEventListener("storage", sync); window.addEventListener("nova-auth-changed", sync); return () => { window.removeEventListener("storage", sync); window.removeEventListener("nova-auth-changed", sync); }; }, []);

  const load = useCallback(async (silent = false) => {
    const current = userFromStorage();
    if (!current?.email) { navigate("/login", { replace: true }); return; }
    if (silent) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const response = await request(`${API_URL}/v1/dashboard`);
      if (!response.ok) throw new Error(`Dashboard request failed: HTTP ${response.status}`);
      const payload = await response.json();
      if (!mounted.current) return;
      setData(payload);
      setUser(current);
      setOnline(true);
      setUpdated(new Date());
    } catch (err) {
      if (!mounted.current || err?.name === "AbortError") return;
      setOnline(false);
      setError(err?.message || "Unable to load the dashboard.");
    } finally { if (mounted.current) { setLoading(false); setRefreshing(false); } }
  }, [navigate]);

  useEffect(() => { load(false); const id = setInterval(() => { if (document.visibilityState === "visible") load(true); }, REFRESH_MS); return () => clearInterval(id); }, [load]);

  const stats = data?.stats || {};
  const subjects = data?.subjects && typeof data.subjects === "object" ? data.subjects : {};
  const subjectEntries = useMemo(() => Object.entries(subjects).sort((a,b) => num(b[1]?.mastery) - num(a[1]?.mastery)), [subjects]);
  const conversations = Array.isArray(data?.recent_conversations) ? data.recent_conversations : [];
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let list = q ? conversations.filter(c => text(c.title).toLowerCase().includes(q) || text(c.last_message).toLowerCase().includes(q)) : [...conversations];
    if (sort === "messages") list.sort((a,b) => integer(b.message_count) - integer(a.message_count));
    else if (sort === "title") list.sort((a,b) => text(a.title).localeCompare(text(b.title)));
    else list.sort((a,b) => new Date(b.updated_at || b.created_at || 0) - new Date(a.updated_at || a.created_at || 0));
    return showAll ? list : list.slice(0, 5);
  }, [conversations, query, sort, showAll]);

  const correct = integer(stats.correct_answers);
  const wrong = integer(stats.wrong_answers);
  const totalAnswers = correct + wrong;
  const accuracy = totalAnswers ? (correct / totalAnswers) * 100 : 0;
  const mastery = pct(stats.overall_mastery);
  const confidence = pct(stats.average_confidence);
  const difficulty = data?.difficulty || {};
  const difficultyTotal = integer(difficulty.easy) + integer(difficulty.medium) + integer(difficulty.hard);
  const strongest = subjectEntries[0];
  const weakest = [...subjectEntries].sort((a,b) => num(a[1]?.mastery) - num(b[1]?.mastery))[0];

  if (loading && !data) return <div className="flex min-h-screen items-center justify-center bg-[#070b12] text-white"><div className="text-center"><Brain size={40} className="mx-auto animate-pulse text-sky-400"/><h1 className="mt-5 text-xl font-semibold">Loading your dashboard</h1><p className="mt-2 text-sm text-slate-600">Nova is gathering your learning data…</p></div></div>;

  return <main className="min-h-screen overflow-hidden bg-[#070b12] text-white">
    <div className="pointer-events-none fixed inset-0 overflow-hidden"><div className="absolute -top-48 left-1/3 h-[520px] w-[520px] rounded-full bg-sky-500/[.06] blur-[140px]"/><div className="absolute right-[-180px] top-1/3 h-[480px] w-[480px] rounded-full bg-violet-500/[.05] blur-[140px]"/></div>
    <header className="sticky top-0 z-40 border-b border-white/[.06] bg-[#070b12]/85 backdrop-blur-2xl"><div className="mx-auto flex h-16 max-w-[1500px] items-center justify-between px-4 sm:px-6 lg:px-8"><button onClick={() => navigate("/")} className="flex items-center gap-2 text-slate-400 transition hover:text-white"><ArrowLeft size={17}/><span className="hidden text-sm sm:block">Home</span></button><div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-xl border border-sky-500/20 bg-sky-500/10 text-sky-400"><Brain size={20}/></div><div className="hidden sm:block"><div className="text-sm font-semibold">Nova Dashboard</div><div className="text-[10px] text-slate-600">Learning intelligence</div></div></div><div className="flex items-center gap-2"><div className="hidden items-center gap-2 rounded-xl border border-white/[.06] bg-white/[.02] px-3 py-2 md:flex"><span className={`h-2 w-2 rounded-full ${online === true ? "bg-emerald-400" : online === false ? "bg-red-400" : "bg-slate-500"}`}/><span className="text-xs text-slate-500">{online === true ? "Backend online" : online === false ? "Backend offline" : "Checking backend"}</span></div><button onClick={() => load(true)} disabled={refreshing} className="flex items-center gap-2 rounded-xl border border-white/[.06] bg-white/[.02] px-3 py-2 text-sm text-slate-400 transition hover:bg-white/[.05] hover:text-white disabled:opacity-50"><RefreshCw size={15} className={refreshing ? "animate-spin" : ""}/> <span className="hidden sm:block">Refresh</span></button></div></div></header>

    <div className="relative z-10 mx-auto max-w-[1500px] px-4 py-8 sm:px-6 lg:px-8">
      {error && <div className="mb-6 flex items-center gap-3 rounded-2xl border border-red-500/20 bg-red-500/[.05] p-4 text-sm text-red-200"><AlertCircle size={18}/><span className="flex-1">{error}</span><button onClick={() => load(false)} className="font-semibold text-red-300">Retry</button></div>}

      <Card className="relative mb-6 overflow-hidden bg-gradient-to-br from-sky-500/[.1] via-white/[.02] to-transparent"><div className="absolute -right-20 -top-24 h-72 w-72 rounded-full bg-sky-500/[.08] blur-3xl"/><div className="relative flex flex-col justify-between gap-8 lg:flex-row lg:items-center"><div><div className="mb-4 inline-flex items-center gap-2 rounded-full border border-sky-400/15 bg-sky-400/[.06] px-3 py-1.5 text-xs font-medium text-sky-300"><Sparkles size={13}/> LEARNING OVERVIEW</div><h1 className="text-3xl font-bold tracking-tight sm:text-5xl">Welcome back, <span className="text-sky-400">{text(user?.name || user?.email, "Learner").split("@")[0]}</span></h1><p className="mt-3 max-w-2xl text-slate-400">Nova is tracking your progress, understanding, strengths and areas that still need work.</p>{updated && <p className="mt-4 text-xs text-slate-600">Updated {date(updated)}</p>}</div><div className="flex flex-col gap-3 sm:flex-row"><button onClick={() => navigate("/chat")} className="flex items-center justify-center gap-2 rounded-xl bg-sky-600 px-5 py-3 font-semibold transition hover:bg-sky-500">Continue learning <ArrowRight size={16}/></button><button onClick={() => navigate("/chat?new=true")} className="flex items-center justify-center gap-2 rounded-xl border border-white/[.08] bg-white/[.03] px-5 py-3 font-medium transition hover:bg-white/[.06]"><Sparkles size={16}/> New session</button></div></div></Card>

      <div className="mb-6 grid grid-cols-2 gap-3 xl:grid-cols-4"><Stat icon={<Target size={19}/>} label="Overall mastery" value={percent(mastery)} detail={mastery >= 75 ? "Strong" : mastery >= 50 ? "Developing" : "Getting started"}/><Stat icon={<CheckCircle2 size={19}/>} label="Accuracy" value={percent(accuracy)} detail={`${fmt(correct)} correct answers`}/><Stat icon={<Brain size={19}/>} label="Confidence" value={percent(confidence)} detail={`${fmt(stats.understanding_attempts)} checks`}/><Stat icon={<MessageSquare size={19}/>} label="Questions" value={fmt(stats.questions)} detail={`${fmt(stats.conversation_count)} conversations`}/></div>

      <div className="mb-6 grid gap-6 xl:grid-cols-3"><Card className="xl:col-span-2"><Header icon={<Gauge size={19}/>} title="Learning performance" subtitle="A high-level view of your current progress."/><div className="grid items-center gap-8 md:grid-cols-[200px_1fr]"><Ring value={mastery} label="Mastery"/><div className="space-y-5"><div><div className="mb-2 flex justify-between text-sm"><span className="text-slate-400">Overall understanding</span><strong>{percent(mastery)}</strong></div><Bar value={mastery}/></div><div className="grid grid-cols-2 gap-3"><Metric label="Correct" value={fmt(correct)} icon={<CheckCircle2 size={15}/>}/><Metric label="Wrong" value={fmt(wrong)} icon={<XCircle size={15}/>}/><Metric label="Attempts" value={fmt(stats.study_attempts)} icon={<Activity size={15}/>}/><Metric label="Topics" value={fmt(stats.total_topics)} icon={<Layers3 size={15}/>}/></div><div className="flex gap-3 rounded-xl border border-white/[.05] bg-white/[.02] p-4 text-xs leading-5 text-slate-500"><Info size={16} className="shrink-0"/> Mastery is an estimate based on Nova’s recorded learning data.</div></div></div></Card><Card><Header icon={<Brain size={19}/>} title="Understanding" subtitle="Nova’s current confidence estimate."/><div className="flex justify-center py-3"><Ring value={confidence} label="Confidence" tone="#a78bfa"/></div><div className="mt-3 grid grid-cols-2 gap-3"><Metric label="Checks" value={fmt(stats.understanding_attempts)}/><Metric label="Memory" value={fmt(stats.memory_count)}/></div><button onClick={() => navigate("/chat")} className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl border border-violet-500/20 bg-violet-500/[.05] px-4 py-3 text-sm font-medium text-violet-300 hover:bg-violet-500/[.1]">Practice with Nova <ArrowRight size={15}/></button></Card></div>

      <div className="mb-6 grid gap-6 xl:grid-cols-3"><Card className="xl:col-span-2"><Header icon={<BookOpen size={19}/>} title="Subjects" subtitle="Your strongest and weakest areas at a glance." action={<span className="rounded-lg border border-white/[.04] bg-white/[.025] px-2 py-1 text-[11px] text-slate-600">{subjectEntries.length} tracked</span>}/>{subjectEntries.length ? <div className="space-y-3">{subjectEntries.slice(0,8).map(([name, item]) => <button key={name} onClick={() => setSelected(selected === name ? null : name)} className="w-full rounded-xl border border-white/[.045] bg-white/[.018] p-4 text-left transition hover:border-white/[.09] hover:bg-white/[.035]"><div className="flex items-center gap-4"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-white/[.05] bg-white/[.04] text-slate-500"><BookOpen size={17}/></div><div className="min-w-0 flex-1"><div className="mb-2 flex justify-between gap-4"><span className="truncate text-sm font-medium">{name}</span><strong className="text-xs text-sky-400">{percent(item?.mastery)}</strong></div><Bar value={item?.mastery} tone={num(item?.mastery) >= 75 ? "bg-emerald-500" : num(item?.mastery) >= 50 ? "bg-sky-500" : "bg-orange-500"}/></div><ChevronRight size={16} className={`text-slate-700 transition ${selected === name ? "rotate-90" : ""}`}/></div>{selected === name && <div className="mt-4 grid grid-cols-3 gap-2 border-t border-white/[.05] pt-4"><Metric label="Topics" value={fmt(item?.topics_count)}/><Metric label="Correct" value={fmt(item?.correct_answers)}/><Metric label="Wrong" value={fmt(item?.wrong_answers)}/></div>}</button>)}</div> : <Empty>Start a learning session and Nova will begin building your subject profile.</Empty>}</Card><Card><Header icon={<TrendingUp size={19}/>} title="Performance snapshot" subtitle="Where your current data points."/>{strongest ? <div className="space-y-4"><Highlight icon={<Trophy size={17}/>} title="Strongest subject" name={strongest[0]} value={strongest[1]?.mastery} positive/><Highlight icon={<TrendingDown size={17}/>} title="Needs attention" name={weakest?.[0]} value={weakest?.[1]?.mastery}/></div> : <Empty>More learning activity is needed before Nova can identify patterns.</Empty>}</Card></div>

      <div className="mb-6 grid gap-6 lg:grid-cols-2"><Insight icon={<Award size={19}/>} title="Strengths" text="Areas where your performance is strongest." items={data?.strengths}/><Insight icon={<AlertTriangle size={19}/>} title="Needs attention" text="Topics where more practice could help." items={data?.weaknesses}/></div>

      <div className="mb-6 grid gap-6 lg:grid-cols-2"><Card><Header icon={<BarChart3 size={19}/>} title="Difficulty profile" subtitle="How your learning interactions have been classified."/>{difficultyTotal ? <div className="space-y-5"><Difficulty label="Easy" value={difficulty.easy} total={difficultyTotal} tone="bg-emerald-500"/><Difficulty label="Medium" value={difficulty.medium} total={difficultyTotal} tone="bg-orange-400"/><Difficulty label="Hard" value={difficulty.hard} total={difficultyTotal} tone="bg-red-500"/></div> : <Empty>No difficulty data yet.</Empty>}</Card><Card><Header icon={<Network size={19}/>} title="Knowledge map" subtitle="Nova’s current view of your subject knowledge."/>{Array.isArray(data?.knowledge_subjects) && data.knowledge_subjects.length ? <div className="space-y-4">{data.knowledge_subjects.slice(0,8).map((item, i) => <div key={item.id || i}><div className="mb-2 flex justify-between text-sm"><span>{text(item.name, "Subject")}</span><span className="text-xs text-slate-500">{percent(item.confidence)}</span></div><Bar value={item.confidence}/><div className="mt-1 text-[10px] text-slate-700">{fmt(item.topics)} topics · {fmt(item.attempts)} attempts</div></div>)}</div> : <Empty>Keep learning and Nova will gradually build this map.</Empty>}</Card></div>

      <Card className="mb-6"><Header icon={<Clock3 size={19}/>} title="Current learning session" subtitle="What Nova currently has in context."/><div className="grid grid-cols-2 gap-3 md:grid-cols-4"><Metric label="Subject" value={text(data?.session?.subject, "None")} icon={<BookOpen size={15}/>}/><Metric label="Topic" value={text(data?.session?.topic, "None")} icon={<Target size={15}/>}/><Metric label="Mode" value={text(data?.session?.mode, "None")} icon={<GraduationCap size={15}/>}/><Metric label="Score" value={text(data?.session?.score, "0")} icon={<Trophy size={15}/>}/></div></Card>

      <Card className="mb-6"><div className="mb-5 flex flex-col justify-between gap-4 lg:flex-row lg:items-center"><Header icon={<MessageSquare size={19}/>} title="Recent conversations" subtitle="Jump back into previous learning sessions." noMargin/><div className="flex flex-col gap-2 sm:flex-row"><div className="relative"><Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600"/><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search conversations…" className="w-full rounded-xl border border-white/[.07] bg-white/[.025] py-2.5 pl-9 pr-3 text-sm text-white outline-none placeholder:text-slate-600 focus:border-sky-500/40 sm:w-64"/></div><div className="relative"><select value={sort} onChange={e => setSort(e.target.value)} className="w-full appearance-none rounded-xl border border-white/[.07] bg-[#0b1018] py-2.5 pl-3 pr-9 text-sm text-slate-400 outline-none sm:w-auto"><option value="recent">Most recent</option><option value="messages">Most messages</option><option value="title">Title</option></select><ChevronDown size={14} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-600"/></div></div></div>{filtered.length ? <div className="space-y-2">{filtered.map(item => <button key={item.id} onClick={() => { try { localStorage.setItem("nova_current_conversation", String(item.id)); } catch {} navigate("/chat"); }} className="group w-full rounded-xl border border-white/[.04] bg-white/[.015] p-4 text-left transition hover:border-white/[.08] hover:bg-white/[.035]"><div className="flex items-center gap-3"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-violet-500/10 bg-violet-500/10 text-violet-400"><MessageSquare size={17}/></div><div className="min-w-0 flex-1"><div className="flex justify-between gap-4"><span className="truncate text-sm font-medium">{text(item.title, "New conversation")}</span><span className="hidden text-[10px] text-slate-700 sm:block">{date(item.updated_at || item.created_at)}</span></div><p className="mt-1 truncate text-xs text-slate-600">{text(item.last_message, "No messages yet")}</p></div><ChevronRight size={16} className="text-slate-700 transition group-hover:translate-x-1 group-hover:text-slate-400"/></div></button>)}{conversations.length > 5 && <button onClick={() => setShowAll(v => !v)} className="w-full rounded-xl border border-white/[.05] py-3 text-sm text-slate-500 transition hover:bg-white/[.03] hover:text-white">{showAll ? "Show less" : `Show all conversations (${conversations.length})`}</button>}</div> : <Empty>{query ? "No matching conversations." : "No conversations yet. Start a learning session with Nova."}</Empty>}</Card>

      <div className="grid grid-cols-2 gap-3 pb-10 md:grid-cols-4"><Footer icon={<Database size={17}/>} label="Memory" value={fmt(stats.memory_count)}/><Footer icon={<MessageSquare size={17}/>} label="Conversations" value={fmt(stats.conversation_count)}/><Footer icon={<Brain size={17}/>} label="Understanding checks" value={fmt(stats.understanding_attempts)}/><Footer icon={<Flame size={17}/>} label="Study attempts" value={fmt(stats.study_attempts)}/></div>
    </div>
  </main>;
}

function Stat({ icon, label, value, detail }) { return <div className="rounded-2xl border border-white/[.06] bg-white/[.02] p-4 transition hover:bg-white/[.035]"><div className="flex h-9 w-9 items-center justify-center rounded-xl border border-sky-500/10 bg-sky-500/10 text-sky-400">{icon}</div><div className="mt-4 text-2xl font-bold tracking-tight sm:text-3xl">{value}</div><div className="mt-1 text-xs text-slate-500">{label}</div><div className="mt-2 truncate text-[11px] text-slate-700">{detail}</div></div>; }
function Metric({ icon, label, value }) { return <div className="rounded-xl border border-white/[.05] bg-white/[.02] p-3"><div className="mb-2 flex items-center gap-2 text-slate-600">{icon}<span className="text-[11px]">{label}</span></div><div className="truncate text-sm font-semibold" title={String(value)}>{value}</div></div>; }
function Highlight({ icon, title, name, value, positive = false }) { return <div className={`rounded-2xl border p-4 ${positive ? "border-emerald-500/10 bg-emerald-500/[.035]" : "border-orange-500/10 bg-orange-500/[.035]"}`}><div className={`mb-3 flex items-center gap-2 text-xs ${positive ? "text-emerald-400" : "text-orange-400"}`}>{icon}{title}</div><div className="flex justify-between gap-3"><span className="truncate font-medium">{name || "None"}</span><strong className={positive ? "text-emerald-400" : "text-orange-400"}>{percent(value)}</strong></div></div>; }
function Insight({ icon, title, text: subtitle, items }) { const list = Array.isArray(items) ? items.filter(Boolean) : []; return <Card><Header icon={icon} title={title} subtitle={subtitle}/>{list.length ? <div className="flex flex-wrap gap-2">{list.map((item, i) => <span key={`${item}-${i}`} className="rounded-xl border border-sky-500/10 bg-sky-500/[.05] px-3 py-2 text-xs text-sky-300">• {item}</span>)}</div> : <Empty>Nova has not identified clear patterns yet.</Empty>}</Card>; }
function Difficulty({ label, value, total, tone }) { const share = total ? (num(value) / total) * 100 : 0; return <div><div className="mb-2 flex justify-between text-sm"><span className="text-slate-300">{label}</span><span className="text-xs text-slate-500">{fmt(value)} · {percent(share)}</span></div><Bar value={share} tone={tone}/></div>; }
function Footer({ icon, label, value }) { return <div className="flex items-center gap-3 rounded-xl border border-white/[.05] bg-white/[.018] p-4"><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/[.035] text-slate-600">{icon}</div><div><div className="text-sm font-semibold">{value}</div><div className="mt-0.5 text-[10px] text-slate-700">{label}</div></div></div>; }

import { useCallback, useEffect, useState } from "react";
import { Activity, ArrowRight, BookOpen, Brain, CheckCircle2, RefreshCw, Sparkles, Target, TrendingUp, XCircle, Zap } from "lucide-react";
import { useNavigate } from "react-router-dom";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

function getUser() {
  try {
    const raw = localStorage.getItem("nova_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function number(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.max(0, Math.round(n)) : 0;
}

function percent(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.max(0, Math.min(100, Math.round(n))) : 0;
}

function errorMessage(error) {
  const text = String(error?.message || "");
  if (/401/.test(text)) return "Your session has expired. Please sign in again.";
  if (/403/.test(text)) return "You do not have permission to view this dashboard.";
  if (/Failed to fetch|NetworkError|Load failed/i.test(text)) return "Nova could not reach the backend.";
  return text || "Dashboard unavailable.";
}

export default function DashboardProduction() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async (silent = false) => {
    const user = getUser();
    if (!user?.email) {
      navigate("/login", { replace: true });
      return;
    }
    if (silent) setRefreshing(true); else setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/v1/dashboard`, { cache: "no-store" });
      if (!response.ok) {
        let detail = "";
        try {
          const body = await response.json();
          detail = body?.error?.message || body?.detail || body?.message || "";
        } catch { /* ignore */ }
        throw new Error(detail || `Dashboard request failed: HTTP ${response.status}`);
      }
      const result = await response.json();
      if (!result?.success) throw new Error("Dashboard returned an invalid response.");
      setData(result);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [navigate]);

  useEffect(() => { load(); }, [load]);

  const stats = data?.stats || {};
  const subjects = data?.subjects && typeof data.subjects === "object" ? Object.values(data.subjects) : [];
  const recent = Array.isArray(data?.recent_conversations) ? data.recent_conversations : [];
  const strengths = Array.isArray(data?.strengths) ? data.strengths : [];
  const weaknesses = Array.isArray(data?.weaknesses) ? data.weaknesses : [];

  if (loading) {
    return <main className="flex min-h-screen items-center justify-center bg-[#020617] text-slate-300"><div className="flex items-center gap-3 text-sm"><RefreshCw size={17} className="animate-spin text-cyan-300" />Loading your dashboard...</div></main>;
  }

  return (
    <main className="min-h-screen bg-[#020617] text-slate-100">
      <header className="border-b border-white/[.07] bg-slate-950/70 px-6 py-5 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div><div className="flex items-center gap-2 text-cyan-300"><Sparkles size={18} /><span className="text-xs font-bold uppercase tracking-[.18em]">Nova Dashboard</span></div><h1 className="mt-2 text-3xl font-semibold tracking-tight">Your learning at a glance.</h1><p className="mt-1 text-sm text-slate-500">Progress, mastery and recent activity from your Nova account.</p></div>
          <div className="flex gap-2"><button type="button" onClick={() => load(true)} disabled={refreshing} className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[.04] px-3 py-2 text-sm text-slate-300 hover:bg-white/[.08] disabled:opacity-50"><RefreshCw size={15} className={refreshing ? "animate-spin" : ""} />Refresh</button><button type="button" onClick={() => navigate("/chat")} className="flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-cyan-300">Open chat <ArrowRight size={15} /></button></div>
        </div>
      </header>

      {error && <div className="mx-auto mt-5 flex max-w-7xl items-center gap-3 rounded-xl border border-red-400/20 bg-red-500/[.06] px-4 py-3 text-sm text-red-200"><XCircle size={17} />{error}<button type="button" onClick={() => load(false)} className="ml-auto underline underline-offset-4">Retry</button></div>}

      <div className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[[Brain, "Questions", number(stats.questions)], [Target, "Overall mastery", `${percent(stats.overall_mastery)}%`], [Activity, "Study attempts", number(stats.study_attempts)], [Zap, "Conversations", number(stats.conversation_count)]].map(([Icon, label, value]) => <article key={label} className="rounded-2xl border border-white/[.07] bg-white/[.025] p-5"><div className="flex items-center justify-between"><span className="text-sm text-slate-500">{label}</span><Icon size={17} className="text-cyan-300" /></div><div className="mt-4 text-3xl font-semibold">{value}</div></article>)}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.4fr_.6fr]">
          <article className="rounded-2xl border border-white/[.07] bg-white/[.025] p-6"><div className="flex items-center justify-between"><div><h2 className="text-lg font-semibold">Subject mastery</h2><p className="mt-1 text-xs text-slate-600">How your tracked subjects are progressing.</p></div><TrendingUp size={19} className="text-emerald-300" /></div><div className="mt-6 space-y-5">{subjects.length === 0 && <p className="text-sm text-slate-600">Start a study conversation and your subjects will appear here.</p>}{subjects.map(subject => <div key={subject.name}><div className="mb-2 flex items-center justify-between text-sm"><span>{subject.name}</span><span className="text-slate-500">{percent(subject.mastery)}%</span></div><div className="h-2 overflow-hidden rounded-full bg-white/[.06]"><div className="h-full rounded-full bg-cyan-400 transition-all" style={{ width: `${percent(subject.mastery)}%` }} /></div><div className="mt-2 text-[11px] text-slate-600">{number(subject.attempts)} attempts · {number(subject.questions)} questions</div></div>)}</div></article>
          <article className="rounded-2xl border border-white/[.07] bg-white/[.025] p-6"><h2 className="text-lg font-semibold">Accuracy</h2><div className="mt-7 flex items-center justify-center"><div className="flex h-36 w-36 flex-col items-center justify-center rounded-full border-8 border-cyan-400/20"><span className="text-3xl font-semibold">{percent(stats.accuracy)}%</span><span className="mt-1 text-xs text-slate-600">accuracy</span></div></div><div className="mt-6 grid grid-cols-2 gap-3 text-center"><div className="rounded-xl bg-emerald-400/[.06] p-3"><CheckCircle2 size={15} className="mx-auto text-emerald-300" /><div className="mt-2 text-lg">{number(stats.correct_answers)}</div><div className="text-[10px] text-slate-600">correct</div></div><div className="rounded-xl bg-red-400/[.06] p-3"><XCircle size={15} className="mx-auto text-red-300" /><div className="mt-2 text-lg">{number(stats.wrong_answers)}</div><div className="text-[10px] text-slate-600">wrong</div></div></div></article>
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <article className="rounded-2xl border border-white/[.07] bg-white/[.025] p-6"><div className="flex items-center gap-2"><BookOpen size={17} className="text-cyan-300" /><h2 className="text-lg font-semibold">Strengths</h2></div>{strengths.length ? <ul className="mt-5 space-y-3">{strengths.slice(0, 8).map(item => <li key={item} className="rounded-xl border border-emerald-400/10 bg-emerald-400/[.04] px-4 py-3 text-sm text-slate-300">{item}</li>)}</ul> : <p className="mt-5 text-sm text-slate-600">Keep studying. Nova will identify your strongest areas as data accumulates.</p>}</article>
          <article className="rounded-2xl border border-white/[.07] bg-white/[.025] p-6"><div className="flex items-center gap-2"><Target size={17} className="text-violet-300" /><h2 className="text-lg font-semibold">Focus areas</h2></div>{weaknesses.length ? <ul className="mt-5 space-y-3">{weaknesses.slice(0, 8).map(item => <li key={item} className="rounded-xl border border-amber-400/10 bg-amber-400/[.04] px-4 py-3 text-sm text-slate-300">{item}</li>)}</ul> : <p className="mt-5 text-sm text-slate-600">No weak areas detected yet.</p>}</article>
        </section>

        <section className="rounded-2xl border border-white/[.07] bg-white/[.025] p-6"><div className="flex items-center justify-between"><div><h2 className="text-lg font-semibold">Recent conversations</h2><p className="mt-1 text-xs text-slate-600">Jump back into your latest learning sessions.</p></div><button type="button" onClick={() => navigate("/chat")} className="text-xs text-cyan-300 hover:text-cyan-200">View all</button></div><div className="mt-5 divide-y divide-white/[.06]">{recent.length === 0 && <p className="py-4 text-sm text-slate-600">No conversation activity yet.</p>}{recent.slice(0, 10).map((item, index) => <button key={`${item.id || "conversation"}-${index}`} type="button" onClick={() => { try { if (item.id) localStorage.setItem("nova_current_conversation", item.id); } catch { /* ignore */ } navigate("/chat"); }} className="flex w-full items-center justify-between gap-4 py-4 text-left hover:bg-white/[.02]"><div className="min-w-0"><div className="truncate text-sm font-medium text-slate-300">{item.title || "Conversation"}</div><div className="mt-1 truncate text-xs text-slate-600">{item.last_message || "No messages yet"}</div></div><ArrowRight size={15} className="shrink-0 text-slate-700" /></button>)}</div></section>
      </div>
    </main>
  );
}

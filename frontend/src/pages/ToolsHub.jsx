import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, Calculator, Clock3, FileText, GraduationCap, Layers3,
  LoaderCircle, RefreshCw, Ruler, ShieldCheck, Sparkles, Wrench,
} from "lucide-react";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

const INTEGRATION_NAMES = {
  google_calendar: "Google Calendar",
  gmail: "Gmail",
  notion: "Notion",
  github: "GitHub",
};

function Panel({ children, className = "" }) {
  return <section className={`rounded-3xl border border-white/[.07] bg-gradient-to-br from-white/[.035] to-white/[.01] p-5 shadow-[0_18px_60px_rgba(0,0,0,.14)] ${className}`}>{children}</section>;
}

function Field({ label, value, onChange, placeholder, type = "text", min, max }) {
  return <label className="block min-w-0"><span className="mb-2 block text-[11px] font-semibold uppercase tracking-[.14em] text-slate-500">{label}</span><input type={type} min={min} max={max} value={value} onChange={event => onChange(event.target.value)} placeholder={placeholder} className="w-full rounded-xl border border-white/[.09] bg-[#080e1b] px-3.5 py-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-cyan-400/40"/></label>;
}

function Output({ toolId, value }) {
  if (!value) return null;
  return <div className="mt-4 overflow-hidden rounded-2xl border border-cyan-400/15 bg-cyan-400/[.045]">
    <div className="flex items-center gap-2 border-b border-white/[.06] px-4 py-3 text-xs font-semibold text-cyan-200"><Sparkles size={14}/> Nova tool result</div>
    <div className="p-4">
      {toolId === "calculator" && <><p className="text-[10px] font-semibold uppercase tracking-[.16em] text-slate-500">{value.expression}</p><p className="mt-1 text-3xl font-semibold tracking-tight text-white">{value.value}</p></>}
      {toolId === "unit_converter" && <><p className="text-[10px] font-semibold uppercase tracking-[.16em] text-slate-500">Converted value</p><p className="mt-1 text-2xl font-semibold text-white">{value.value} <span className="text-base text-cyan-200">{value.to_unit}</span></p><p className="mt-1 text-xs text-slate-500">{value.input} {value.from_unit} · {value.category}</p></>}
      {toolId === "world_clock" && <><p className="text-xl font-semibold text-white">{value.formatted}</p><p className="mt-1 text-xs text-slate-500">{value.timezone}</p></>}
      {toolId === "study_planner" && <><div className="mb-3 flex flex-wrap gap-2 text-[10px] text-cyan-100"><span className="rounded-lg bg-cyan-300/10 px-2.5 py-1">{value.duration_days} days</span><span className="rounded-lg bg-cyan-300/10 px-2.5 py-1">{value.daily_minutes} min / day</span><span className="rounded-lg bg-cyan-300/10 px-2.5 py-1">{value.total_minutes} min total</span></div><div className="max-h-64 space-y-2 overflow-auto">{(value.sessions || []).map(session => <div key={session.day} className="flex gap-3 rounded-xl border border-white/[.05] bg-black/10 p-3"><span className="shrink-0 text-xs font-semibold text-cyan-200">Day {session.day}</span><div><p className="text-[10px] text-slate-500">{session.date}</p><p className="mt-1 text-xs leading-5 text-slate-200">{session.activity}</p></div></div>)}</div></>}
      {toolId === "text_analyzer" && <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">{[["Words", value.words], ["Characters", value.characters], ["Sentences", value.sentences], ["Paragraphs", value.paragraphs], ["Reading time", value.estimated_reading_minutes + " min"]].map(([label, amount]) => <div key={label} className="rounded-xl border border-white/[.05] bg-black/10 p-3"><p className="text-[10px] text-slate-500">{label}</p><p className="mt-1 text-lg font-semibold text-white">{amount}</p></div>)}</div>}
    </div>
  </div>;
}

export default function ToolsHub() {
  const [catalog, setCatalog] = useState([]);
  const [integrations, setIntegrations] = useState([]);
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [outputs, setOutputs] = useState({});
  const [expression, setExpression] = useState("12 * (8 + 2)");
  const [unitValue, setUnitValue] = useState("5");
  const [fromUnit, setFromUnit] = useState("km");
  const [toUnit, setToUnit] = useState("mi");
  const [timezone, setTimezone] = useState("Europe/Paris");
  const [topic, setTopic] = useState("");
  const [days, setDays] = useState("7");
  const [minutes, setMinutes] = useState("30");
  const [text, setText] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      fetch(`${API_URL}/v1/tools`, { credentials: "include", headers: { Accept: "application/json" } }),
      fetch(`${API_URL}/v1/integrations`, { credentials: "include", headers: { Accept: "application/json" } }),
    ]).then(async ([toolsResponse, integrationsResponse]) => {
      const toolsPayload = toolsResponse.ok ? await toolsResponse.json() : null;
      const integrationsPayload = integrationsResponse.ok ? await integrationsResponse.json() : null;
      if (!active) return;
      setCatalog(Array.isArray(toolsPayload?.tools) ? toolsPayload.tools : []);
      setIntegrations(Array.isArray(integrationsPayload?.integrations) ? integrationsPayload.integrations : []);
    }).catch(() => {
      if (active) setError("Nova could not load the tool catalog. Check your connection and try again.");
    }).finally(() => { if (active) setLoadingCatalog(false); });
    return () => { active = false; };
  }, []);

  async function runTool(toolId, argumentsValue) {
    setBusy(toolId);
    setError("");
    try {
      const response = await fetch(`${API_URL}/v1/tools/execute`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ tool_id: toolId, arguments: argumentsValue }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload?.detail || payload?.error?.message || `Tool request failed (HTTP ${response.status}).`);
      setOutputs(current => ({ ...current, [toolId]: payload.result }));
    } catch (failure) {
      setError(failure?.message || "Nova could not run that tool.");
    } finally {
      setBusy("");
    }
  }

  const available = new Set(catalog.map(item => item.id));
  const buttonClass = "inline-flex items-center justify-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/[.09] px-4 py-2.5 text-xs font-semibold text-cyan-200 transition hover:border-cyan-400/40 hover:bg-cyan-400/[.14] disabled:cursor-not-allowed disabled:opacity-50";

  return <main className="min-h-screen bg-[#020617] px-5 pb-16 pt-8 text-white sm:px-8">
    <div className="mx-auto max-w-6xl">
      <header className="mb-9 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/chat" className="mb-5 inline-flex items-center gap-2 text-xs text-slate-500 transition hover:text-white"><ArrowLeft size={14}/> Back to chat</Link>
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-400/20 bg-cyan-400/[.08] text-cyan-300"><Wrench size={20}/></div>
            <div><p className="text-[10px] font-semibold uppercase tracking-[.22em] text-cyan-300/70">Nova workspace</p><h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">Tool Hub</h1></div>
          </div>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">A growing collection of tools Nova can use while helping you learn, plan and work with information.</p>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-emerald-400/15 bg-emerald-400/[.045] px-3 py-2 text-[11px] text-emerald-200"><ShieldCheck size={14}/> Local tools are read-only</div>
      </header>

      {error && <div role="alert" className="mb-6 rounded-2xl border border-rose-400/20 bg-rose-400/[.06] px-4 py-3 text-sm text-rose-200">{error}</div>}

      <div className="mb-5 flex items-center justify-between gap-3"><div><h2 className="text-sm font-semibold text-white">Available tools</h2><p className="mt-1 text-xs text-slate-500">Nova can also select supported tools automatically during a chat.</p></div>{loadingCatalog && <LoaderCircle size={17} className="animate-spin text-cyan-300"/>}</div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Panel>
          <div className="mb-4 flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400/[.08] text-cyan-300"><Calculator size={17}/></span><div><h3 className="text-sm font-semibold">Smart calculator</h3><p className="text-[11px] text-slate-500">Safe arithmetic engine</p></div></div>
          <Field label="Expression" value={expression} onChange={setExpression} placeholder="e.g. sqrt(81) + 12 * 4"/>
          <button className={`${buttonClass} mt-3 w-full`} disabled={busy === "calculator" || !available.has("calculator")} onClick={() => runTool("calculator", { expression })}>{busy === "calculator" ? <LoaderCircle size={14} className="animate-spin"/> : <Calculator size={14}/>} Calculate</button>
          <Output toolId="calculator" value={outputs.calculator}/>
        </Panel>

        <Panel>
          <div className="mb-4 flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-400/[.08] text-violet-300"><Ruler size={17}/></span><div><h3 className="text-sm font-semibold">Unit converter</h3><p className="text-[11px] text-slate-500">Common scientific units</p></div></div>
          <Field label="Value" value={unitValue} onChange={setUnitValue} type="number" placeholder="5"/>
          <div className="mt-3 grid grid-cols-2 gap-3"><Field label="From" value={fromUnit} onChange={setFromUnit} placeholder="km"/><Field label="To" value={toUnit} onChange={setToUnit} placeholder="mi"/></div>
          <button className={`${buttonClass} mt-3 w-full`} disabled={busy === "unit_converter" || !available.has("unit_converter")} onClick={() => runTool("unit_converter", { value: Number(unitValue), from_unit: fromUnit, to_unit: toUnit })}>{busy === "unit_converter" ? <LoaderCircle size={14} className="animate-spin"/> : <Ruler size={14}/>} Convert</button>
          <Output toolId="unit_converter" value={outputs.unit_converter}/>
        </Panel>

        <Panel>
          <div className="mb-4 flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-amber-400/[.08] text-amber-300"><Clock3 size={17}/></span><div><h3 className="text-sm font-semibold">World clock</h3><p className="text-[11px] text-slate-500">City or IANA timezone</p></div></div>
          <Field label="Timezone" value={timezone} onChange={setTimezone} placeholder="Europe/Paris"/>
          <button className={`${buttonClass} mt-3 w-full`} disabled={busy === "world_clock" || !available.has("world_clock")} onClick={() => runTool("world_clock", { timezone })}>{busy === "world_clock" ? <LoaderCircle size={14} className="animate-spin"/> : <Clock3 size={14}/>} Get local time</button>
          <Output toolId="world_clock" value={outputs.world_clock}/>
        </Panel>

        <Panel>
          <div className="mb-4 flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-400/[.08] text-emerald-300"><GraduationCap size={17}/></span><div><h3 className="text-sm font-semibold">Study planner</h3><p className="text-[11px] text-slate-500">Active recall and spaced review</p></div></div>
          <Field label="Study topic" value={topic} onChange={setTopic} placeholder="e.g. Algebra, cell biology..."/>
          <div className="mt-3 grid grid-cols-2 gap-3"><Field label="Days" value={days} onChange={setDays} type="number" min="1" max="90"/><Field label="Minutes / day" value={minutes} onChange={setMinutes} type="number" min="5" max="240"/></div>
          <button className={`${buttonClass} mt-3 w-full`} disabled={busy === "study_planner" || !available.has("study_planner") || !topic.trim()} onClick={() => runTool("study_planner", { topic, days: Number(days), daily_minutes: Number(minutes) })}>{busy === "study_planner" ? <LoaderCircle size={14} className="animate-spin"/> : <GraduationCap size={14}/>} Build study plan</button>
          <Output toolId="study_planner" value={outputs.study_planner}/>
        </Panel>

        <Panel className="md:col-span-2">
          <div className="mb-4 flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-400/[.08] text-sky-300"><FileText size={17}/></span><div><h3 className="text-sm font-semibold">Text analyzer</h3><p className="text-[11px] text-slate-500">Understand the size and structure of your notes or draft</p></div></div>
          <textarea value={text} onChange={event => setText(event.target.value)} rows={4} maxLength={20000} placeholder="Paste your notes or a text passage here..." className="w-full resize-y rounded-xl border border-white/[.09] bg-[#080e1b] px-3.5 py-3 text-sm leading-6 text-slate-100 outline-none transition placeholder:text-slate-600 focus:border-cyan-400/40"/>
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3"><span className="text-[11px] text-slate-600">{text.length.toLocaleString()} / 20,000 characters</span><button className={buttonClass} disabled={busy === "text_analyzer" || !available.has("text_analyzer") || !text.trim()} onClick={() => runTool("text_analyzer", { text })}>{busy === "text_analyzer" ? <LoaderCircle size={14} className="animate-spin"/> : <FileText size={14}/>} Analyze text</button></div>
          <Output toolId="text_analyzer" value={outputs.text_analyzer}/>
        </Panel>
      </div>

      <section className="mt-10">
        <div className="mb-4 flex items-center gap-3"><Layers3 size={17} className="text-cyan-300"/><div><h2 className="text-sm font-semibold">External integrations</h2><p className="mt-1 text-xs text-slate-500">The connection framework is planned, but no external account is connected yet.</p></div></div>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {integrations.map(item => <Panel key={item.id} className="p-4"><div className="flex items-start justify-between gap-2"><div><h3 className="text-sm font-semibold">{INTEGRATION_NAMES[item.id] || item.name}</h3><p className="mt-1 text-[11px] leading-5 text-slate-500">{item.description}</p></div><span className="shrink-0 rounded-lg border border-amber-400/15 bg-amber-400/[.05] px-2 py-1 text-[9px] font-semibold uppercase tracking-wider text-amber-200">Setup needed</span></div><p className="mt-3 text-[10px] text-slate-600">OAuth connection · Explicit permission · Confirm before writes</p></Panel>)}
        </div>
      </section>

      <div className="mt-8 flex items-start gap-3 rounded-2xl border border-white/[.06] bg-white/[.02] p-4 text-xs leading-5 text-slate-500"><ShieldCheck size={16} className="mt-0.5 shrink-0 text-emerald-300"/> Nova's current built-in tools run locally and do not send tool inputs to a third-party service. External integrations remain disabled until their OAuth flows, permissions and secure token storage are configured.</div>
      <button onClick={() => { setOutputs({}); setError(""); }} className="mt-5 inline-flex items-center gap-2 text-xs text-slate-500 transition hover:text-white"><RefreshCw size={13}/> Clear results</button>
    </div>
  </main>;
}

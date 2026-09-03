import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Check, LoaderCircle, RotateCcw, Save, Settings as SettingsIcon, ShieldCheck } from "lucide-react";
import { applyNovaLanguage } from "../i18n";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").trim().replace(/\/+$/, "");

const DEFAULTS = {
  name: "", language: "English", level: "High School", teaching_style: "adaptive",
  difficulty: "adaptive", hints: "when_needed", step_by_step: true, adaptive_learning: true,
  response_length: "balanced", tone: "friendly", use_examples: true, use_analogies: true,
  encouragement: true, correction_style: "explain", show_correct_answer: true, creativity: "medium",
  behavior: "", custom_instructions: ""
};

const LANGUAGES = [
  ["English", "English"], ["Spanish", "Spanish"], ["Chinese", "Chinese"], ["Hindi", "Hindi"],
  ["French", "French"], ["Arabic", "Arabic"], ["Portuguese", "Portuguese"], ["Russian", "Russian"],
  ["German", "German"], ["Japanese", "Japanese"], ["Korean", "Korean"], ["Italian", "Italian"],
  ["Turkish", "Turkish"], ["Dutch", "Dutch"], ["Polish", "Polish"], ["Ukrainian", "Ukrainian"],
  ["Vietnamese", "Vietnamese"], ["Thai", "Thai"], ["Indonesian", "Indonesian"], ["Swedish", "Swedish"],
  ["Greek", "Greek"], ["Czech", "Czech"], ["Romanian", "Romanian"], ["Hungarian", "Hungarian"]
];

const UI = {
  English: { title:"Nova Settings", subtitle:"Personalize how Nova teaches and responds.", back:"Back", profile:"Profile", name:"Your name", language:"Language", level:"Learning level", teaching:"Teaching style", difficulty:"Difficulty", hints:"Hints", response:"Response", length:"Response length", tone:"Tone", examples:"Use examples", analogies:"Use analogies", encouragement:"Encouragement", corrections:"Corrections", correctionStyle:"Correction style", answer:"Show correct answer", ai:"AI generation", creativity:"Creativity", personal:"Personal instructions", behavior:"Personal behavior", custom:"Custom AI instructions", save:"Save settings", saving:"Saving…", saved:"Settings saved", reset:"Reset", resetConfirm:"Reset all settings to their defaults?", status:"Your settings are stored with Nova and used on your next message." },
  French: { title:"Paramètres de Nova", subtitle:"Personnalisez la façon dont Nova enseigne et répond.", back:"Retour", profile:"Profil", name:"Votre nom", language:"Langue", level:"Niveau d’apprentissage", teaching:"Style d’enseignement", difficulty:"Difficulté", hints:"Indices", response:"Réponses", length:"Longueur des réponses", tone:"Ton", examples:"Utiliser des exemples", analogies:"Utiliser des analogies", encouragement:"Encouragement", corrections:"Corrections", correctionStyle:"Style de correction", answer:"Afficher la bonne réponse", ai:"Génération IA", creativity:"Créativité", personal:"Instructions personnelles", behavior:"Comportement personnel", custom:"Instructions IA personnalisées", save:"Enregistrer", saving:"Enregistrement…", saved:"Paramètres enregistrés", reset:"Réinitialiser", resetConfirm:"Réinitialiser tous les paramètres ?", status:"Vos paramètres sont enregistrés dans Nova et utilisés dès votre prochain message." },
  Spanish: { title:"Configuración de Nova", subtitle:"Personaliza cómo Nova enseña y responde.", back:"Atrás", profile:"Perfil", name:"Tu nombre", language:"Idioma", level:"Nivel de aprendizaje", teaching:"Estilo de enseñanza", difficulty:"Dificultad", hints:"Pistas", response:"Respuestas", length:"Longitud de respuesta", tone:"Tono", examples:"Usar ejemplos", analogies:"Usar analogías", encouragement:"Ánimo", corrections:"Correcciones", correctionStyle:"Estilo de corrección", answer:"Mostrar respuesta correcta", ai:"Generación de IA", creativity:"Creatividad", personal:"Instrucciones personales", behavior:"Comportamiento personal", custom:"Instrucciones de IA personalizadas", save:"Guardar", saving:"Guardando…", saved:"Configuración guardada", reset:"Restablecer", resetConfirm:"¿Restablecer toda la configuración?", status:"Tu configuración se guarda en Nova y se usa en tu próximo mensaje." },
  German: { title:"Nova-Einstellungen", subtitle:"Passe an, wie Nova lehrt und antwortet.", back:"Zurück", profile:"Profil", name:"Dein Name", language:"Sprache", level:"Lernniveau", teaching:"Lehrstil", difficulty:"Schwierigkeit", hints:"Hinweise", response:"Antworten", length:"Antwortlänge", tone:"Ton", examples:"Beispiele verwenden", analogies:"Analogien verwenden", encouragement:"Ermutigung", corrections:"Korrekturen", correctionStyle:"Korrekturstil", answer:"Richtige Antwort anzeigen", ai:"KI-Generierung", creativity:"Kreativität", personal:"Persönliche Anweisungen", behavior:"Persönliches Verhalten", custom:"Eigene KI-Anweisungen", save:"Speichern", saving:"Speichern…", saved:"Einstellungen gespeichert", reset:"Zurücksetzen", resetConfirm:"Alle Einstellungen zurücksetzen?", status:"Deine Einstellungen werden in Nova gespeichert und für deine nächste Nachricht verwendet." },
  Italian: { title:"Impostazioni Nova", subtitle:"Personalizza il modo in cui Nova insegna e risponde.", back:"Indietro", profile:"Profilo", name:"Il tuo nome", language:"Lingua", level:"Livello di apprendimento", teaching:"Stile di insegnamento", difficulty:"Difficoltà", hints:"Suggerimenti", response:"Risposte", length:"Lunghezza risposta", tone:"Tono", examples:"Usa esempi", analogies:"Usa analogie", encouragement:"Incoraggiamento", corrections:"Correzioni", correctionStyle:"Stile di correzione", answer:"Mostra risposta corretta", ai:"Generazione IA", creativity:"Creatività", personal:"Istruzioni personali", behavior:"Comportamento personale", custom:"Istruzioni IA personalizzate", save:"Salva impostazioni", saving:"Salvataggio…", saved:"Impostazioni salvate", reset:"Reimposta", resetConfirm:"Reimpostare tutte le impostazioni?", status:"Le impostazioni vengono salvate in Nova e usate nel prossimo messaggio." }
};

const FALLBACK_UI = {
  title:"Nova Settings", subtitle:"Personalize how Nova teaches and responds.", back:"Back", profile:"Profile", name:"Your name", language:"Language", level:"Learning level", teaching:"Teaching style", difficulty:"Difficulty", hints:"Hints", response:"Response", length:"Response length", tone:"Tone", examples:"Use examples", analogies:"Use analogies", encouragement:"Encouragement", corrections:"Corrections", correctionStyle:"Correction style", answer:"Show correct answer", ai:"AI generation", creativity:"Creativity", personal:"Personal instructions", behavior:"Personal behavior", custom:"Custom AI instructions", save:"Save settings", saving:"Saving…", saved:"Settings saved", reset:"Reset", resetConfirm:"Reset all settings to their defaults?", status:"Your settings are stored with Nova and used on your next message."
};

function normalize(data) {
  const source = data?.settings || data || {};
  return { ...DEFAULTS, ...source };
}

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = `Request failed (HTTP ${response.status}).`;
    try { const body = await response.json(); if (body?.detail) message = String(body.detail); } catch {}
    throw new Error(message);
  }
  return response.json();
}

function Select({ value, onChange, children }) {
  return <select value={value} onChange={e => onChange(e.target.value)} className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm text-white outline-none focus:border-cyan-400/50">{children}</select>;
}
function Field({ label, children }) { return <label className="block"><span className="mb-2 block text-sm font-medium text-slate-200">{label}</span>{children}</label>; }
function Toggle({ label, value, onChange }) { return <button type="button" onClick={() => onChange(!value)} className="flex w-full items-center justify-between gap-5 rounded-xl border border-white/5 bg-white/[.02] p-4 text-left hover:bg-white/[.04]"><span className="text-sm text-slate-200">{label}</span><span className={`h-6 w-11 rounded-full p-1 transition ${value ? "bg-cyan-500" : "bg-slate-700"}`}><span className={`block h-4 w-4 rounded-full bg-white transition ${value ? "translate-x-5" : "translate-x-0"}`} /></span></button>; }

export default function SettingsFixed() {
  const navigate = useNavigate();
  const [settings, setSettings] = useState(DEFAULTS);
  const [original, setOriginal] = useState(DEFAULTS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const language = settings.language;
  const ui = UI[language] || FALLBACK_UI;
  const dirty = useMemo(() => JSON.stringify(settings) !== JSON.stringify(original), [settings, original]);

  useEffect(() => {
    let active = true;
    request(`${API_URL}/settings`)
      .then(data => { if (!active) return; const next = normalize(data); setSettings(next); setOriginal(next); localStorage.setItem("nova_settings", JSON.stringify({ version: 1, settings: next })); applyNovaLanguage(next.language); })
      .catch(err => { if (!active) return; try { const raw = localStorage.getItem("nova_settings"); const cached = raw ? normalize(JSON.parse(raw)) : DEFAULTS; setSettings(cached); setOriginal(cached); applyNovaLanguage(cached.language); setError(err.message); } catch { setError(err.message); } })
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, []);

  function update(key, value) {
    setSettings(prev => ({ ...prev, [key]: value }));
    setSaved(false);
    setError("");
    if (key === "language") applyNovaLanguage(value);
  }

  async function save() {
    if (!dirty || saving) return;
    setSaving(true); setSaved(false); setError("");
    const payload = normalize(settings);
    try {
      const data = await request(`${API_URL}/settings`, { method:"POST", headers:{ "Content-Type":"application/json", "Accept":"application/json" }, body:JSON.stringify(payload) });
      const next = normalize(data);
      setSettings(next); setOriginal(next); setSaved(true);
      localStorage.setItem("nova_settings", JSON.stringify({ version:1, settings:next }));
      applyNovaLanguage(next.language);
    } catch (err) { setError(err.message || "Could not save settings."); }
    finally { setSaving(false); }
  }

  async function reset() {
    if (!window.confirm(ui.resetConfirm)) return;
    setSaving(true); setError("");
    try {
      const data = await request(`${API_URL}/settings/reset`, { method:"POST", headers:{ "Accept":"application/json" } });
      const next = normalize(data); setSettings(next); setOriginal(next); setSaved(true);
      localStorage.setItem("nova_settings", JSON.stringify({ version:1, settings:next })); applyNovaLanguage(next.language);
    } catch (err) {
      const next = { ...DEFAULTS }; setSettings(next); setOriginal(next); localStorage.setItem("nova_settings", JSON.stringify({ version:1, settings:next })); applyNovaLanguage(next.language); setError(err.message || "Could not reset settings.");
    } finally { setSaving(false); }
  }

  if (loading) return <div className="flex min-h-screen items-center justify-center bg-[#070a13] text-white"><LoaderCircle className="animate-spin text-cyan-300" size={28}/></div>;

  return <div className="min-h-screen bg-[#070a13] text-white">
    <header className="sticky top-0 z-20 border-b border-white/10 bg-[#070a13]/90 backdrop-blur-xl"><div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-5 py-4"><button onClick={() => navigate("/")} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white"><ArrowLeft size={17}/>{ui.back}</button><div className="flex items-center gap-3"><div className="rounded-xl border border-cyan-400/10 bg-cyan-400/10 p-2 text-cyan-300"><SettingsIcon size={18}/></div><div><div className="font-semibold">{ui.title}</div><div className="text-xs text-slate-500">{ui.subtitle}</div></div></div><button onClick={save} disabled={!dirty || saving} className="flex items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-40"><Save size={16}/>{saving ? ui.saving : ui.save}</button></div></header>
    <main className="mx-auto max-w-4xl space-y-5 px-5 py-8 pb-24">
      {error && <div className="rounded-xl border border-amber-400/20 bg-amber-400/5 px-4 py-3 text-sm text-amber-200">{error}</div>}
      {saved && <div className="flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-400/5 px-4 py-3 text-sm text-emerald-200"><Check size={16}/>{ui.saved}</div>}
      <section className="rounded-2xl border border-white/10 bg-white/[.03] p-6"><h2 className="mb-5 text-xl font-semibold">{ui.profile}</h2><div className="grid gap-5 md:grid-cols-2"><Field label={ui.name}><input value={settings.name} onChange={e => update("name", e.target.value)} className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm outline-none focus:border-cyan-400/50" /></Field><Field label={ui.language}><Select value={settings.language} onChange={v => update("language", v)}>{LANGUAGES.map(([label,value]) => <option key={value} value={value}>{label}</option>)}</Select></Field><Field label={ui.level}><Select value={settings.level} onChange={v => update("level", v)}><option>Middle School</option><option>High School</option><option>University</option></Select></Field></div></section>
      <section className="rounded-2xl border border-white/10 bg-white/[.03] p-6"><h2 className="mb-5 text-xl font-semibold">{ui.teaching}</h2><div className="grid gap-5 md:grid-cols-2"><Field label={ui.teaching}><Select value={settings.teaching_style} onChange={v => update("teaching_style", v)}><option value="adaptive">Adaptive</option><option value="step_by_step">Step by step</option><option value="socratic">Socratic</option><option value="direct">Direct</option></Select></Field><Field label={ui.difficulty}><Select value={settings.difficulty} onChange={v => update("difficulty", v)}><option value="adaptive">Adaptive</option><option value="easy">Easy</option><option value="normal">Normal</option><option value="advanced">Advanced</option></Select></Field><Field label={ui.hints}><Select value={settings.hints} onChange={v => update("hints", v)}><option value="when_needed">When needed</option><option value="always">Always</option><option value="never">Never</option></Select></Field></div><div className="mt-5 grid gap-3 md:grid-cols-2"><Toggle label="Adaptive learning" value={settings.adaptive_learning} onChange={v => update("adaptive_learning", v)}/><Toggle label="Step-by-step explanations" value={settings.step_by_step} onChange={v => update("step_by_step", v)}/></div></section>
      <section className="rounded-2xl border border-white/10 bg-white/[.03] p-6"><h2 className="mb-5 text-xl font-semibold">{ui.response}</h2><div className="grid gap-5 md:grid-cols-2"><Field label={ui.length}><Select value={settings.response_length} onChange={v => update("response_length", v)}><option value="concise">Concise</option><option value="balanced">Balanced</option><option value="detailed">Detailed</option></Select></Field><Field label={ui.tone}><Select value={settings.tone} onChange={v => update("tone", v)}><option value="friendly">Friendly</option><option value="professional">Professional</option><option value="academic">Academic</option><option value="casual">Casual</option></Select></Field></div><div className="mt-5 grid gap-3 md:grid-cols-2"><Toggle label={ui.examples} value={settings.use_examples} onChange={v => update("use_examples", v)}/><Toggle label={ui.analogies} value={settings.use_analogies} onChange={v => update("use_analogies", v)}/><Toggle label={ui.encouragement} value={settings.encouragement} onChange={v => update("encouragement", v)}/></div></section>
      <section className="rounded-2xl border border-white/10 bg-white/[.03] p-6"><h2 className="mb-5 text-xl font-semibold">{ui.corrections}</h2><div className="grid gap-5 md:grid-cols-2"><Field label={ui.correctionStyle}><Select value={settings.correction_style} onChange={v => update("correction_style", v)}><option value="explain">Explain the mistake</option><option value="gentle">Gentle</option><option value="strict">Strict and precise</option><option value="minimal">Minimal</option></Select></Field><Toggle label={ui.answer} value={settings.show_correct_answer} onChange={v => update("show_correct_answer", v)}/></div></section>
      <section className="rounded-2xl border border-white/10 bg-white/[.03] p-6"><h2 className="mb-5 text-xl font-semibold">{ui.ai}</h2><Field label={ui.creativity}><Select value={settings.creativity} onChange={v => update("creativity", v)}><option value="low">Low · Precise</option><option value="medium">Medium · Balanced</option><option value="high">High · Creative</option></Select></Field></section>
      <section className="rounded-2xl border border-white/10 bg-white/[.03] p-6"><h2 className="mb-5 text-xl font-semibold">{ui.personal}</h2><div className="space-y-5"><Field label={ui.behavior}><textarea rows={5} value={settings.behavior} onChange={e => update("behavior", e.target.value)} className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm outline-none focus:border-cyan-400/50" /></Field><Field label={ui.custom}><textarea rows={6} value={settings.custom_instructions} onChange={e => update("custom_instructions", e.target.value)} className="w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-3 text-sm outline-none focus:border-cyan-400/50" /></Field></div></section>
      <section className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/[.03] p-6 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-start gap-3"><ShieldCheck className="mt-0.5 shrink-0 text-emerald-300" size={18}/><p className="text-sm text-slate-400">{ui.status}</p></div><div className="flex gap-3"><button onClick={reset} disabled={saving} className="flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-sm text-slate-300 hover:bg-white/[.04] disabled:opacity-40"><RotateCcw size={16}/>{ui.reset}</button><button onClick={save} disabled={!dirty || saving} className="flex items-center gap-2 rounded-xl bg-cyan-500 px-5 py-2.5 text-sm font-semibold text-slate-950 disabled:opacity-40"><Save size={16}/>{saving ? ui.saving : ui.save}</button></div></section>
    </main>
  </div>;
}

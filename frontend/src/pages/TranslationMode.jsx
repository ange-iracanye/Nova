import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, Copy, Languages, LoaderCircle, Sparkles, WandSparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { NOVA_LANGUAGES, readNovaLanguage } from "../i18n.js";
import { uiText } from "../i18n-ui.js";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

function getUser() {
  try {
    const raw = localStorage.getItem("nova_user");
    const parsed = raw ? JSON.parse(raw) : null;
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function getUiCopy() {
  return {
    title: "Translation mode",
    subtitle: "Translate text accurately while preserving meaning, formatting, and tone.",
    source: "Source language",
    auto: "Auto-detect",
    target: "Translate to",
    input: "Text to translate",
    output: "Translation",
    placeholder: "Paste or type anything you want to translate...",
    translate: "Translate",
    translating: "Translating...",
    copy: "Copy",
    copied: "Copied",
    back: uiText("Back"),
    language: uiText("Language"),
    note: "Nova automatically keeps code, formulas, URLs, names, and formatting intact when possible.",
  };
}

export default function TranslationMode() {
  const navigate = useNavigate();
  const [source, setSource] = useState("auto");
  const [target, setTarget] = useState(() => readNovaLanguage().code || "en");
  const [input, setInput] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [ui, setUi] = useState(getUiCopy);

  useEffect(() => {
    const refresh = () => setUi(getUiCopy());
    window.addEventListener("nova-language-changed", refresh);
    return () => window.removeEventListener("nova-language-changed", refresh);
  }, []);

  const targetLanguage = useMemo(
    () => NOVA_LANGUAGES.find((language) => language.code === target) || NOVA_LANGUAGES[0],
    [target],
  );

  async function translate() {
    const text = input.trim();
    if (!text || loading) return;

    setLoading(true);
    setError("");
    setOutput("");
    setCopied(false);

    try {
      const user = getUser();
      let sessionId = null;
      let endpoint = "/chat/stream";

      if (!user?.email) {
        endpoint = "/demo/chat/stream";
        const sessionResponse = await fetch(`${API_URL}/demo/session`, { method: "POST" });
        if (!sessionResponse.ok) throw new Error(`Demo session failed: HTTP ${sessionResponse.status}`);
        const sessionData = await sessionResponse.json();
        sessionId = sessionData?.session_id;
        if (!sessionId) throw new Error("Nova returned an invalid demo session.");
      }

      const body = user?.email
        ? { message: text, email: user.email, tutor_mode: `translation:${target}` }
        : { message: text, session_id: sessionId, tutor_mode: `translation:${target}` };

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/plain" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const detail = await response.text().catch(() => "");
        throw new Error(detail || `Translation failed: HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("Nova returned an empty translation stream.");

      const decoder = new TextDecoder();
      let result = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        result += decoder.decode(value, { stream: true });
        setOutput(result);
      }
      result += decoder.decode();
      setOutput(result.trim());
    } catch (err) {
      setError(err?.message || "Nova could not translate this text.");
    } finally {
      setLoading(false);
    }
  }

  async function copyOutput() {
    if (!output) return;
    try {
      await navigator.clipboard.writeText(output);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1400);
    } catch {
      setError("Nova could not copy the translation.");
    }
  }

  return (
    <div className="min-h-[100dvh] bg-[#04060b] text-white">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -left-40 -top-40 h-[520px] w-[520px] rounded-full bg-sky-500/[.05] blur-[120px]" />
        <div className="absolute -right-40 top-20 h-[500px] w-[500px] rounded-full bg-violet-500/[.045] blur-[120px]" />
      </div>

      <main className="relative mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="inline-flex items-center gap-2 rounded-xl border border-white/[.08] bg-white/[.03] px-3.5 py-2.5 text-sm text-slate-300 hover:bg-white/[.06]"
          >
            <ArrowLeft size={16} />
            {ui.back}
          </button>

          <div className="flex items-center gap-2 text-xs text-slate-600">
            <Languages size={15} />
            {ui.language}
          </div>
        </header>

        <section className="mx-auto mt-12 max-w-3xl text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] border border-white/10 bg-white/[.045] shadow-2xl">
            <WandSparkles size={27} />
          </div>
          <p className="mt-6 text-[10px] font-bold uppercase tracking-[.25em] text-slate-600">NOVA AI</p>
          <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">{ui.title}</h1>
          <p className="mx-auto mt-4 max-w-2xl text-sm leading-6 text-slate-500">{ui.subtitle}</p>
        </section>

        <section className="mx-auto mt-10 grid max-w-5xl gap-4 lg:grid-cols-2">
          <div className="rounded-3xl border border-white/[.08] bg-white/[.025] p-4 shadow-2xl backdrop-blur-xl">
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="text-xs text-slate-500">
                {ui.source}
                <select value={source} onChange={(event) => setSource(event.target.value)} className="mt-2 w-full rounded-xl border border-white/[.08] bg-[#090c13] px-3 py-2.5 text-sm text-slate-200 outline-none">
                  <option value="auto">{ui.auto}</option>
                  {NOVA_LANGUAGES.map((language) => <option key={language.code} value={language.code}>{language.nativeName}</option>)}
                </select>
              </label>
              <label className="text-xs text-slate-500">
                {ui.target}
                <select value={target} onChange={(event) => setTarget(event.target.value)} className="mt-2 w-full rounded-xl border border-white/[.08] bg-[#090c13] px-3 py-2.5 text-sm text-slate-200 outline-none">
                  {NOVA_LANGUAGES.map((language) => <option key={language.code} value={language.code}>{language.nativeName}</option>)}
                </select>
              </label>
            </div>

            <label className="mt-4 block text-xs text-slate-500">
              {ui.input}
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder={ui.placeholder}
                maxLength={12000}
                rows={13}
                className="mt-2 w-full resize-y rounded-2xl border border-white/[.08] bg-[#070a11] px-4 py-3 text-sm leading-7 text-slate-200 outline-none placeholder:text-slate-700 focus:border-sky-400/30"
              />
            </label>

            <div className="mt-3 flex items-center justify-between gap-3">
              <span className="text-[10px] text-slate-700">{input.length.toLocaleString()} / 12,000</span>
              <button
                type="button"
                onClick={translate}
                disabled={!input.trim() || loading}
                className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-xs font-semibold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:bg-white/[.07] disabled:text-slate-600"
              >
                {loading ? <LoaderCircle size={14} className="animate-spin" /> : <Sparkles size={14} />}
                {loading ? ui.translating : ui.translate}
              </button>
            </div>
          </div>

          <div className="rounded-3xl border border-white/[.08] bg-white/[.025] p-4 shadow-2xl backdrop-blur-xl">
            <div className="flex items-center justify-between gap-3 px-1">
              <div>
                <div className="text-xs text-slate-500">{ui.output}</div>
                <div className="mt-1 text-[10px] text-slate-700">{targetLanguage.nativeName}</div>
              </div>
              <button type="button" onClick={copyOutput} disabled={!output} className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-2 text-[10px] text-slate-600 hover:bg-white/[.05] hover:text-slate-300 disabled:opacity-30">
                <Copy size={13} />
                {copied ? ui.copied : ui.copy}
              </button>
            </div>

            <div className="mt-3 min-h-[390px] whitespace-pre-wrap rounded-2xl border border-white/[.06] bg-[#070a11] p-4 text-sm leading-7 text-slate-200">
              {error ? <span className="text-red-300">{error}</span> : output || <span className="text-slate-700">{ui.note}</span>}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}

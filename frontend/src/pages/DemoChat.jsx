import { useEffect, useRef, useState } from "react";
import { ArrowRight, Bot, ChevronLeft, LoaderCircle, Lock, Menu, Send, Sparkles, User } from "lucide-react";
import { Link } from "react-router-dom";
import NovaLogo from "../components/NovaLogo";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const STARTERS = ["Explain photosynthesis simply", "Quiz me on algebra", "Why is the sky blue?", "Help me understand Newton's laws"];

const DEMO_SESSION_ATTEMPTS = 3;
const DEMO_SESSION_RETRY_DELAY = 1200;

async function createDemoSession() {
    let lastError = null;

    for (let attempt = 1; attempt <= DEMO_SESSION_ATTEMPTS; attempt += 1) {
        try {
            const response = await fetch(`${API_URL}/demo/session`, {
                method: "POST",
                headers: {
                    Accept: "application/json",
                },
                cache: "no-store",
            });

            if (!response.ok) {
                let detail = "Nova demo is unavailable right now.";
                try {
                    const data = await response.json();
                    detail = data?.detail || data?.error?.message || detail;
                } catch { /* keep the fallback message */ }
                throw new Error(detail);
            }

            const data = await response.json();
            if (!data?.session_id) throw new Error("Nova demo did not return a session.");
            return data.session_id;
        } catch (error) {
            lastError = error;
            if (attempt < DEMO_SESSION_ATTEMPTS) {
                await new Promise(resolve => setTimeout(resolve, DEMO_SESSION_RETRY_DELAY * attempt));
            }
        }
    }

    throw lastError || new Error("Nova demo is unavailable right now.");
}

async function streamDemoAnswer(sessionId, message, onChunk) {
    const response = await fetch(`${API_URL}/demo/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/plain" },
        cache: "no-store",
        body: JSON.stringify({ session_id: sessionId, message })
    });
    if (!response.ok) {
        let detail = "Nova could not answer right now.";
        try { const data = await response.json(); detail = data?.detail || data?.error?.message || detail; } catch { /* text response */ }
        throw new Error(detail);
    }
    if (!response.body) return await response.text();
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let answer = "";
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        answer += chunk;
        onChunk(answer);
    }
    return answer;
}

export default function DemoChat() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [busy, setBusy] = useState(false);
    const [menu, setMenu] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [error, setError] = useState("");
    const bottom = useRef(null);

    useEffect(() => {
        let cancelled = false;
        createDemoSession().then(id => { if (!cancelled) setSessionId(id); }).catch(err => { if (!cancelled) setError(err.message); });
        return () => { cancelled = true; };
    }, []);

    useEffect(() => bottom.current?.scrollIntoView({ behavior: "smooth" }), [messages, busy]);

    const send = async value => {
        const text = String(value ?? input).trim();
        if (!text || busy || !sessionId) return;
        setInput("");
        setError("");
        setMessages(prev => [...prev, { role: "user", text }, { role: "nova", text: "", streaming: true }]);
        setBusy(true);
        try {
            await streamDemoAnswer(sessionId, text, answer => {
                setMessages(prev => {
                    const next = [...prev];
                    const index = next.length - 1;
                    next[index] = { role: "nova", text: answer, streaming: true };
                    return next;
                });
            });
            setMessages(prev => {
                const next = [...prev];
                if (next.length) next[next.length - 1] = { ...next[next.length - 1], streaming: false };
                return next;
            });
        } catch (err) {
            setMessages(prev => prev.slice(0, -1));
            setError(err?.message || "Nova could not answer right now.");
        } finally { setBusy(false); }
    };

    return <main className="min-h-screen bg-[#070a13] text-white">
        <style>{`@keyframes demoIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}.demo-in{animation:demoIn .35s ease-out both}@media(prefers-reduced-motion:reduce){.demo-in{animation:none}}`}</style>
        <header className="sticky top-0 z-30 border-b border-white/[.06] bg-[#070a13]/90 backdrop-blur-xl">
            <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6"><Link to="/" className="flex items-center gap-3"><NovaLogo className="h-9 w-9 rounded-xl"/><span className="text-sm font-bold tracking-[.18em]">NOVA</span></Link><div className="hidden items-center gap-2 sm:flex"><span className="rounded-full border border-cyan-300/15 bg-cyan-300/[.05] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[.16em] text-cyan-200">Live demo</span><Link to="/login" className="rounded-xl px-3 py-2 text-xs text-slate-400 hover:text-white">Sign in</Link><Link to="/register" className="rounded-xl bg-white px-3.5 py-2 text-xs font-bold text-slate-950">Create account</Link></div><button className="rounded-xl border border-white/10 p-2 sm:hidden" onClick={()=>setMenu(v=>!v)}><Menu size={18}/></button></div>
            {menu && <div className="border-t border-white/[.06] px-4 py-3 sm:hidden"><div className="flex gap-2"><Link to="/login" className="flex-1 rounded-xl border border-white/10 px-3 py-2 text-center text-xs">Sign in</Link><Link to="/register" className="flex-1 rounded-xl bg-white px-3 py-2 text-center text-xs font-bold text-slate-950">Create account</Link></div></div>}
        </header>
        <div className="mx-auto flex min-h-[calc(100vh-64px)] max-w-6xl">
            <aside className="hidden w-64 shrink-0 border-r border-white/[.06] p-4 md:block"><Link to="/" className="mb-5 flex items-center gap-2 text-xs text-slate-500 hover:text-white"><ChevronLeft size={15}/>Home</Link><div className="rounded-2xl border border-cyan-300/10 bg-cyan-300/[.04] p-4"><Sparkles size={18} className="text-cyan-300"/><div className="mt-3 text-sm font-semibold">Nova live demo</div><p className="mt-1 text-xs leading-5 text-slate-500">This demo uses Nova's real AI backend. Conversations are temporary until you create an account.</p></div></aside>
            <section className="flex min-w-0 flex-1 flex-col">
                <div className="flex-1 overflow-y-auto px-4 py-8 sm:px-8"><div className="mx-auto max-w-3xl">
                    {messages.length === 0 ? <div className="flex min-h-[58vh] flex-col items-center justify-center text-center"><div className="flex h-16 w-16 items-center justify-center rounded-3xl border border-cyan-300/15 bg-cyan-300/[.06] shadow-[0_0_70px_rgba(34,211,238,.1)]"><Sparkles size={27} className="text-cyan-200"/></div><h1 className="mt-6 text-3xl font-semibold tracking-tight sm:text-5xl">What do you want to learn?</h1><p className="mt-4 max-w-xl text-sm leading-6 text-slate-500">Ask a real question. Nova's free public demo now uses the same AI backend as the full experience.</p><div className="mt-8 grid w-full max-w-2xl gap-2 sm:grid-cols-2">{STARTERS.map(s=><button key={s} onClick={()=>send(s)} disabled={!sessionId||busy} className="group rounded-2xl border border-white/[.07] bg-white/[.025] p-4 text-left text-sm text-slate-300 transition hover:-translate-y-0.5 hover:border-cyan-300/20 hover:bg-white/[.045] disabled:cursor-wait disabled:opacity-50"><span>{s}</span><ArrowRight size={15} className="mt-3 text-slate-600 transition group-hover:translate-x-1 group-hover:text-cyan-300"/></button>)}</div></div> : <div className="space-y-5">{messages.map((m,i)=><div key={i} className="demo-in flex gap-3"><div className={`mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border ${m.role === "user" ? "border-sky-400/20 bg-sky-400/10 text-sky-300" : "border-cyan-300/15 bg-cyan-300/[.06] text-cyan-200"}`}>{m.role === "user" ? <User size={16}/> : <Bot size={17}/>}</div><div className="min-w-0 rounded-2xl border border-white/[.07] bg-white/[.025] px-4 py-3 text-sm leading-7 text-slate-200 whitespace-pre-wrap">{m.text || (m.streaming ? "Nova is thinking…" : "")}</div></div>)}<div ref={bottom}/></div>}
                    {error && <div className="mt-4 rounded-xl border border-red-400/20 bg-red-400/[.05] px-4 py-3 text-xs text-red-200">{error}</div>}
                </div></div>
                <div className="border-t border-white/[.06] p-4 sm:p-6"><div className="mx-auto max-w-3xl"><div className="rounded-2xl border border-white/10 bg-white/[.035] p-2 shadow-2xl focus-within:border-cyan-300/20"><div className="flex items-end gap-2"><textarea value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}} rows={1} placeholder={sessionId ? "Ask Nova anything..." : "Connecting to Nova..."} disabled={!sessionId||busy} className="min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-sm text-white outline-none placeholder:text-slate-600 disabled:opacity-50"/><button onClick={()=>send()} disabled={!input.trim()||busy||!sessionId} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-slate-950 transition hover:scale-105 disabled:cursor-not-allowed disabled:opacity-30"><Send size={17}/></button></div></div><div className="mt-3 flex items-center justify-center gap-2 text-[10px] text-slate-600"><Lock size={11}/> Real Nova AI · Demo conversations are temporary · <Link to="/register" className="text-cyan-300 hover:text-cyan-200">Create a free account to keep them</Link></div></div></div>
            </section>
        </div>
    </main>;
}

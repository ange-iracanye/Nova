import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Copy, Edit3, LoaderCircle, Plus, Send, Sparkles, Trash2, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const USER_KEY = "nova_user";
const CURRENT_KEY = "nova_current_conversation";
const MAX_INPUT = 12000;

const userFromStorage = () => { try { const raw = localStorage.getItem(USER_KEY); return raw ? JSON.parse(raw) : null; } catch { return null; } };
const getCurrent = () => { try { return localStorage.getItem(CURRENT_KEY) || null; } catch { return null; } };
const setCurrent = id => { try { if (id) localStorage.setItem(CURRENT_KEY, id); else localStorage.removeItem(CURRENT_KEY); } catch {} };

async function fail(response) {
  let message = "";
  try { const body = await response.json(); message = body?.error?.message || body?.detail || body?.message || ""; } catch {}
  throw new Error(message || `Nova request failed: HTTP ${response.status}`);
}

function friendly(error) {
  const text = String(error?.message || "");
  if (/401/.test(text)) return "Your session has expired. Please sign in again.";
  if (/403/.test(text)) return "Nova refused this request because you do not have permission.";
  if (/404/.test(text)) return "Nova could not find that conversation.";
  if (/429/.test(text)) return "Nova is receiving too many requests. Try again shortly.";
  if (/Failed to fetch|NetworkError|Load failed/i.test(text)) return "Nova could not reach the backend.";
  return text || "Something went wrong while contacting Nova.";
}

async function stream(response, onChunk, signal) {
  if (!response.body) throw new Error("Nova returned an empty response stream.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let timer;
  const arm = () => { clearTimeout(timer); timer = setTimeout(() => reader.cancel(), 60000); };
  try {
    arm();
    while (true) {
      if (signal.aborted) { await reader.cancel(); throw new DOMException("Aborted", "AbortError"); }
      const { done, value } = await reader.read();
      if (done) break;
      arm();
      if (value) onChunk(decoder.decode(value, { stream: true }));
    }
    const tail = decoder.decode();
    if (tail) onChunk(tail);
  } finally { clearTimeout(timer); try { reader.releaseLock(); } catch {} }
}

export default function ChatProductionV2() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [conversationId, setConversationId] = useState(getCurrent());
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null);
  const [title, setTitle] = useState("");
  const abortRef = useRef(null);
  const endRef = useRef(null);
  const email = userFromStorage()?.email;

  const open = useCallback(async id => {
    if (!id) return;
    try {
      const response = await fetch(`${API}/v1/conversations/${encodeURIComponent(id)}`, { cache: "no-store" });
      if (!response.ok) await fail(response);
      const data = await response.json();
      const conversation = data?.conversation || {};
      setConversationId(id);
      setCurrent(id);
      setMessages((Array.isArray(conversation.messages) ? conversation.messages : []).map(item => ({ role: item?.role === "user" ? "user" : "nova", text: String(item?.text || "") })));
      setError("");
    } catch (err) { setError(friendly(err)); }
  }, []);

  const load = useCallback(async preferredId => {
    if (!email) { navigate("/login", { replace: true }); return; }
    setHistoryLoading(true);
    try {
      const response = await fetch(`${API}/v1/conversations`, { cache: "no-store" });
      if (!response.ok) await fail(response);
      const data = await response.json();
      const raw = data?.conversations && typeof data.conversations === "object" ? data.conversations : {};
      const items = Object.entries(raw).map(([id, value]) => ({ id, ...(value || {}) })).sort((a, b) => new Date(b.updated_at || 0) - new Date(a.updated_at || 0));
      setHistory(items);
      const saved = preferredId || conversationId || getCurrent();
      const target = saved && items.some(item => item.id === saved) ? saved : (items[0]?.id || null);
      if (target) await open(target);
      else { setConversationId(null); setCurrent(null); setMessages([]); }
    } catch (err) { setError(friendly(err)); }
    finally { setHistoryLoading(false); }
  }, [email, navigate, conversationId, open]);

  useEffect(() => { load(); }, []);
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: loading ? "auto" : "smooth" }); }, [messages, loading]);

  const newChat = () => {
    if (loading) return;
    abortRef.current?.abort();
    setLoading(false); setConversationId(null); setCurrent(null); setMessages([]); setInput(""); setError("");
  };

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    if (!email) { navigate("/login", { replace: true }); return; }
    if (text.length > MAX_INPUT) { setError(`Keep your message under ${MAX_INPUT.toLocaleString()} characters.`); return; }
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true); setError(""); setInput("");
    setMessages(prev => [...prev, { role: "user", text }]);
    try {
      const response = await fetch(`${API}/chat/stream`, { method: "POST", headers: { "Content-Type": "application/json", Accept: "text/plain" }, body: JSON.stringify({ message: text, email, conversation_id: conversationId || null, tutor_mode: "adaptive" }), signal: controller.signal });
      if (!response.ok) await fail(response);
      setMessages(prev => [...prev, { role: "nova", text: "", streaming: true }]);
      let answer = "";
      await stream(response, chunk => { answer += chunk; setMessages(prev => { const next = [...prev]; const i = next.length - 1; if (i >= 0 && next[i].role === "nova") next[i] = { ...next[i], text: answer, streaming: true }; return next; }); }, controller.signal);
      setMessages(prev => { const next = [...prev]; const i = next.length - 1; if (i >= 0 && next[i].role === "nova") next[i] = { ...next[i], text: answer || "Nova returned an empty response.", streaming: false }; return next; });
      // The API persists the conversation itself. Reloading the list and selecting
      // the newest item avoids depending on Access-Control-Expose-Headers for the
      // X-Conversation-ID response header.
      await load();
    } catch (err) {
      if (err?.name !== "AbortError") { const message = friendly(err); setError(message); setMessages(prev => [...prev, { role: "nova", text: message, error: true }]); }
    } finally { abortRef.current = null; setLoading(false); }
  };

  const deleteConversation = async id => {
    try {
      const response = await fetch(`${API}/v1/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
      if (!response.ok) await fail(response);
      if (id === conversationId) newChat();
      await load(id === conversationId ? null : conversationId);
    } catch (err) { setError(friendly(err)); }
  };

  const renameConversation = async () => {
    if (!editing || !title.trim()) return;
    try {
      const response = await fetch(`${API}/v1/conversations/${encodeURIComponent(editing)}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title: title.trim() }) });
      if (!response.ok) await fail(response);
      setEditing(null); await load(conversationId);
    } catch (err) { setError(friendly(err)); }
  };

  const filtered = useMemo(() => { const q = search.trim().toLowerCase(); return q ? history.filter(item => `${item.title || ""} ${item.messages?.at?.(-1)?.text || ""}`.toLowerCase().includes(q)) : history; }, [history, search]);

  return (
    <main className="flex min-h-screen bg-[#020617] text-slate-100">
      <aside className="hidden w-80 shrink-0 flex-col border-r border-white/[.07] bg-slate-950/80 md:flex">
        <div className="flex items-center justify-between border-b border-white/[.07] p-4"><div className="flex items-center gap-2"><Sparkles size={18} className="text-cyan-300" /><span className="font-semibold">Nova Chat</span></div><button onClick={newChat} className="rounded-xl border border-white/10 bg-white/[.04] p-2"><Plus size={17} /></button></div>
        <div className="p-3"><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search conversations" className="w-full rounded-xl border border-white/10 bg-white/[.04] px-3 py-2 text-sm outline-none placeholder:text-slate-600" /></div>
        <div className="flex-1 overflow-y-auto px-2">{historyLoading && <div className="px-3 py-4 text-sm text-slate-600">Loading history...</div>}{!historyLoading && !filtered.length && <div className="px-3 py-6 text-sm text-slate-600">No conversations yet.</div>}{filtered.map(item => <div key={item.id} className={`group mb-1 rounded-xl border ${item.id === conversationId ? "border-cyan-300/20 bg-cyan-300/[.06]" : "border-transparent hover:bg-white/[.03]"}`}><button onClick={() => open(item.id)} className="w-full px-3 py-3 text-left"><div className="truncate text-sm font-medium">{item.title || "New Chat"}</div><div className="mt-1 truncate text-xs text-slate-600">{item.messages?.at?.(-1)?.text || "No messages yet"}</div></button><div className="flex gap-1 px-2 pb-2 opacity-0 group-hover:opacity-100"><button onClick={() => { setEditing(item.id); setTitle(item.title || "New Chat"); }} className="p-1.5 text-slate-500 hover:text-white"><Edit3 size={13} /></button><button onClick={() => deleteConversation(item.id)} className="p-1.5 text-slate-500 hover:text-red-300"><Trash2 size={13} /></button></div></div>)}</div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-white/[.07] bg-slate-950/70 px-4 py-3"><div className="flex items-center gap-3"><button onClick={newChat} className="rounded-xl border border-white/10 bg-white/[.04] p-2 md:hidden"><Plus size={16} /></button><MessageIcon /><span className="text-sm font-semibold">{history.find(item => item.id === conversationId)?.title || "New Chat"}</span></div><button onClick={() => navigate("/dashboard")} className="rounded-xl px-3 py-2 text-xs text-slate-400 hover:bg-white/[.04]">Dashboard</button></header>
        {error && <div className="mx-auto mt-4 flex w-[min(900px,calc(100%-2rem))] items-center justify-between rounded-xl border border-red-400/20 bg-red-500/[.06] px-4 py-3 text-sm text-red-200"><span>{error}</span><button onClick={() => setError("")}><X size={15} /></button></div>}
        <div className="flex-1 overflow-y-auto px-4 py-8"><div className="mx-auto flex max-w-4xl flex-col gap-5">{!messages.length && <div className="flex min-h-[55vh] flex-col items-center justify-center text-center"><Sparkles size={34} className="text-cyan-300" /><h1 className="mt-5 text-3xl font-semibold">What do you want to learn?</h1><p className="mt-3 max-w-lg text-sm text-slate-500">Ask Nova anything. Your conversation is saved automatically.</p></div>}{messages.map((message, index) => <article key={`${index}-${message.role}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}><div className={`max-w-[85%] rounded-2xl border px-4 py-3 ${message.role === "user" ? "border-cyan-400/20 bg-cyan-500/10" : "border-white/[.07] bg-white/[.035]"}`}>{message.role === "nova" && <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.16em] text-slate-600"><Sparkles size={12} />Nova</div>}{message.role === "nova" && !message.text && message.streaming ? <LoaderCircle size={16} className="animate-spin text-slate-500" /> : <div className="text-sm leading-7"><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown></div>}{message.role === "nova" && message.text && !message.streaming && <button onClick={() => navigator.clipboard?.writeText(message.text)} className="mt-3 flex items-center gap-1 text-xs text-slate-600"><Copy size={12} />Copy</button>}</div></article>)}<div ref={endRef} /></div></div>
        <form onSubmit={e => { e.preventDefault(); send(); }} className="border-t border-white/[.07] bg-slate-950/70 p-4"><div className="mx-auto flex max-w-4xl items-end gap-2 rounded-2xl border border-white/10 bg-white/[.035] p-2"><textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} maxLength={MAX_INPUT} rows={1} placeholder="Message Nova..." className="min-h-12 flex-1 resize-none bg-transparent px-3 py-3 text-sm outline-none placeholder:text-slate-600" /><button disabled={!input.trim() || loading} className="flex h-11 w-11 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 disabled:opacity-40"><Send size={17} /></button></div></form>
      </section>
      {editing && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"><div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950 p-5"><div className="flex justify-between"><h2 className="font-semibold">Rename conversation</h2><button onClick={() => setEditing(null)}><X size={17} /></button></div><input autoFocus value={title} onChange={e => setTitle(e.target.value)} onKeyDown={e => e.key === "Enter" && renameConversation()} className="mt-5 w-full rounded-xl border border-white/10 bg-white/[.04] px-3 py-3 text-sm outline-none" /><div className="mt-4 flex justify-end gap-2"><button onClick={() => setEditing(null)} className="rounded-xl px-4 py-2 text-sm text-slate-400">Cancel</button><button onClick={renameConversation} className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950">Save</button></div></div></div>}
    </main>
  );
}

function MessageIcon() { return <Sparkles size={17} className="text-cyan-300" />; }

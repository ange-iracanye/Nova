import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Copy, Edit3, LoaderCircle, MessageSquare, Plus, RefreshCw, Send, Sparkles, Trash2, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
const CURRENT_KEY = "nova_current_conversation";
const USER_KEY = "nova_user";
const STREAM_TIMEOUT = 60000;
const MAX_INPUT = 12000;

function getUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function currentId() {
  try {
    return localStorage.getItem(CURRENT_KEY) || null;
  } catch {
    return null;
  }
}

function setCurrentId(id) {
  try {
    if (id) localStorage.setItem(CURRENT_KEY, id);
    else localStorage.removeItem(CURRENT_KEY);
  } catch {
    // Storage is optional.
  }
}

function friendlyError(error) {
  const message = String(error?.message || "");
  if (/401/.test(message)) return "Your session has expired. Please sign in again.";
  if (/403/.test(message)) return "Nova refused this request because you do not have permission.";
  if (/404/.test(message)) return "Nova could not find that conversation.";
  if (/429/.test(message)) return "Nova is receiving too many requests. Try again in a moment.";
  if (/500|502|503|504/.test(message)) return "Nova's backend encountered an internal error.";
  if (/Failed to fetch|NetworkError|Load failed/i.test(message)) return "Nova could not reach the backend.";
  return message || "Something went wrong while contacting Nova.";
}

async function readError(response) {
  let text = "";
  try { text = await response.text(); } catch { /* ignore */ }
  let detail = "";
  try {
    const data = JSON.parse(text);
    detail = data?.error?.message || data?.detail || data?.message || "";
  } catch { /* response may be plain text */ }
  throw new Error(detail || `Nova request failed: HTTP ${response.status}`);
}

async function readStream(response, onChunk, signal) {
  if (!response.body) throw new Error("Nova returned an empty response stream.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let timer;
  let timedOut = false;
  const arm = () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      timedOut = true;
      try { reader.cancel(); } catch { /* ignore */ }
    }, STREAM_TIMEOUT);
  };
  try {
    arm();
    while (true) {
      if (signal?.aborted) {
        try { await reader.cancel(); } catch { /* ignore */ }
        throw new DOMException("Request aborted", "AbortError");
      }
      const { done, value } = await reader.read();
      if (timedOut) throw new Error("Nova stream timed out.");
      if (done) break;
      arm();
      if (value) onChunk(decoder.decode(value, { stream: true }));
    }
    const tail = decoder.decode();
    if (tail) onChunk(tail);
  } finally {
    clearTimeout(timer);
    try { reader.releaseLock(); } catch { /* ignore */ }
  }
}

function normalizeConversation(item) {
  const conversation = item && typeof item === "object" ? item : {};
  return {
    id: String(conversation.id || ""),
    title: String(conversation.title || "New Chat"),
    created_at: conversation.created_at || null,
    updated_at: conversation.updated_at || conversation.created_at || null,
    messages: Array.isArray(conversation.messages) ? conversation.messages : [],
  };
}

export default function ChatProduction() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [conversationId, setConversationId] = useState(currentId());
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const endRef = useRef(null);
  const abortRef = useRef(null);

  const user = getUser();
  const email = user?.email;

  const loadHistory = useCallback(async (selectId = null) => {
    if (!email) {
      navigate("/login", { replace: true });
      return;
    }
    setHistoryLoading(true);
    try {
      const response = await fetch(`${API_URL}/v1/conversations`, { cache: "no-store" });
      if (!response.ok) await readError(response);
      const data = await response.json();
      const raw = data?.conversations && typeof data.conversations === "object" ? data.conversations : {};
      const items = Object.entries(raw).map(([id, value]) => normalizeConversation({ id, ...value }));
      items.sort((a, b) => new Date(b.updated_at || 0) - new Date(a.updated_at || 0));
      setHistory(items);
      const target = selectId || conversationId || currentId();
      if (target && items.some(item => item.id === target)) {
        await openConversation(target);
      } else if (!target) {
        setMessages([]);
      }
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setHistoryLoading(false);
    }
  }, [email, navigate, conversationId]);

  const openConversation = useCallback(async (id) => {
    if (!id) return;
    try {
      const response = await fetch(`${API_URL}/v1/conversations/${encodeURIComponent(id)}`, { cache: "no-store" });
      if (!response.ok) await readError(response);
      const data = await response.json();
      const conversation = normalizeConversation(data?.conversation);
      setConversationId(id);
      setCurrentId(id);
      setMessages(conversation.messages.map(message => ({
        role: message?.role === "user" ? "user" : "nova",
        text: typeof message?.text === "string" ? message.text : "",
      })));
      setError("");
    } catch (err) {
      setError(friendlyError(err));
    }
  }, []);

  useEffect(() => {
    loadHistory();
    // Initial production load only. Further refreshes are explicit or after a message.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: loading ? "auto" : "smooth" });
  }, [messages, loading]);

  const newChat = useCallback(() => {
    if (loading) return;
    abortRef.current?.abort();
    setLoading(false);
    setConversationId(null);
    setCurrentId(null);
    setMessages([]);
    setInput("");
    setError("");
  }, [loading]);

  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    if (text.length > MAX_INPUT) {
      setError(`Keep your message under ${MAX_INPUT.toLocaleString()} characters.`);
      return;
    }
    if (!email) {
      navigate("/login", { replace: true });
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError("");
    setInput("");
    setMessages(previous => [...previous, { role: "user", text }]);

    try {
      // Do NOT create an empty conversation here. NovaCore owns creation when
      // conversation_id is absent. This keeps its in-memory manager and the
      // JSON-backed history synchronized.
      const response = await fetch(`${API_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/plain" },
        body: JSON.stringify({
          message: text,
          email,
          conversation_id: conversationId || null,
          tutor_mode: "adaptive",
        }),
        signal: controller.signal,
      });

      if (!response.ok) await readError(response);

      const returnedId = response.headers.get("X-Conversation-ID") || conversationId;
      if (returnedId) {
        setConversationId(returnedId);
        setCurrentId(returnedId);
      }

      setMessages(previous => [...previous, { role: "nova", text: "", streaming: true }]);
      let answer = "";
      await readStream(response, chunk => {
        answer += chunk;
        setMessages(previous => {
          const next = [...previous];
          const last = next.length - 1;
          if (last >= 0 && next[last].role === "nova") {
            next[last] = { ...next[last], text: answer, streaming: true };
          }
          return next;
        });
      }, controller.signal);

      setMessages(previous => {
        const next = [...previous];
        const last = next.length - 1;
        if (last >= 0 && next[last].role === "nova") {
          next[last] = { ...next[last], text: answer || "Nova returned an empty response.", streaming: false };
        }
        return next;
      });
      await loadHistory(returnedId || undefined);
    } catch (err) {
      if (err?.name !== "AbortError") {
        setError(friendlyError(err));
        setMessages(previous => [...previous, { role: "nova", text: friendlyError(err), error: true }]);
      }
    } finally {
      abortRef.current = null;
      setLoading(false);
    }
  }, [input, loading, email, navigate, conversationId, loadHistory]);

  const deleteConversation = useCallback(async (id) => {
    if (!id || loading) return;
    try {
      const response = await fetch(`${API_URL}/v1/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
      if (!response.ok) await readError(response);
      if (conversationId === id) newChat();
      await loadHistory(conversationId === id ? null : conversationId);
    } catch (err) {
      setError(friendlyError(err));
    }
  }, [conversationId, loading, loadHistory, newChat]);

  const renameConversation = useCallback(async () => {
    if (!editing || !editTitle.trim()) return;
    try {
      const response = await fetch(`${API_URL}/v1/conversations/${encodeURIComponent(editing)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: editTitle.trim() }),
      });
      if (!response.ok) await readError(response);
      setEditing(null);
      await loadHistory(conversationId);
    } catch (err) {
      setError(friendlyError(err));
    }
  }, [editing, editTitle, loadHistory, conversationId]);

  const filteredHistory = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return history;
    return history.filter(item => `${item.title} ${item.messages?.at(-1)?.text || ""}`.toLowerCase().includes(query));
  }, [history, search]);

  return (
    <main className="flex min-h-screen bg-[#020617] text-slate-100">
      <aside className="hidden w-80 shrink-0 flex-col border-r border-white/[.07] bg-slate-950/80 md:flex">
        <div className="flex items-center justify-between border-b border-white/[.07] p-4">
          <div className="flex items-center gap-2"><Sparkles size={18} className="text-cyan-300" /><span className="font-semibold">Nova Chat</span></div>
          <button type="button" onClick={newChat} className="rounded-xl border border-white/10 bg-white/[.04] p-2 hover:bg-white/[.08]" title="New chat"><Plus size={17} /></button>
        </div>
        <div className="p-3"><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search conversations" className="w-full rounded-xl border border-white/10 bg-white/[.04] px-3 py-2 text-sm outline-none placeholder:text-slate-600 focus:border-cyan-300/30" /></div>
        <div className="flex-1 overflow-y-auto px-2 pb-3">
          {historyLoading && <div className="flex items-center gap-2 px-3 py-4 text-sm text-slate-500"><LoaderCircle size={15} className="animate-spin" />Loading history...</div>}
          {!historyLoading && filteredHistory.length === 0 && <div className="px-3 py-6 text-sm text-slate-600">No conversations yet.</div>}
          {filteredHistory.map(item => (
            <div key={item.id} className={`group mb-1 rounded-xl border ${item.id === conversationId ? "border-cyan-300/20 bg-cyan-300/[.06]" : "border-transparent hover:border-white/[.06] hover:bg-white/[.03]"}`}>
              <button type="button" onClick={() => openConversation(item.id)} className="block w-full px-3 py-3 text-left">
                <div className="truncate text-sm font-medium text-slate-200">{item.title}</div>
                <div className="mt-1 truncate text-xs text-slate-600">{item.messages?.at(-1)?.text || "No messages yet"}</div>
              </button>
              <div className="flex gap-1 px-2 pb-2 opacity-0 transition group-hover:opacity-100">
                <button type="button" onClick={() => { setEditing(item.id); setEditTitle(item.title); }} className="rounded-lg p-1.5 text-slate-500 hover:bg-white/[.06] hover:text-slate-200" title="Rename"><Edit3 size={13} /></button>
                <button type="button" onClick={() => deleteConversation(item.id)} className="rounded-lg p-1.5 text-slate-500 hover:bg-red-500/10 hover:text-red-300" title="Delete"><Trash2 size={13} /></button>
              </div>
            </div>
          ))}
        </div>
      </aside>

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-white/[.07] bg-slate-950/60 px-4 py-3 backdrop-blur-xl md:px-6">
          <div className="flex items-center gap-3"><button type="button" onClick={newChat} className="rounded-xl border border-white/10 bg-white/[.04] p-2 md:hidden"><Plus size={17} /></button><MessageSquare size={17} className="text-cyan-300" /><span className="text-sm font-semibold">{history.find(item => item.id === conversationId)?.title || "New Chat"}</span></div>
          <button type="button" onClick={() => navigate("/dashboard")} className="rounded-xl px-3 py-2 text-xs text-slate-400 hover:bg-white/[.04] hover:text-white">Dashboard</button>
        </header>

        {error && <div className="mx-auto mt-4 flex w-[min(900px,calc(100%-2rem))] items-center justify-between rounded-xl border border-red-400/20 bg-red-500/[.06] px-4 py-3 text-sm text-red-200"><span>{error}</span><button type="button" onClick={() => setError("")}><X size={15} /></button></div>}

        <div className="flex-1 overflow-y-auto px-4 py-8 md:px-8">
          <div className="mx-auto flex w-full max-w-4xl flex-col gap-5">
            {messages.length === 0 && <div className="flex min-h-[55vh] flex-col items-center justify-center text-center"><div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-300/15 bg-cyan-300/[.06] text-cyan-300"><Sparkles size={28} /></div><h1 className="text-3xl font-semibold tracking-tight">What do you want to learn?</h1><p className="mt-3 max-w-lg text-sm leading-6 text-slate-500">Ask Nova a question, request an explanation, or start practicing. Your conversation will be saved automatically.</p></div>}
            {messages.map((message, index) => (
              <article key={`${index}-${message.role}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[85%] rounded-2xl border px-4 py-3 ${message.role === "user" ? "border-cyan-400/20 bg-cyan-500/10 text-slate-100" : "border-white/[.07] bg-white/[.035] text-slate-200"}`}>
                  {message.role === "nova" && <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.16em] text-slate-600"><Sparkles size={12} /> Nova</div>}
                  {message.role === "nova" && !message.text && message.streaming ? <LoaderCircle size={16} className="animate-spin text-slate-500" /> : <div className="nova-markdown text-sm leading-7"><ReactMarkdown remarkPlugins={[remarkGfm]}>{message.text}</ReactMarkdown></div>}
                  {message.role === "nova" && message.text && !message.streaming && <button type="button" onClick={() => navigator.clipboard?.writeText(message.text)} className="mt-3 flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-300"><Copy size={12} /> Copy</button>}
                </div>
              </article>
            ))}
            <div ref={endRef} />
          </div>
        </div>

        <form onSubmit={event => { event.preventDefault(); send(); }} className="border-t border-white/[.07] bg-slate-950/70 p-4 backdrop-blur-xl md:p-5">
          <div className="mx-auto flex max-w-4xl items-end gap-3 rounded-2xl border border-white/10 bg-white/[.035] p-2 focus-within:border-cyan-300/20">
            <textarea value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); } }} rows={1} maxLength={MAX_INPUT} placeholder="Message Nova..." className="max-h-48 min-h-12 flex-1 resize-none bg-transparent px-3 py-3 text-sm outline-none placeholder:text-slate-600" />
            <button type="submit" disabled={!input.trim() || loading} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40" title="Send"><Send size={17} /></button>
          </div>
          <div className="mx-auto mt-2 flex max-w-4xl items-center justify-between px-2 text-[10px] text-slate-700"><span>Enter to send · Shift+Enter for a new line</span><span>{input.length}/{MAX_INPUT}</span></div>
        </form>
      </section>

      {editing && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"><div className="w-full max-w-md rounded-2xl border border-white/10 bg-slate-950 p-5 shadow-2xl"><div className="flex items-center justify-between"><h2 className="font-semibold">Rename conversation</h2><button type="button" onClick={() => setEditing(null)}><X size={17} /></button></div><input autoFocus value={editTitle} onChange={event => setEditTitle(event.target.value)} onKeyDown={event => { if (event.key === "Enter") renameConversation(); }} className="mt-5 w-full rounded-xl border border-white/10 bg-white/[.04] px-3 py-3 text-sm outline-none focus:border-cyan-300/30" /><div className="mt-4 flex justify-end gap-2"><button type="button" onClick={() => setEditing(null)} className="rounded-xl px-4 py-2 text-sm text-slate-400 hover:bg-white/[.05]">Cancel</button><button type="button" onClick={renameConversation} className="rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950">Save</button></div></div></div>}
    </main>
  );
}

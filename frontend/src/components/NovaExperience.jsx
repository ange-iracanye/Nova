import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  ArrowRight, Brain, Command, Gauge, Keyboard, LayoutDashboard,
  Palette, Search, Settings2, Sparkles, UserCircle, X, Zap
} from "lucide-react";
import "../styles/novaExperience.css";

const EXCLUDED = new Set(["/", "/chat", "/analytics"]);

const ACTIONS = [
  { label: "Open dashboard", hint: "Learning cockpit", icon: LayoutDashboard, path: "/dashboard" },
  { label: "Open settings", hint: "Tutor behavior", icon: Settings2, path: "/settings" },
  { label: "Open account", hint: "Profile & appearance", icon: UserCircle, path: "/account" },
  { label: "Account security", hint: "Password & protection", icon: Gauge, path: "/account-security" },
  { label: "Capabilities", hint: "Explore Nova", icon: Sparkles, path: "/capabilities/adaptive-tutoring" },
];

function readProfile() {
  try { return JSON.parse(localStorage.getItem("nova_profile_preferences") || "{}") || {}; }
  catch { return {}; }
}

function applyAccent() {
  const profile = readProfile();
  const colors = { cyan: "#22d3ee", violet: "#a78bfa", blue: "#60a5fa", emerald: "#34d399", rose: "#fb7185", amber: "#fbbf24" };
  document.documentElement.style.setProperty("--nova-accent", colors[profile.accent] || colors.cyan);
}

export default function NovaExperience() {
  const location = useLocation();
  const navigate = useNavigate();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [spotlight, setSpotlight] = useState({ x: 50, y: 35 });
  const [progress, setProgress] = useState(0);
  const [dockOpen, setDockOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const frame = useRef(0);
  const pendingPointer = useRef(null);
  const enhanced = !EXCLUDED.has(location.pathname);
  const dashboard = location.pathname === "/dashboard";
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? ACTIONS.filter(item => `${item.label} ${item.hint}`.toLowerCase().includes(q)) : ACTIONS;
  }, [query]);

  useEffect(() => {
    document.body.classList.toggle("nova-enhanced", enhanced);
    document.body.classList.toggle("nova-dashboard-mode", dashboard);
    document.body.dataset.novaRoute = location.pathname;
    applyAccent();
    return () => {
      document.body.classList.remove("nova-enhanced", "nova-dashboard-mode");
      delete document.body.dataset.novaRoute;
    };
  }, [enhanced, dashboard, location.pathname]);

  useEffect(() => {
    if (!enhanced) return undefined;
    const onKey = event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen(value => !value);
        setDockOpen(false);
        return;
      }
      if (event.key === "Escape") {
        setPaletteOpen(false);
        setDockOpen(false);
        return;
      }
      if (!paletteOpen || !filtered.length) return;
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setActiveIndex(index => (index + 1) % filtered.length);
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setActiveIndex(index => (index - 1 + filtered.length) % filtered.length);
      } else if (event.key === "Enter") {
        event.preventDefault();
        const item = filtered[activeIndex];
        if (item) { setPaletteOpen(false); setQuery(""); navigate(item.path); }
      }
    };
    const onMove = event => {
      pendingPointer.current = { x: (event.clientX / window.innerWidth) * 100, y: (event.clientY / window.innerHeight) * 100 };
      if (frame.current) return;
      frame.current = window.requestAnimationFrame(() => {
        if (pendingPointer.current) setSpotlight(pendingPointer.current);
        frame.current = 0;
      });
    };
    const onScroll = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(max > 0 ? (window.scrollY / max) * 100 : 0);
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("scroll", onScroll);
      if (frame.current) window.cancelAnimationFrame(frame.current);
    };
  }, [enhanced, paletteOpen, filtered, activeIndex, navigate]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query, paletteOpen]);

  useEffect(() => {
    if (!enhanced) return undefined;
    setPaletteOpen(false);
    setDockOpen(false);
    setQuery("");
    window.scrollTo(0, 0);
    document.documentElement.classList.add("nova-page-enter");
    const timer = window.setTimeout(() => document.documentElement.classList.remove("nova-page-enter"), 650);
    return () => window.clearTimeout(timer);
  }, [location.pathname, enhanced]);

  if (!enhanced) return null;

  const run = path => { setPaletteOpen(false); setDockOpen(false); setQuery(""); navigate(path); };

  return <>
    <div className="nova-ambient" aria-hidden="true">
      <div className="nova-ambient-grid" />
      <div className="nova-orb nova-orb-one" />
      <div className="nova-orb nova-orb-two" />
      <div className="nova-orb nova-orb-three" />
      <div className="nova-spotlight" style={{ left: `${spotlight.x}%`, top: `${spotlight.y}%` }} />
      <div className="nova-stars" />
      <div className="nova-scanline" />
    </div>
    <div className="nova-scroll-progress" style={{ width: `${progress}%` }} />

    <button className={`nova-command-orb ${dockOpen ? "is-open" : ""}`} onClick={() => setDockOpen(value => !value)} aria-label="Open Nova command center" title="Nova command center">
      {dockOpen ? <X size={20} /> : <Zap size={20} />}
      <span className="nova-orb-core" />
      <span className="nova-orb-ring" />
      <span className="nova-orb-ring nova-orb-ring-two" />
    </button>

    {dockOpen && <div className="nova-quick-dock">
      <div className="nova-dock-label"><span /> NOVA CONTROL</div>
      <button onClick={() => setPaletteOpen(true)}><Command size={15} /> Command center <kbd>⌘K</kbd></button>
      <button onClick={() => run("/account")}><Palette size={15} /> Personalize</button>
      <button onClick={() => run("/dashboard")}><Brain size={15} /> Learning cockpit</button>
    </div>}

    {dashboard && <div className="nova-dashboard-hud" aria-hidden="true">
      <div className="nova-hud-dot" /> <span>LIVE LEARNING OS</span><span className="nova-hud-divider" /><span>ADAPTIVE</span><span className="nova-hud-signal">◉</span>
    </div>}

    {paletteOpen && <div className="nova-command-backdrop" onMouseDown={() => setPaletteOpen(false)}>
      <div className="nova-command-panel" onMouseDown={event => event.stopPropagation()}>
        <div className="nova-command-header"><div className="nova-command-title"><Command size={17} /> Nova command center <span className="nova-command-live">READY</span></div><button onClick={() => setPaletteOpen(false)}><X size={17} /></button></div>
        <div className="nova-command-search"><Search size={17} /><input autoFocus value={query} onChange={event => setQuery(event.target.value)} placeholder="Jump anywhere in Nova…"/><kbd>ESC</kbd></div>
        <div className="nova-command-list">
          {filtered.map((item, index) => { const Icon = item.icon; return <button key={item.path} onMouseEnter={() => setActiveIndex(index)} onClick={() => run(item.path)} className={`nova-command-item ${activeIndex === index ? "is-active" : ""}`}><span className="nova-command-icon"><Icon size={17} /></span><span><strong>{item.label}</strong><small>{item.hint}</small></span><span className="nova-command-index">{index + 1}</span><ArrowRight size={15} /></button>; })}
          {!filtered.length && <div className="nova-command-empty"><Keyboard size={18} /> Nothing matched that search.</div>}
        </div>
        <div className="nova-command-footer"><span><kbd>↑↓</kbd> Navigate</span><span><kbd>↵</kbd> Open</span><span><kbd>ESC</kbd> Close</span></div>
      </div>
    </div>}
  </>;
}

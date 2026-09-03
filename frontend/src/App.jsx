import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { BarChart3, Home as HomeIcon, Languages, LoaderCircle } from "lucide-react";

const Home = lazy(() => import("./pages/Home"));
const DemoHome = lazy(() => import("./pages/DemoHome"));
const Chat = lazy(() => import("./pages/Chat"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Analytics = lazy(() => import("./pages/Analytics"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const Settings = lazy(() => import("./pages/Settings"));
const DemoSettings = lazy(() => import("./pages/DemoSettings"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Capabilities = lazy(() => import("./pages/Capabilities"));
const AboutNova = lazy(() => import("./pages/AboutNova"));
const TranslationMode = lazy(() => import("./pages/TranslationMode"));

const PRODUCTION_API_URL = "https://nova-api-i07q.onrender.com";
const NOVA_API_URL = import.meta.env.PROD
    ? PRODUCTION_API_URL
    : (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").trim().replace(/\/+$/, "");

function readUser() {
    try { const raw = localStorage.getItem("nova_user"); if (!raw) return null; const parsed = JSON.parse(raw); return parsed && typeof parsed === "object" ? parsed : null; }
    catch { return null; }
}
function readSessionToken() {
    try {
        const raw = localStorage.getItem("nova_session");
        if (raw) { try { const parsed = JSON.parse(raw); if (parsed?.token) return parsed.token; } catch {} return raw; }
        const user = readUser();
        return user?.session?.token || user?.token || null;
    } catch { return null; }
}
function installApiCompatibility() {
    if (window.__novaApiCompatibilityInstalled) return;
    const originalFetch = window.fetch.bind(window);
    window.__novaApiCompatibilityInstalled = true;
    window.fetch = async (input, init = {}) => {
        let url = typeof input === "string" ? input : input?.url || "";
        if (url.startsWith("http://127.0.0.1:8000") || url.startsWith("http://localhost:8000")) url = `${NOVA_API_URL}${url.replace(/^https?:\/\/(127\.0\.0\.1|localhost):8000/, "")}`;
        const headers = new Headers(init.headers || (typeof input !== "string" ? input.headers : undefined) || {});
        const token = readSessionToken();
        if (token && !headers.has("Authorization") && !headers.has("X-Nova-Session")) headers.set("X-Nova-Session", token);
        const nextInit = { ...init, headers };
        if (url.startsWith(NOVA_API_URL)) nextInit.credentials = "include";
        const response = await originalFetch(url, nextInit);
        if (response.ok && /^\/settings(?:\/reset)?$/.test(new URL(url, window.location.origin).pathname)) {
            try {
                const payload = await response.clone().json();
                if (payload?.settings && typeof payload.settings === "object") return new Response(JSON.stringify(payload.settings), { status: response.status, statusText: response.statusText, headers: response.headers });
            } catch {}
        }
        return response;
    };
}

// Install before React renders any route. Settings.jsx performs its request
// from a child effect, so installing this in App's useEffect was too late.
// This also guarantees cross-origin requests to Nova carry the HttpOnly
// session cookie via credentials: include.
installApiCompatibility();

function useAuthState() {
    const [user, setUser] = useState(readUser);
    useEffect(() => { const sync = () => setUser(readUser()); window.addEventListener("storage", sync); window.addEventListener("nova-auth-changed", sync); window.addEventListener("nova:auth", sync); const timer = window.setInterval(sync, 1000); return () => { window.removeEventListener("storage", sync); window.removeEventListener("nova-auth-changed", sync); window.removeEventListener("nova:auth", sync); window.clearInterval(timer); }; }, []);
    return user;
}
function PageLoader() { return <div className="flex min-h-screen items-center justify-center bg-[#070a13] text-white"><div className="flex flex-col items-center gap-4"><div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[.04]"><LoaderCircle className="animate-spin text-cyan-300" size={25}/></div><span className="text-xs text-slate-500">Loading Nova...</span></div></div>; }
function AuthRedirect({ children }) { const user = useAuthState(); return user ? children : <Navigate to="/login" replace />; }
function AnalyticsShortcut() { const navigate = useNavigate(); return <button onClick={() => navigate("/analytics")} title="Nova Analytics" className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-2xl border border-sky-400/20 bg-[#0b1322]/95 px-4 py-3 text-xs font-semibold text-sky-300 shadow-2xl backdrop-blur-xl transition hover:border-sky-400/40 hover:bg-[#101c30]"><BarChart3 size={16}/> Analytics</button>; }
function TranslationShortcut() { const navigate = useNavigate(); return <button onClick={() => navigate("/translate")} title="Translation mode" className="fixed bottom-5 left-5 z-50 flex items-center gap-2 rounded-2xl border border-violet-400/20 bg-[#0b1322]/95 px-4 py-3 text-xs font-semibold text-violet-300 shadow-2xl backdrop-blur-xl transition hover:border-violet-400/40 hover:bg-[#101c30]"><Languages size={16}/> Translate</button>; }
function AuthHomeButton() { const navigate = useNavigate(); return <button type="button" onClick={() => navigate("/")} title="Back to Nova home" aria-label="Back to Nova home" className="fixed left-5 top-5 z-[100] flex items-center gap-2 rounded-xl border border-white/10 bg-slate-900/80 px-3.5 py-2.5 text-sm font-medium text-slate-300 shadow-xl backdrop-blur-xl transition hover:border-cyan-400/30 hover:bg-slate-800 hover:text-white"><HomeIcon size={16}/> Home</button>; }
function AdaptiveRoute({ authenticated, demo, account }) { const user = useAuthState(); const location = useLocation(); useEffect(() => { const labels = { "/": user ? "Your learning space" : "Learn smarter", "/chat": "Learn", "/translate": "Translation", "/dashboard": "Dashboard", "/analytics": "Analytics", "/settings": "Settings", "/about": "About Nova" }; document.title = `Nova AI · ${labels[location.pathname] || "Explore"}`; }, [location.pathname, user]); if (authenticated) return user ? authenticated : demo; return user ? account : demo; }
function AppRoutes() { return <Suspense fallback={<PageLoader/>}><Routes><Route path="/" element={<><AdaptiveRoute demo={<DemoHome/>} account={<Home/>}/><TranslationShortcut/></>}/><Route path="/chat" element={<Chat/>}/><Route path="/translate" element={<TranslationMode/>}/><Route path="/settings" element={<AdaptiveRoute demo={<DemoSettings/>} account={<Settings/>}/>}/><Route path="/dashboard" element={<AuthRedirect><><Dashboard/><AnalyticsShortcut/><TranslationShortcut/></></AuthRedirect>}/><Route path="/analytics" element={<AuthRedirect><Analytics/></AuthRedirect>}/><Route path="/capabilities/:capability" element={<Capabilities/>}/><Route path="/about" element={<AboutNova/>}/><Route path="/login" element={<><AuthHomeButton/><Login/></>}/><Route path="/register" element={<><AuthHomeButton/><Register/></>}/><Route path="*" element={<NotFound/>}/></Routes></Suspense>; }
export default function App() { const locationKey = useMemo(() => window.location.pathname, []); return <BrowserRouter key={locationKey}><AppRoutes/></BrowserRouter>; }
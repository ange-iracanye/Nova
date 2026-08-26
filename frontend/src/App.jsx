import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { BarChart3, LoaderCircle } from "lucide-react";

const Home = lazy(() => import("./pages/Home"));
const DemoHome = lazy(() => import("./pages/DemoHome"));
const Chat = lazy(() => import("./pages/Chat"));
const DemoChat = lazy(() => import("./pages/DemoChat"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Analytics = lazy(() => import("./pages/Analytics"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const Settings = lazy(() => import("./pages/Settings"));
const DemoSettings = lazy(() => import("./pages/DemoSettings"));
const NotFound = lazy(() => import("./pages/NotFound"));
const Capabilities = lazy(() => import("./pages/Capabilities"));
const AboutNova = lazy(() => import("./pages/AboutNova"));

function readUser() {
    try {
        const raw = localStorage.getItem("nova_user");
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        return parsed && typeof parsed === "object" ? parsed : null;
    } catch { return null; }
}

function useAuthState() {
    const [user, setUser] = useState(readUser);
    useEffect(() => {
        const sync = () => setUser(readUser());
        window.addEventListener("storage", sync);
        window.addEventListener("nova-auth-changed", sync);
        window.addEventListener("nova:auth", sync);
        const timer = window.setInterval(sync, 1000);
        return () => {
            window.removeEventListener("storage", sync);
            window.removeEventListener("nova-auth-changed", sync);
            window.removeEventListener("nova:auth", sync);
            window.clearInterval(timer);
        };
    }, []);
    return user;
}

function PageLoader() {
    return <div className="flex min-h-screen items-center justify-center bg-[#070a13] text-white"><div className="flex flex-col items-center gap-4"><div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-white/[.04]"><LoaderCircle className="animate-spin text-cyan-300" size={25}/></div><span className="text-xs text-slate-500">Loading Nova...</span></div></div>;
}

function AuthRedirect({ children }) {
    const user = useAuthState();
    return user ? children : <Navigate to="/login" replace />;
}

function AnalyticsShortcut() {
    const navigate = useNavigate();
    return <button onClick={() => navigate("/analytics")} title="Nova Analytics" className="fixed bottom-5 right-5 z-50 flex items-center gap-2 rounded-2xl border border-sky-400/20 bg-[#0b1322]/95 px-4 py-3 text-xs font-semibold text-sky-300 shadow-2xl backdrop-blur-xl transition hover:border-sky-400/40 hover:bg-[#101c30]"><BarChart3 size={16}/> Analytics</button>;
}

function AdaptiveRoute({ authenticated, demo, account }) {
    const user = useAuthState();
    const location = useLocation();
    useEffect(() => {
        const labels = {
            "/": user ? "Your learning space" : "Learn smarter",
            "/chat": "Learn",
            "/dashboard": "Dashboard",
            "/analytics": "Analytics",
            "/settings": "Settings",
            "/about": "About Nova",
        };
        document.title = `Nova AI · ${labels[location.pathname] || "Explore"}`;
    }, [location.pathname, user]);
    if (authenticated) return user ? authenticated : demo;
    return user ? account : demo;
}

function AppRoutes() {
    return <Suspense fallback={<PageLoader />}><Routes>
        <Route path="/" element={<AdaptiveRoute demo={<DemoHome/>} account={<Home/>} />} />
        <Route path="/chat" element={<AdaptiveRoute demo={<DemoChat/>} account={<Chat/>} />} />
        <Route path="/settings" element={<AdaptiveRoute demo={<DemoSettings/>} account={<Settings/>} />} />
        <Route path="/dashboard" element={<AuthRedirect><><Dashboard/><AnalyticsShortcut/></></AuthRedirect>} />
        <Route path="/analytics" element={<AuthRedirect><Analytics/></AuthRedirect>} />
        <Route path="/capabilities/:capability" element={<Capabilities/>} />
        <Route path="/about" element={<AboutNova/>} />
        <Route path="/login" element={<Login/>} />
        <Route path="/register" element={<Register/>} />
        <Route path="*" element={<NotFound/>} />
    </Routes></Suspense>;
}

export default function App() {
    const locationKey = useMemo(() => window.location.pathname, []);
    return <BrowserRouter key={locationKey}><AppRoutes/></BrowserRouter>;
}

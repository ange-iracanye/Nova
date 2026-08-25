import React, { Suspense, useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

const NOVA_CONFIG = {
    appName: "Nova AI",
    version: "1.0.0",
    rootId: "root",
    loadingMessage: "Loading Nova...",
    loadingSubmessage: "Preparing your learning environment.",
    errorMessage: "Nova could not start correctly.",
    storageKeys: { theme: "nova_theme", lastRoute: "nova_last_route", session: "nova_session", initialized: "nova_initialized" }
};

function getApiBase() {
    const configured = (import.meta.env.VITE_API_URL || "").trim().replace(/\/+$/, "");
    if (import.meta.env.PROD && !configured) {
        throw new Error("Nova production API is not configured. Set VITE_API_URL before building the frontend.");
    }
    return configured || "http://127.0.0.1:8000";
}

const API_BASE = getApiBase();
const LOCAL_API_BASES = ["http://127.0.0.1:8000", "http://localhost:8000"];

function readSessionToken() {
    try {
        const raw = localStorage.getItem(NOVA_CONFIG.storageKeys.session);
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        return typeof parsed?.token === "string" && parsed.token.trim() ? parsed.token.trim() : null;
    } catch {
        return null;
    }
}

function normalizeApiUrl(rawUrl) {
    let url = String(rawUrl || "");
    for (const localBase of LOCAL_API_BASES) {
        if (url === localBase || url.startsWith(`${localBase}/`)) {
            url = `${API_BASE}${url.slice(localBase.length)}`;
            break;
        }
    }
    return url;
}

function installApiCredentialPolicy() {
    if (window.__novaCredentialFetchInstalled) return;
    const originalFetch = window.fetch.bind(window);
    window.fetch = (input, init = {}) => {
        const originalUrl = typeof input === "string" ? input : input?.url || "";
        const url = normalizeApiUrl(originalUrl);
        const isApiRequest = url === API_BASE || url.startsWith(`${API_BASE}/`);
        if (!isApiRequest) return originalFetch(input, init);

        const headers = new Headers(init.headers || {});
        headers.set("Accept", headers.get("Accept") || "application/json");
        const token = readSessionToken();
        if (token) headers.set("Authorization", `Bearer ${token}`);

        return originalFetch(url, { ...init, headers, credentials: "include" });
    };
    window.__novaCredentialFetchInstalled = true;
}

function initializeNova() {
    try {
        installApiCredentialPolicy();
        localStorage.setItem(NOVA_CONFIG.storageKeys.initialized, "true");
        const savedTheme = localStorage.getItem(NOVA_CONFIG.storageKeys.theme);
        document.documentElement.dataset.theme = savedTheme === "light" || savedTheme === "dark" ? savedTheme : "dark";
        document.documentElement.dataset.novaVersion = NOVA_CONFIG.version;
        document.documentElement.dataset.novaReady = "false";
        document.body.classList.add("nova-app");
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) { viewport = document.createElement("meta"); viewport.name = "viewport"; document.head.appendChild(viewport); }
        viewport.content = "width=device-width, initial-scale=1.0, viewport-fit=cover";
        let colorScheme = document.querySelector('meta[name="color-scheme"]');
        if (!colorScheme) { colorScheme = document.createElement("meta"); colorScheme.name = "color-scheme"; document.head.appendChild(colorScheme); }
        colorScheme.content = "dark";
        let themeColor = document.querySelector('meta[name="theme-color"]');
        if (!themeColor) { themeColor = document.createElement("meta"); themeColor.name = "theme-color"; document.head.appendChild(themeColor); }
        themeColor.content = "#020617";
        return true;
    } catch (error) {
        console.error("[Nova] Initialization failed:", error);
        return false;
    }
}

class NovaErrorBoundary extends React.Component {
    constructor(props) { super(props); this.state = { hasError: false, error: null }; }
    static getDerivedStateFromError(error) { return { hasError: true, error }; }
    componentDidCatch(error, errorInfo) {
        console.error("[Nova] React application error:", error);
        console.error("[Nova] Component stack:", errorInfo?.componentStack);
        try { localStorage.setItem("nova_last_error", JSON.stringify({ message: error?.message || "Unknown error", timestamp: new Date().toISOString() })); } catch { /* ignore */ }
    }
    handleReload = () => window.location.reload();
    handleReset = () => { try { localStorage.removeItem(NOVA_CONFIG.storageKeys.lastRoute); } catch { /* ignore */ } window.location.href = "/"; };
    render() {
        if (!this.state.hasError) return this.props.children;
        const errorMessage = this.state.error?.message || NOVA_CONFIG.errorMessage;
        return <div className="nova-fatal-error" role="alert"><div className="nova-fatal-error-card"><div className="nova-fatal-error-icon" aria-hidden="true">N</div><h1>Nova ran into a problem.</h1><p>The application could not finish loading correctly.</p><details><summary>Technical details</summary><pre>{errorMessage}</pre></details><div className="nova-fatal-error-actions"><button type="button" onClick={this.handleReload}>Reload Nova</button><button type="button" onClick={this.handleReset}>Return Home</button></div></div></div>;
    }
}

function NovaLoadingScreen() {
    return <div className="nova-loading-screen" role="status" aria-live="polite"><div className="nova-loading-orb" aria-hidden="true"><span>N</span></div><div className="nova-loading-content"><h1>{NOVA_CONFIG.appName}</h1><p>{NOVA_CONFIG.loadingMessage}</p><span>{NOVA_CONFIG.loadingSubmessage}</span></div><div className="nova-loading-bar" aria-hidden="true"><div /></div></div>;
}

function useNovaReady() {
    const [ready, setReady] = useState(false);
    useEffect(() => {
        let cancelled = false;
        initializeNova();
        requestAnimationFrame(() => { if (!cancelled) { document.documentElement.dataset.novaReady = "true"; setReady(true); } });
        return () => { cancelled = true; };
    }, []);
    return ready;
}

function NovaApplication() { const ready = useNovaReady(); return ready ? <App /> : <NovaLoadingScreen />; }

function installGlobalErrorHandlers() {
    window.addEventListener("error", event => console.error("[Nova] Unhandled browser error:", event.error || event.message));
    window.addEventListener("unhandledrejection", event => console.error("[Nova] Unhandled promise rejection:", event.reason));
}

function getApplicationRoot() {
    const root = document.getElementById(NOVA_CONFIG.rootId);
    if (!root) throw new Error(`Nova root element "#${NOVA_CONFIG.rootId}" was not found.`);
    return root;
}

function bootstrapNova() {
    installGlobalErrorHandlers();
    const root = ReactDOM.createRoot(getApplicationRoot());
    root.render(<React.StrictMode><NovaErrorBoundary><Suspense fallback={<NovaLoadingScreen />}><NovaApplication /></Suspense></NovaErrorBoundary></React.StrictMode>);
}

try { bootstrapNova(); } catch (error) {
    console.error("[Nova] Fatal bootstrap error:", error);
    const root = document.getElementById(NOVA_CONFIG.rootId);
    if (root) root.innerHTML = `<div class="nova-fatal-error" role="alert"><div class="nova-fatal-error-card"><div class="nova-fatal-error-icon">N</div><h1>Nova could not start.</h1><p>The frontend failed during startup.</p><button type="button" onclick="window.location.reload()">Reload Nova</button></div></div>`;
}

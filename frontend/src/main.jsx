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
    storageKeys: {
        theme: "nova_theme",
        lastRoute: "nova_last_route",
        session: "nova_session",
        initialized: "nova_initialized"
    }
};

function installApiCredentialPolicy() {
    if (window.__novaCredentialFetchInstalled) return;
    const originalFetch = window.fetch.bind(window);
    const apiBase = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");
    window.fetch = (input, init = {}) => {
        const url = typeof input === "string" ? input : input?.url || "";
        const isNovaApi = url === apiBase || url.startsWith(`${apiBase}/`);
        if (!isNovaApi) return originalFetch(input, init);
        return originalFetch(input, { ...init, credentials: "include" });
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
        if (!viewport) {
            viewport = document.createElement("meta");
            viewport.name = "viewport";
            document.head.appendChild(viewport);
        }
        viewport.content = "width=device-width, initial-scale=1.0, viewport-fit=cover";
        let colorScheme = document.querySelector('meta[name="color-scheme"]');
        if (!colorScheme) {
            colorScheme = document.createElement("meta");
            colorScheme.name = "color-scheme";
            document.head.appendChild(colorScheme);
        }
        colorScheme.content = "dark";
        let themeColor = document.querySelector('meta[name="theme-color"]');
        if (!themeColor) {
            themeColor = document.createElement("meta");
            themeColor.name = "theme-color";
            document.head.appendChild(themeColor);
        }
        themeColor.content = "#020617";
        return true;
    } catch (error) {
        console.error("[Nova] Initialization failed:", error);
        return false;
    }
}

class NovaErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }
    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }
    componentDidCatch(error, errorInfo) {
        console.error("[Nova] React application error:", error);
        console.error("[Nova] Component stack:", errorInfo?.componentStack);
        try {
            localStorage.setItem("nova_last_error", JSON.stringify({ message: error?.message || "Unknown error", timestamp: new Date().toISOString() }));
        } catch {
            // Ignore storage failures in the fallback path.
        }
    }
    handleReload = () => window.location.reload();
    handleReset = () => {
        try { localStorage.removeItem(NOVA_CONFIG.storageKeys.lastRoute); } catch { /* ignore */ }
        window.location.href = "/";
    };
    render() {
        if (!this.state.hasError) return this.props.children;
        const errorMessage = this.state.error?.message || NOVA_CONFIG.errorMessage;
        return (
            <div className="nova-fatal-error" role="alert">
                <div className="nova-fatal-error-card">
                    <div className="nova-fatal-error-icon" aria-hidden="true">N</div>
                    <h1>Nova ran into a problem.</h1>
                    <p>The application could not finish loading correctly.</p>
                    <details><summary>Technical details</summary><pre>{errorMessage}</pre></details>
                    <div className="nova-fatal-error-actions">
                        <button type="button" onClick={this.handleReload}>Reload Nova</button>
                        <button type="button" onClick={this.handleReset}>Return Home</button>
                    </div>
                </div>
            </div>
        );
    }
}

function NovaLoadingScreen() {
    return (
        <div className="nova-loading-screen" role="status" aria-live="polite">
            <div className="nova-loading-orb" aria-hidden="true"><span>N</span></div>
            <div className="nova-loading-content"><h1>{NOVA_CONFIG.appName}</h1><p>{NOVA_CONFIG.loadingMessage}</p><span>{NOVA_CONFIG.loadingSubmessage}</span></div>
            <div className="nova-loading-bar" aria-hidden="true"><div /></div>
        </div>
    );
}

function useNovaReady() {
    const [ready, setReady] = useState(false);
    useEffect(() => {
        let cancelled = false;
        const initialize = async () => {
            try {
                initializeNova();
                await new Promise(resolve => requestAnimationFrame(resolve));
                if (cancelled) return;
                document.documentElement.dataset.novaReady = "true";
                setReady(true);
            } catch (error) {
                console.error("[Nova] Startup error:", error);
                if (!cancelled) setReady(true);
            }
        };
        initialize();
        return () => { cancelled = true; };
    }, []);
    return ready;
}

function NovaApplication() {
    const ready = useNovaReady();
    return ready ? <App /> : <NovaLoadingScreen />;
}

function enableDevelopmentDiagnostics() {
    if (import.meta.env.DEV) {
        console.info(`%cNova AI v${NOVA_CONFIG.version}`, "font-weight:700;font-size:16px;");
        console.info("[Nova] Development mode enabled.");
        console.info("[Nova] Frontend initialized.");
    }
}

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
    enableDevelopmentDiagnostics();
    installGlobalErrorHandlers();
    const rootElement = getApplicationRoot();
    const root = ReactDOM.createRoot(rootElement);
    root.render(
        <React.StrictMode>
            <NovaErrorBoundary>
                <Suspense fallback={<NovaLoadingScreen />}><NovaApplication /></Suspense>
            </NovaErrorBoundary>
        </React.StrictMode>
    );
    return root;
}

try {
    bootstrapNova();
} catch (error) {
    console.error("[Nova] Fatal bootstrap error:", error);
    const root = document.getElementById(NOVA_CONFIG.rootId);
    if (root) {
        root.innerHTML = `<div class="nova-fatal-error" role="alert"><div class="nova-fatal-error-card"><div class="nova-fatal-error-icon">N</div><h1>Nova could not start.</h1><p>The frontend failed during startup.</p><button type="button" onclick="window.location.reload()">Reload Nova</button></div></div>`;
    }
}

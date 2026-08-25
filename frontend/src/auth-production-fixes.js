const PRODUCTION_API_URL = "https://nova-api-i07q.onrender.com";
const ORIGINAL_FETCH = window.fetch.bind(window);
const AUTH_TIMEOUT_MS = 60000;
const GET_DEDUP_WINDOW_MS = 5000;
const recentGets = new Map();

function apiBase() {
    return (import.meta.env.VITE_API_URL || PRODUCTION_API_URL).replace(/\/+$/, "");
}

function rewriteUrl(input) {
    const raw = typeof input === "string" ? input : input?.url || "";
    if (!raw) return input;

    let rewritten = raw;
    if (rewritten.startsWith("http://127.0.0.1:8000")) {
        rewritten = rewritten.replace("http://127.0.0.1:8000", apiBase());
    } else if (rewritten.startsWith("http://localhost:8000")) {
        rewritten = rewritten.replace("http://localhost:8000", apiBase());
    }

    try {
        const url = new URL(rewritten, window.location.origin);
        const base = new URL(apiBase());
        if (url.origin !== base.origin) return rewritten;

        // Chat's connectivity probe uses the API root. The production entry
        // point exposes /health as the canonical lightweight health check.
        if (url.pathname === "/" && url.search === "") {
            url.pathname = "/health";
        }

        const path = url.pathname;
        const legacyList = path.match(/^\/conversations\/([^/]+)$/);
        const legacyGet = path.match(/^\/conversation\/([^/]+)\/([^/]+)$/);
        const legacyRename = path.match(/^\/conversation\/([^/]+)\/([^/]+)\/rename$/);

        if (path === "/conversation/new") {
            url.pathname = "/v1/conversations";
            url.search = "";
        } else if (legacyRename) {
            url.pathname = `/v1/conversations/${encodeURIComponent(decodeURIComponent(legacyRename[2]))}`;
            url.search = "";
        } else if (legacyGet) {
            url.pathname = `/v1/conversations/${encodeURIComponent(decodeURIComponent(legacyGet[2]))}`;
            url.search = "";
        } else if (legacyList) {
            url.pathname = "/v1/conversations";
            url.search = "";
        }

        return url.toString();
    } catch {
        return rewritten;
    }
}

function isLocalDevelopment() {
    return window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
}

function readDevelopmentSessionToken() {
    if (!isLocalDevelopment()) return "";
    try {
        const raw = localStorage.getItem("nova_session");
        if (!raw) return "";
        const value = JSON.parse(raw);
        return typeof value === "string" ? value : String(value?.token || "");
    } catch {
        return "";
    }
}

function saveDevelopmentSession(data) {
    if (!isLocalDevelopment()) return;
    const session = data?.session;
    const token = data?.token || data?.access_token || data?.session_token || session?.token;
    if (!token) return;
    try {
        localStorage.setItem("nova_session", JSON.stringify({
            token: String(token),
            type: data?.token_type || session?.token_type || "Bearer"
        }));
    } catch {
        // Storage may be unavailable in private browsing.
    }
}

function installHomeContrastFix() {
    if (document.getElementById("nova-home-contrast-fix")) return;
    const style = document.createElement("style");
    style.id = "nova-home-contrast-fix";
    style.textContent = `
        body.nova-app main a.bg-white,
        body.nova-app main button.bg-white,
        body.nova-app main a[class*="bg-white"]:not([class*="bg-white/"]) {
            color: #0f172a !important;
        }
        body.nova-app main a.bg-white *,
        body.nova-app main button.bg-white * {
            color: #0f172a !important;
        }
    `;
    document.head.appendChild(style);
}

window.fetch = async function novaProductionFetch(input, init = {}) {
    const url = rewriteUrl(input);
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    if (init.headers) new Headers(init.headers).forEach((value, key) => headers.set(key, value));

    const token = readDevelopmentSessionToken();
    const path = typeof url === "string" ? url : url?.url || "";
    const isAuthRequest = /\/login$|\/register$|\/health$|\/ready$|\/auth\/session$|\/auth\/me$|\/auth\/logout$/.test(path);
    const isLoginOrRegister = /\/login$|\/register$/.test(path);

    if (token && !isAuthRequest && !headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const requestInit = {
        ...init,
        headers,
        credentials: init.credentials || "include",
    };

    const method = String(requestInit.method || "GET").toUpperCase();
    const isConversationRead = method === "GET" && /^https:\/\/[^/]+\/v1\/conversations(?:\/[^/]+)?$/.test(String(url));
    const dedupeKey = isConversationRead ? String(url) : "";

    if (dedupeKey) {
        const cached = recentGets.get(dedupeKey);
        if (cached && Date.now() - cached.time < GET_DEDUP_WINDOW_MS) {
            const response = await cached.promise;
            return response.clone();
        }
    }

    let authTimeoutId = null;
    let authController = null;
    if (isLoginOrRegister && !isLocalDevelopment()) {
        authController = new AbortController();
        authTimeoutId = window.setTimeout(() => authController.abort(), AUTH_TIMEOUT_MS);
        requestInit.signal = authController.signal;
    }

    const request = ORIGINAL_FETCH(url, requestInit);

    if (dedupeKey) {
        recentGets.set(dedupeKey, { time: Date.now(), promise: request });
        request.finally(() => {
            window.setTimeout(() => {
                const current = recentGets.get(dedupeKey);
                if (current?.promise === request) recentGets.delete(dedupeKey);
            }, GET_DEDUP_WINDOW_MS);
        }).catch(() => {});
    }

    try {
        const response = await request;

        if (isLoginOrRegister && response.ok) {
            try {
                const data = await response.clone().json();
                if (data?.success !== false) saveDevelopmentSession(data);
            } catch {
                // Leave normal response handling to the calling page.
            }
        }

        if (!isLocalDevelopment() && isLoginOrRegister && response.ok) {
            try {
                localStorage.removeItem("nova_session");
            } catch {
                // Ignore unavailable storage.
            }
        }

        return response;
    } finally {
        if (authTimeoutId !== null) window.clearTimeout(authTimeoutId);
        void authController;
    }
};

installHomeContrastFix();

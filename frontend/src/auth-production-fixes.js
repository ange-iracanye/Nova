const PRODUCTION_API_URL = "/api";
const ORIGINAL_FETCH = window.fetch.bind(window);
const AUTH_TIMEOUT_MS = 60000;
const HEALTH_CACHE_MS = 30000;
const GET_CACHE_MS = 5000;
const recentGets = new Map();
const successfulGetCache = new Map();

function apiBase() {
    return (import.meta.env.VITE_API_URL || PRODUCTION_API_URL).replace(/\/+$/, "");
}

function rewriteUrl(input) {
    const raw = typeof input === "string" ? input : input?.url || "";
    if (!raw) return input;
    let rewritten = raw;
    if (rewritten.startsWith("http://127.0.0.1:8000")) rewritten = rewritten.replace("http://127.0.0.1:8000", apiBase());
    else if (rewritten.startsWith("http://localhost:8000")) rewritten = rewritten.replace("http://localhost:8000", apiBase());
    try {
        const url = new URL(rewritten, window.location.origin);
        const base = new URL(apiBase(), window.location.origin);
        if (url.origin !== base.origin) return rewritten;
        if (url.pathname === base.pathname && url.search === "") url.pathname = `${base.pathname}/health`;
        const path = url.pathname;
        const apiPrefix = base.pathname === "/" ? "" : base.pathname;
        const relativePath = path.startsWith(`${apiPrefix}/`) ? path.slice(apiPrefix.length) : path;
        const legacyList = relativePath.match(/^\/conversations\/([^/]+)$/);
        const legacyGet = relativePath.match(/^\/conversation\/([^/]+)\/([^/]+)$/);
        const legacyRename = relativePath.match(/^\/conversation\/([^/]+)\/([^/]+)\/rename$/);
        if (relativePath === "/conversation/new") {
            url.pathname = `${apiPrefix}/v1/conversations`;
            url.search = "";
        } else if (legacyRename) {
            url.pathname = `${apiPrefix}/v1/conversations/${encodeURIComponent(decodeURIComponent(legacyRename[2]))}`;
            url.search = "";
        } else if (legacyGet) {
            url.pathname = `${apiPrefix}/v1/conversations/${encodeURIComponent(decodeURIComponent(legacyGet[2]))}`;
            url.search = "";
        } else if (legacyList) {
            url.pathname = `${apiPrefix}/v1/conversations`;
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
        localStorage.setItem("nova_session", JSON.stringify({ token: String(token), type: data?.token_type || session?.token_type || "Bearer" }));
    } catch {}
}

function installHomeContrastFix() {
    if (document.getElementById("nova-home-contrast-fix")) return;
    const style = document.createElement("style");
    style.id = "nova-home-contrast-fix";
    style.textContent = `
        main a.bg-white,
        main button.bg-white,
        main a[class*="bg-white"]:not([class*="bg-white/"]) {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }
        main a.bg-white *,
        main button.bg-white * {
            color: #0f172a !important;
            -webkit-text-fill-color: #0f172a !important;
        }
        main a.bg-white svg,
        main button.bg-white svg {
            color: #0f172a !important;
            stroke: currentColor !important;
        }
    `;
    document.head.appendChild(style);
}

function isCacheableGet(method, url) {
    return method === "GET" && /^https?:\/\/[^/]+\/(?:api\/)?(?:health|ready|v1\/conversations(?:\/[^/]+)?)$/.test(String(url));
}

function cacheTtl(url) {
    return /\/health$|\/ready$/.test(String(url)) ? HEALTH_CACHE_MS : GET_CACHE_MS;
}

window.fetch = async function novaProductionFetch(input, init = {}) {
    const url = rewriteUrl(input);
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    if (init.headers) new Headers(init.headers).forEach((value, key) => headers.set(key, value));
    const token = readDevelopmentSessionToken();
    const path = typeof url === "string" ? url : url?.url || "";
    const isHealthRequest = /\/health$|\/ready$/.test(path);
    const isAuthRequest = /\/login$|\/register$|\/health$|\/ready$|\/auth\/session$|\/auth\/me$|\/auth\/logout$/.test(path);
    const isLoginOrRegister = /\/login$|\/register$/.test(path);
    if (token && !isAuthRequest && !headers.has("Authorization")) headers.set("Authorization", `Bearer ${token}`);
    const requestInit = { ...init, headers, credentials: isHealthRequest ? "omit" : (init.credentials || "include") };
    const method = String(requestInit.method || "GET").toUpperCase();
    const cacheableGet = isCacheableGet(method, url);
    const cacheKey = cacheableGet ? String(url) : "";
    if (cacheKey) {
        const cached = successfulGetCache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < cacheTtl(url)) return cached.response.clone();
        if (cached) successfulGetCache.delete(cacheKey);
        const inFlight = recentGets.get(cacheKey);
        if (inFlight) {
            try { return (await inFlight).clone(); } catch { recentGets.delete(cacheKey); }
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
    if (cacheKey) recentGets.set(cacheKey, request);
    try {
        const response = await request;
        if (cacheKey && response.ok) successfulGetCache.set(cacheKey, { timestamp: Date.now(), response: response.clone() });
        if (isLoginOrRegister && response.ok) {
            try {
                const data = await response.clone().json();
                if (data?.success !== false) saveDevelopmentSession(data);
            } catch {}
        }
        if (!isLocalDevelopment() && isLoginOrRegister && response.ok) {
            try { localStorage.removeItem("nova_session"); } catch {}
        }
        return response;
    } finally {
        if (cacheKey && recentGets.get(cacheKey) === request) recentGets.delete(cacheKey);
        if (authTimeoutId !== null) window.clearTimeout(authTimeoutId);
        void authController;
    }
};

installHomeContrastFix();

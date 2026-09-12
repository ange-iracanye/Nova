const ORIGINAL_FETCH = window.fetch.bind(window);
const API_HOST = "nova-api-i07q.onrender.com";

function isApiPath(pathname) {
    return pathname === "/" || pathname === "/api" || pathname.startsWith("/api/") ||
        pathname === "/health" || pathname === "/ready" || pathname === "/status" ||
        pathname === "/login" || pathname === "/register" || pathname.startsWith("/auth/") ||
        pathname === "/chat" || pathname === "/stream" || pathname.startsWith("/chat/") ||
        pathname === "/dashboard" || pathname.startsWith("/dashboard/") ||
        pathname === "/settings" || pathname.startsWith("/settings/") ||
        pathname === "/conversations" || pathname.startsWith("/conversations/") ||
        pathname === "/conversation/new" || pathname.startsWith("/conversation/") ||
        pathname === "/history" || pathname.startsWith("/history/") ||
        pathname === "/memory" || pathname.startsWith("/memory/") ||
        pathname === "/account" || pathname.startsWith("/account/") ||
        pathname === "/demo/session" || pathname.startsWith("/demo/session/") ||
        pathname === "/demo/chat/stream" || pathname.startsWith("/demo/chat/") ||
        pathname === "/frontend/config" || pathname === "/frontend/ping" ||
        pathname === "/statistics" || pathname.startsWith("/v1/") ||
        /^\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?:\/.*)?$/i.test(pathname);
}

function getStoredEmail() {
    try {
        const raw = localStorage.getItem("nova_user");
        if (!raw) return "";
        const user = JSON.parse(raw);
        return typeof user?.email === "string" ? user.email.trim() : "";
    } catch { return ""; }
}

function getStoredSessionToken() {
    try {
        const raw = localStorage.getItem("nova_session");
        if (!raw) return "";
        const session = JSON.parse(raw);
        return typeof session?.token === "string" ? session.token.trim() : "";
    } catch { return ""; }
}

function storeSession(session) {
    const token = typeof session?.token === "string" ? session.token.trim() : "";
    if (!token) return false;
    try {
        localStorage.setItem("nova_session", JSON.stringify({ token, type: session?.type || "Bearer" }));
        if (session?.email) localStorage.setItem("nova_user", JSON.stringify({ email: String(session.email).trim().toLowerCase() }));
        return true;
    } catch { return false; }
}

function clearStoredSession() {
    try { localStorage.removeItem("nova_session"); } catch {}
}

function rewriteLegacyRoute(pathname) {
    const email = getStoredEmail();
    const encodedEmail = email ? encodeURIComponent(email) : "";
    if (pathname === "/stream") return "/chat/stream";
    if (pathname === "/conversations" && encodedEmail) return `/conversations/${encodedEmail}`;
    const match = pathname.match(/^\/conversation\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})(\/.*)?$/i);
    if (match && encodedEmail) return `/conversation/${encodedEmail}/${match[1]}${match[2] || ""}`;
    const uuidOnly = pathname.match(/^\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i);
    if (uuidOnly && encodedEmail) return `/conversation/${encodedEmail}/${uuidOnly[1]}`;
    return pathname;
}

function rewrite(input) {
    const raw = typeof input === "string" ? input : input?.url || "";
    if (!raw) return input;
    try {
        const url = new URL(raw, window.location.origin);
        if (url.hostname === API_HOST) return url.toString();
        if (url.origin !== window.location.origin || !isApiPath(url.pathname)) return raw;
        let pathname = url.pathname;
        if (pathname === "/api" || pathname === "/api/") pathname = "/health";
        else if (pathname.startsWith("/api/")) pathname = pathname.slice(4) || "/health";
        else if (pathname === "/") pathname = "/health";
        pathname = rewriteLegacyRoute(pathname);
        url.protocol = "https:";
        url.hostname = API_HOST;
        url.port = "";
        url.pathname = pathname;
        return url.toString();
    } catch { return raw; }
}

function installLandingContrastFix() {
    if (document.getElementById("nova-landing-contrast-fix")) return;
    const style = document.createElement("style");
    style.id = "nova-landing-contrast-fix";
    style.textContent = `
        main a.bg-white, main button.bg-white, main a[class*="bg-white"]:not([class*="bg-white/"]) { color: #2563eb !important; -webkit-text-fill-color: #2563eb !important; }
        main a.bg-white *, main button.bg-white * { color: #2563eb !important; -webkit-text-fill-color: #2563eb !important; }
        main a.bg-white svg, main button.bg-white svg { color: #2563eb !important; stroke: #2563eb !important; }
    `;
    document.head.appendChild(style);
}

function recoverStaleConversation(pathname) {
    if (!/\/conversation\/[^/]+\/[0-9a-f-]{36}$/i.test(pathname) && !/\/v1\/conversations\/[0-9a-f-]{36}$/i.test(pathname)) return;
    try { localStorage.removeItem("nova_current_conversation"); } catch {}
    try {
        if (sessionStorage.getItem("nova_stale_conversation_reloaded")) return;
        sessionStorage.setItem("nova_stale_conversation_reloaded", "1");
        window.location.reload();
    } catch {}
}

let sessionRecoveryPromise = null;

async function recoverSessionFromCookie() {
    if (sessionRecoveryPromise) return sessionRecoveryPromise;
    sessionRecoveryPromise = (async () => {
        try {
            const response = await ORIGINAL_FETCH(`https://${API_HOST}/auth/session`, {
                method: "GET",
                credentials: "include",
                headers: { Accept: "application/json" },
            });
            if (!response.ok) return false;
            const data = await response.json().catch(() => null);
            return !!(data?.authenticated && data?.session?.token && storeSession(data.session));
        } catch { return false; }
        finally { sessionRecoveryPromise = null; }
    })();
    return sessionRecoveryPromise;
}

async function fetchWithAuthRecovery(requestInput, requestInit, rewritten) {
    let response = await ORIGINAL_FETCH(requestInput, requestInit);
    const pathname = (() => { try { return new URL(rewritten, window.location.origin).pathname; } catch { return ""; } })();
    const isAuthEndpoint = pathname === "/login" || pathname === "/register" || pathname === "/auth/session" || pathname === "/auth/me";
    if (response.status === 401 && !isAuthEndpoint) {
        const recovered = await recoverSessionFromCookie();
        if (recovered) {
            const headers = new Headers(requestInit.headers || {});
            headers.delete("Authorization");
            headers.delete("X-Nova-Session");
            const token = getStoredSessionToken();
            if (token) headers.set("X-Nova-Session", token);
            response = await ORIGINAL_FETCH(requestInput, { ...requestInit, headers, credentials: "include" });
        }
        if (response.status === 401) clearStoredSession();
    }
    if (response.status === 404) recoverStaleConversation(pathname);
    return response;
}

window.fetch = function novaProductionFetch(input, init = {}) {
    const originalUrl = typeof input === "string" ? input : input?.url || "";
    const rewritten = rewrite(input);
    if (rewritten === originalUrl || !rewritten) return ORIGINAL_FETCH(input, init);
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    if (init.headers) new Headers(init.headers).forEach((value, key) => headers.set(key, value));
    const sessionToken = getStoredSessionToken();
    if (sessionToken && !headers.has("X-Nova-Session") && !headers.has("Authorization")) headers.set("X-Nova-Session", sessionToken);
    const requestInit = { ...init, headers, credentials: init.credentials || "include" };
    let requestInput = rewritten;
    if (input instanceof Request) {
        try { requestInput = new Request(rewritten, input); } catch { requestInput = rewritten; }
    }
    return fetchWithAuthRecovery(requestInput, requestInit, rewritten);
};

installLandingContrastFix();
if (!getStoredSessionToken()) recoverSessionFromCookie();

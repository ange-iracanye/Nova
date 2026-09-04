const ORIGINAL_FETCH = window.fetch.bind(window);
const API_HOST = "nova-api-i07q.onrender.com";

function isApiPath(pathname) {
    return pathname === "/" || pathname === "/api" || pathname.startsWith("/api/") ||
        pathname === "/health" || pathname === "/ready" || pathname === "/status" ||
        pathname === "/login" || pathname === "/register" || pathname.startsWith("/auth/") ||
        pathname === "/chat" || pathname.startsWith("/chat/") ||
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

        url.protocol = "https:";
        url.hostname = API_HOST;
        url.port = "";
        url.pathname = pathname;
        return url.toString();
    } catch {
        return raw;
    }
}

function installLandingContrastFix() {
    if (document.getElementById("nova-landing-contrast-fix")) return;
    const style = document.createElement("style");
    style.id = "nova-landing-contrast-fix";
    style.textContent = `
        main a.bg-white,
        main button.bg-white,
        main a[class*="bg-white"]:not([class*="bg-white/"]) {
            color: #2563eb !important;
            -webkit-text-fill-color: #2563eb !important;
        }
        main a.bg-white *,
        main button.bg-white * {
            color: #2563eb !important;
            -webkit-text-fill-color: #2563eb !important;
        }
        main a.bg-white svg,
        main button.bg-white svg {
            color: #2563eb !important;
            stroke: #2563eb !important;
        }
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

window.fetch = function novaProductionFetch(input, init = {}) {
    const originalUrl = typeof input === "string" ? input : input?.url || "";
    const rewritten = rewrite(input);

    if (rewritten === originalUrl || !rewritten) return ORIGINAL_FETCH(input, init);

    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    if (init.headers) new Headers(init.headers).forEach((value, key) => headers.set(key, value));

    const requestInit = { ...init, headers, credentials: init.credentials || "include" };
    let requestInput = rewritten;
    if (input instanceof Request) {
        try { requestInput = new Request(rewritten, input); } catch { requestInput = rewritten; }
    }

    const promise = ORIGINAL_FETCH(requestInput, requestInit);
    promise.then(response => {
        if (response.status === 404) {
            try { recoverStaleConversation(new URL(rewritten, window.location.origin).pathname); } catch {}
        }
    }).catch(() => {});
    return promise;
};

installLandingContrastFix();

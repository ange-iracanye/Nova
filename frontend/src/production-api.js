const ORIGINAL_FETCH = window.fetch.bind(window);
const API_PREFIX = "/api";
const API_HOST = "nova-api-i07q.onrender.com";

function shouldProxy(pathname) {
    return pathname === "/health" || pathname === "/ready" || pathname === "/login" || pathname === "/register" ||
        pathname === "/chat/stream" || pathname === "/dashboard" || pathname === "/settings" || pathname.startsWith("/settings/") ||
        pathname === "/conversations" || pathname.startsWith("/conversations/") || pathname === "/conversation/new" ||
        pathname.startsWith("/conversation/") || pathname === "/demo/session" || pathname === "/demo/chat/stream" ||
        pathname.startsWith("/v1/") || /^\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(pathname);
}

function rewrite(input) {
    const raw = typeof input === "string" ? input : input?.url || "";
    if (!raw) return input;
    try {
        const url = new URL(raw, window.location.origin);
        if (url.hostname === API_HOST) {
            url.pathname = `${API_PREFIX}${url.pathname === "/" ? "/health" : url.pathname}`;
            return url.toString();
        }
        if (url.origin !== window.location.origin || url.pathname.startsWith(`${API_PREFIX}/`) || url.pathname === API_PREFIX) return raw;
        if (shouldProxy(url.pathname)) {
            url.pathname = `${API_PREFIX}${url.pathname}`;
            return url.toString();
        }
        return raw;
    } catch {
        return raw;
    }
}

window.fetch = function novaSameOriginFetch(input, init = {}) {
    const rewritten = rewrite(input);
    if (rewritten === input) return ORIGINAL_FETCH(input, init);
    if (input instanceof Request) {
        try { return ORIGINAL_FETCH(new Request(rewritten, input), { ...init, credentials: init.credentials || "include" }); }
        catch { return ORIGINAL_FETCH(rewritten, { ...init, credentials: init.credentials || "include" }); }
    }
    return ORIGINAL_FETCH(rewritten, { ...init, credentials: init.credentials || "include" });
};

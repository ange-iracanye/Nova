const PRODUCTION_API_URL = "https://nova-api-i07q.onrender.com";
const ORIGINAL_FETCH = window.fetch.bind(window);
const AUTH_TIMEOUT_MS = 60000;

function apiBase() {
    return (import.meta.env.VITE_API_URL || PRODUCTION_API_URL).replace(/\/+$/, "");
}

function rewriteUrl(input) {
    const raw = typeof input === "string" ? input : input?.url || "";
    if (!raw) return input;
    if (raw.startsWith("http://127.0.0.1:8000")) {
        return raw.replace("http://127.0.0.1:8000", apiBase());
    }
    if (raw.startsWith("http://localhost:8000")) {
        return raw.replace("http://localhost:8000", apiBase());
    }
    return input;
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

    let requestInit = {
        ...init,
        headers,
        credentials: init.credentials || "include",
    };

    // Render's free web services can take a while to wake from sleep. The
    // login page historically supplied a 10s AbortController, which could
    // abort a perfectly valid cold-start request before the API responded.
    // Give authentication requests their own 60s budget in production.
    let authTimeoutId = null;
    let authController = null;
    if (isLoginOrRegister && !isLocalDevelopment()) {
        authController = new AbortController();
        authTimeoutId = window.setTimeout(() => authController.abort(), AUTH_TIMEOUT_MS);
        requestInit.signal = authController.signal;
    }

    try {
        const response = await ORIGINAL_FETCH(url, requestInit);

        if (isLoginOrRegister && response.ok) {
            try {
                const data = await response.clone().json();
                if (data?.success !== false) saveDevelopmentSession(data);
            } catch {
                // Leave normal response handling to the calling page.
            }
        }

        // Production authentication uses an HttpOnly, Secure session cookie.
        // Never persist that bearer token in localStorage where XSS could read it.
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
    }
};

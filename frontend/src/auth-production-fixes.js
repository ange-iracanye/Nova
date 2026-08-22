const PRODUCTION_API_URL = "https://nova-api-i07q.onrender.com";
const ORIGINAL_FETCH = window.fetch.bind(window);

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

function readSessionToken() {
    try {
        const raw = localStorage.getItem("nova_session");
        if (!raw) return "";
        const value = JSON.parse(raw);
        return typeof value === "string" ? value : String(value?.token || "");
    } catch {
        return "";
    }
}

function saveSession(data) {
    const session = data?.session;
    const token = data?.token || data?.access_token || data?.session_token || session?.token;
    if (!token) return;
    try {
        localStorage.setItem("nova_session", JSON.stringify({
            token: String(token),
            type: data?.token_type || session?.token_type || "Bearer"
        }));
    } catch {
        // Storage may be unavailable in private browsing. The request itself still works.
    }
}

window.fetch = async function novaProductionFetch(input, init = {}) {
    let url = rewriteUrl(input);
    const headers = new Headers(input instanceof Request ? input.headers : undefined);
    if (init.headers) new Headers(init.headers).forEach((value, key) => headers.set(key, value));

    const token = readSessionToken();
    const path = typeof url === "string" ? url : url?.url || "";
    const isAuthRequest = /\/login$|\/register$|\/health$|\/auth\/session$|\/auth\/me$|\/auth\/logout$/.test(path);
    if (token && !isAuthRequest && !headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await ORIGINAL_FETCH(url, { ...init, headers });

    if (/\/login$|\/register$/.test(path) && response.ok) {
        try {
            const data = await response.clone().json();
            if (data?.success !== false) saveSession(data);
        } catch {
            // Leave normal response handling to the calling page.
        }
    }

    return response;
};

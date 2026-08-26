/* eslint-disable no-undef */
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const PRODUCTION_API_URL = "https://nova-api-i07q.onrender.com";

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "VITE_");
    const configuredApiUrl = (env.VITE_API_URL || "").trim().replace(/\/$/, "");
    const apiUrl = configuredApiUrl || (mode === "production" ? PRODUCTION_API_URL : "");

    function productionApiEndpoint() {
        return {
            name: "nova-production-api-endpoint",
            enforce: "post",
            transform(code, id) {
                if (!apiUrl || !/\.(jsx?|tsx?)$/.test(id)) return null;
                const legacy = "http://127.0.0.1:8000";
                const localhost = "http://localhost:8000";
                let next = code;
                next = next.split(legacy).join(apiUrl);
                next = next.split(localhost).join(apiUrl);
                if (next === code) return null;
                return { code: next, map: null };
            },
        };
    }

    function novaProductionRuntime() {
        return {
            name: "nova-production-runtime",
            enforce: "post",
            transform(code, id) {
                if (!id.endsWith("/src/main.jsx")) return null;
                return {
                    code: `${code}\nimport "./auth-production-fixes.js";\nimport "./chat-fixes.css";\n`,
                    map: null,
                };
            },
        };
    }

    function novaChatProductionFixes() {
        return {
            name: "nova-chat-production-fixes",
            enforce: "post",
            transform(code, id) {
                if (!id.endsWith("/src/pages/Chat.jsx")) return null;
                let next = code;

                // Health checks must not poll every few seconds. A 30-second
                // cadence avoids browser/edge rate limiting while still keeping
                // the status indicator reasonably fresh.
                next = next.replace(
                    /setInterval\(\s*checkBackend,\s*3000\s*\)/,
                    "setInterval(checkBackend, 30000)"
                );

                // Use the authenticated V1 conversation API instead of the
                // legacy email-in-URL endpoints.
                next = next.replace(
                    /`\$\{API_URL\}\/conversations\/\$\{encodeURIComponent\(\s*user\.email\s*\)\}`/m,
                    "`${API_URL}/v1/conversations`"
                );
                next = next.replace(
                    /`\$\{API_URL\}\/conversation\/\$\{encodeURIComponent\(\s*user\.email\s*\)\}\/\$\{encodeURIComponent\(id\)\}`/m,
                    "`${API_URL}/v1/conversations/${encodeURIComponent(id)}`"
                );
                next = next.replace(
                    /`\$\{API_URL\}\/conversation\/new`/g,
                    "`${API_URL}/v1/conversations`"
                );

                // The old callback dependency accidentally contained an array
                // inside its dependency array, creating a fresh dependency on
                // every render and repeatedly re-running chat initialization.
                next = next.replace(
                    /\[\s*\[\s*demo,\s*navigate,\s*scrollBottom,\s*mode,\s*\]\s*\]/m,
                    "[demo, navigate, scrollBottom, mode]"
                );

                // Health endpoint, not the API root.
                next = next.replace(
                    /fetch\(`\$\{API_URL\}\/`,\s*\{\s*cache:\s*"no-store"\s*\}\)/,
                    'fetch(`${API_URL}/health`, { cache: "no-store" })'
                );

                next = next.replace(
                    /previous\.slice\(0, index\)/,
                    'previous.slice(0, Math.max(0, index - 1))'
                );
                next = next.replace(
                    /const \[sidebar, setSidebar\] = useState\(true\);/,
                    'const [sidebar, setSidebar] = useState(() => typeof window !== "undefined" && window.innerWidth >= 768);'
                );

                return next === code ? null : { code: next, map: null };
            },
        };
    }

    function novaDashboardProductionFixes() {
        return {
            name: "nova-dashboard-production-fixes",
            enforce: "post",
            transform(code, id) {
                if (!id.endsWith("/src/pages/Dashboard.jsx")) return null;
                const next = code.replace(
                    /`\$\{API_URL\}\/dashboard\?email=\$\{encodeURIComponent\(\s*currentUser\.email\s*\)\}`/m,
                    "`${API_URL}/v1/dashboard`"
                );
                return next === code ? null : { code: next, map: null };
            },
        };
    }

    return {
        plugins: [
            react(),
            tailwindcss(),
            productionApiEndpoint(),
            novaProductionRuntime(),
            novaChatProductionFixes(),
            novaDashboardProductionFixes(),
        ],
        define: {
            "import.meta.env.VITE_API_URL": JSON.stringify(apiUrl),
        },
    };
});

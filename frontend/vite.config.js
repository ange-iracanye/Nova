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

                // The source currently polls every 3 seconds. Keep the health
                // indicator lightweight even if a future refactor restores the
                // shorter interval.
                next = next.replace(
                    /setInterval\(\s*checkBackend,\s*3000\s*\)/g,
                    "setInterval(checkBackend, 30000)"
                );

                // Replace the exact legacy conversation URLs wherever they are
                // present. The runtime fetch wrapper also protects older builds.
                next = next.replace(
                    /`\$\{API_URL\}\/conversations\/\$\{encodeURIComponent\(\s*user\.email\s*\)\}`/g,
                    "`${API_URL}/v1/conversations`"
                );
                next = next.replace(
                    /`\$\{API_URL\}\/conversation\/\$\{encodeURIComponent\(\s*user\.email\s*\)\}\/\$\{encodeURIComponent\(id\)\}`/g,
                    "`${API_URL}/v1/conversations/${encodeURIComponent(id)}`"
                );
                next = next.replace(
                    /`\$\{API_URL\}\/conversation\/new`/g,
                    "`${API_URL}/v1/conversations`"
                );

                // Fix the actual nested dependency array in Chat.jsx. This is
                // intentionally broad about whitespace so formatting changes
                // cannot silently reintroduce the render/effect loop.
                next = next.replace(
                    /\[\s*\[\s*demo\s*,\s*navigate\s*,\s*scrollBottom\s*,\s*mode\s*,?\s*\]\s*\]/g,
                    "[demo, navigate, scrollBottom, mode]"
                );

                // The health probe should use the explicit health endpoint.
                next = next.replace(
                    /fetch\(\s*`\$\{API_URL\}\/`\s*,/g,
                    "fetch(`${API_URL}/health`,"
                );

                next = next.replace(
                    /previous\.slice\(0, index\)/g,
                    "previous.slice(0, Math.max(0, index - 1))"
                );
                next = next.replace(
                    /const \[sidebar, setSidebar\] = useState\(true\);/g,
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
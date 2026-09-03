/* eslint-disable no-undef */
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Production always uses Nova's known live API endpoint. This prevents a stale
// or incorrect Render VITE_API_URL value from being baked into the static bundle.
const PRODUCTION_API_URL = "https://nova-api-i07q.onrender.com";

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "VITE_");
    const configuredApiUrl = (env.VITE_API_URL || "").trim().replace(/\/$/, "");
    const apiUrl = mode === "production"
        ? PRODUCTION_API_URL
        : (configuredApiUrl || "http://127.0.0.1:8000");

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

                next = next.replace(
                    /\/\* =======================================================\s*BACKEND CHECK\s*======================================================= \*\/[\s\S]*?\/\* =======================================================\s*DEMO SESSION\s*======================================================= \*\//,
                    `/* =======================================================\n     BACKEND CHECK\n     ======================================================= */\n\n  const checkBackend = useCallback(async () => {\n    try {\n      const r = await fetch(\`${apiUrl}/health\`, { cache: "no-store" });\n      if (mountedRef.current) setBackend(r.ok);\n    } catch {\n      if (mountedRef.current) setBackend(false);\n    }\n  }, []);\n\n  useEffect(() => {\n    checkBackend();\n  }, [checkBackend]);\n\n  /* =======================================================\n     DEMO SESSION\n     ======================================================= */`
                );

                next = next.replace(
                    /\n\s*const interval\s*=\s*setInterval\([\s\S]*?\);\s*\n\s*return \(\) => \{\s*\n\s*clearInterval\(interval\);\s*\n\s*\};/m,
                    ""
                );

                next = next.replace(/\$\{API_URL\}\/conversations\/\$\{encodeURIComponent\(\s*user\.email\s*\)\}/g, "${API_URL}/v1/conversations");
                next = next.replace(/\$\{API_URL\}\/conversation\/\$\{encodeURIComponent\(\s*user\.email\s*\)\}\/\$\{encodeURIComponent\(id\)\}/g, "${API_URL}/v1/conversations/${encodeURIComponent(id)}");
                next = next.replace(/\$\{API_URL\}\/conversation\/new/g, "${API_URL}/v1/conversations");
                next = next.replace(/\[\s*\[\s*demo\s*,\s*navigate\s*,\s*scrollBottom\s*,\s*mode\s*,?\s*\]\s*\]/g, "[demo, navigate, scrollBottom, mode]");
                next = next.replace(/\$\{API_URL\}\/dashboard\?email=\$\{encodeURIComponent\(\s*currentUser\.email\s*\)\}/g, "${API_URL}/v1/dashboard");
                next = next.replace(/previous\.slice\(0, index\)/g, "previous.slice(0, Math.max(0, index - 1))");
                next = next.replace(/const \[sidebar, setSidebar\] = useState\(true\);/g, 'const [sidebar, setSidebar] = useState(() => typeof window !== "undefined" && window.innerWidth >= 768);');

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
        ],
        define: {
            "import.meta.env.VITE_API_URL": JSON.stringify(apiUrl),
        },
    };
});

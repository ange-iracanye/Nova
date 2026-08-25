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
                next = next.replace(/fetch\(\`\$\{API_URL\}\/\`,\s*\{\s*cache:\s*"no-store"\s*\}\)/, 'fetch(`${API_URL}/health`, { cache: "no-store" })');
                next = next.replace(/previous\.slice\(0, index\)/, 'previous.slice(0, Math.max(0, index - 1))');
                next = next.replace(/const \[sidebar, setSidebar\] = useState\(true\);/, 'const [sidebar, setSidebar] = useState(() => typeof window !== "undefined" && window.innerWidth >= 768);');
                next = next.replace(
                    /\[\s*\[\s*demo,\s*navigate,\s*scrollBottom,\s*mode,\s*\]\s*\]/m,
                    "[demo, navigate, scrollBottom, mode]"
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

    function novaHomeContrastFixes() {
        return {
            name: "nova-home-contrast-fixes",
            enforce: "post",
            transform(code, id) {
                if (!id.endsWith("/src/pages/Home.jsx") && !id.endsWith("/src/pages/DemoHome.jsx")) return null;
                // Keep the bright CTA cards readable even if a global Tailwind
                // rule changes the default text color. The slate surface keeps
                // the existing design while making the labels unambiguous.
                const next = code.replace(/bg-white/g, "bg-slate-100");
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
            novaHomeContrastFixes(),
        ],
        define: {
            "import.meta.env.VITE_API_URL": JSON.stringify(apiUrl),
        },
    };
});

import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), "VITE_");
    const apiUrl = (env.VITE_API_URL || "").trim().replace(/\/$/, "");

    if (mode === "production" && !apiUrl) {
        throw new Error(
            "VITE_API_URL is required for production builds. Set it to the public Nova API URL."
        );
    }

    function productionApiEndpoint() {
        return {
            name: "nova-production-api-endpoint",
            enforce: "post",
            transform(code, id) {
                if (!apiUrl || !/\.(jsx?|tsx?)$/.test(id)) {
                    return null;
                }
                const legacy = "http://127.0.0.1:8000";
                if (!code.includes(legacy)) {
                    return null;
                }
                return {
                    code: code.split(legacy).join(apiUrl),
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
                if (id.endsWith("/src/main.jsx")) {
                    return {
                        code: `${code}\nimport "./chat-fixes.css";\n`,
                        map: null,
                    };
                }

                if (!id.endsWith("/src/pages/Chat.jsx")) {
                    return null;
                }

                let next = code;

                next = next.replace(
                    /fetch\(\`\$\{API_URL\}\/\`,\s*\{\s*cache:\s*"no-store"\s*\}\)/,
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

    return {
        plugins: [
            react(),
            tailwindcss(),
            productionApiEndpoint(),
            novaChatProductionFixes(),
        ],
    };
});

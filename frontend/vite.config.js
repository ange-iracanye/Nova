import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => {
    // Vite intentionally does not expose process.env in browser-oriented
    // config files. loadEnv gives the config the same .env/.env.local values
    // that Vite uses for import.meta.env without requiring Node globals.
    const env = loadEnv(mode, process.cwd(), "VITE_");
    const apiUrl = (env.VITE_API_URL || "").trim().replace(/\/$/, "");

    // Never ship a production bundle that silently points at localhost.
    // Local development keeps the historical localhost fallback.
    if (mode === "production" && !apiUrl) {
        throw new Error(
            "VITE_API_URL is required for production builds. Set it to the public Nova API URL."
        );
    }

    // V1 still has a few legacy pages with an inline localhost API constant.
    // Rewrite that literal only during the production build so the existing UI
    // stays unchanged while Render can point the browser at the real API.
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

    return {
        plugins: [
            react(),
            tailwindcss(),
            productionApiEndpoint(),
        ],
    };
});

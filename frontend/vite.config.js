import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

const apiUrl = (process.env.VITE_API_URL || "").trim().replace(/\/$/, "");

// V1 currently has a few legacy pages with an inline localhost API constant.
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

export default defineConfig({
    plugins: [
        react(),
        tailwindcss(),
        productionApiEndpoint(),
    ],
});

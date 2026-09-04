const http = require("node:http");
const https = require("node:https");
const fs = require("node:fs");
const path = require("node:path");
const { URL } = require("node:url");

const PORT = Number(process.env.PORT || 10000);
const HOST = "0.0.0.0";
const API_ORIGIN = "https://nova-api-i07q.onrender.com";
const DIST_DIR = path.join(__dirname, "dist");

const MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".ico": "image/x-icon",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
};

function proxyApi(req, res) {
    const incoming = new URL(req.url, "http://nova-frontend.local");
    const backendPath = incoming.pathname === "/api" || incoming.pathname === "/api/"
        ? "/health"
        : incoming.pathname.replace(/^\/api(?=\/|$)/, "") || "/";
    const target = new URL(backendPath + incoming.search, API_ORIGIN);
    const headers = { ...req.headers, host: target.host };
    delete headers.connection;
    delete headers["content-length"];

    const request = https.request(target, {
        method: req.method,
        headers,
    }, upstream => {
        const responseHeaders = { ...upstream.headers };
        delete responseHeaders["content-length"];
        res.writeHead(upstream.statusCode || 502, responseHeaders);
        upstream.pipe(res);
    });

    request.on("error", error => {
        if (!res.headersSent) {
            res.writeHead(502, {
                "content-type": "application/json; charset=utf-8",
                "cache-control": "no-store",
            });
            res.end(JSON.stringify({
                success: false,
                error: "API proxy unavailable",
                detail: error.message,
            }));
        } else {
            res.destroy(error);
        }
    });

    req.pipe(request);
}

function serveFile(req, res) {
    let requested = decodeURIComponent(new URL(req.url, "http://localhost").pathname);
    if (requested === "/") requested = "/index.html";
    const candidate = path.normalize(path.join(DIST_DIR, requested));
    const safeCandidate = candidate.startsWith(DIST_DIR + path.sep)
        ? candidate
        : path.join(DIST_DIR, "index.html");

    fs.stat(safeCandidate, (error, stats) => {
        if (!error && stats.isFile()) {
            const ext = path.extname(safeCandidate).toLowerCase();
            res.writeHead(200, {
                "content-type": MIME_TYPES[ext] || "application/octet-stream",
                "cache-control": ext === ".html"
                    ? "no-store, max-age=0, must-revalidate"
                    : "public, max-age=31536000, immutable",
            });
            fs.createReadStream(safeCandidate).pipe(res);
            return;
        }

        const index = path.join(DIST_DIR, "index.html");
        res.writeHead(200, {
            "content-type": "text/html; charset=utf-8",
            "cache-control": "no-store, max-age=0, must-revalidate",
        });
        fs.createReadStream(index).pipe(res);
    });
}

const server = http.createServer((req, res) => {
    if (req.url === "/api" || req.url.startsWith("/api/")) {
        proxyApi(req, res);
        return;
    }
    serveFile(req, res);
});

server.listen(PORT, HOST, () => {
    console.log(`Nova frontend listening on ${HOST}:${PORT}`);
    console.log(`API proxy target: ${API_ORIGIN}`);
});

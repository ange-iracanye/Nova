const http = require("node:http");
const https = require("node:https");
const fs = require("node:fs");
const path = require("node:path");
const zlib = require("node:zlib");
const { URL } = require("node:url");

const PORT = Number(process.env.PORT || 10000);
const HOST = "0.0.0.0";
const API_ORIGIN = "https://nova-api-i07q.onrender.com";
const DIST_DIR = path.join(__dirname, "dist");
const API_AGENT = new https.Agent({ keepAlive: true, maxSockets: 64, maxFreeSockets: 16, timeout: 30_000, freeSocketTimeout: 15_000 });

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
    const headers = { ...req.headers, host: target.host, connection: "keep-alive" };
    delete headers.connection;
    delete headers["content-length"];
    headers.host = target.host;

    const request = https.request(target, {
        method: req.method,
        headers,
        agent: API_AGENT,
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

function chooseCompression(req, contentType) {
    if (!/^(text\/|application\/(javascript|json|xml)|image\/svg\+xml)/i.test(contentType)) return null;
    const accept = String(req.headers["accept-encoding"] || "").toLowerCase();
    if (accept.includes("br")) return { encoding: "br", stream: zlib.createBrotliCompress({ params: { [zlib.constants.BROTLI_PARAM_QUALITY]: 4 } }) };
    if (accept.includes("gzip")) return { encoding: "gzip", stream: zlib.createGzip({ level: 6 }) };
    return null;
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
            const contentType = MIME_TYPES[ext] || "application/octet-stream";
            const headers = {
                "content-type": contentType,
                "cache-control": ext === ".html"
                    ? "no-store, max-age=0, must-revalidate"
                    : "public, max-age=31536000, immutable",
            };
            const compression = chooseCompression(req, contentType);
            if (compression) {
                headers["content-encoding"] = compression.encoding;
                headers.vary = "Accept-Encoding";
            }
            res.writeHead(200, headers);
            const stream = fs.createReadStream(safeCandidate);
            if (compression) stream.pipe(compression.stream).pipe(res);
            else stream.pipe(res);
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

server.keepAliveTimeout = 65_000;
server.headersTimeout = 70_000;

server.listen(PORT, HOST, () => {
    console.log(`Nova frontend listening on ${HOST}:${PORT}`);
    console.log(`API proxy target: ${API_ORIGIN}`);
});

from pathlib import Path

main = Path('frontend/src/main.jsx')
text = main.read_text(encoding='utf-8')
marker = 'import { initializeNovaLanguage } from "./i18n.js";'
replacement = marker + '\nimport "./uiLanguageRuntime.js";'
if 'import "./uiLanguageRuntime.js";' not in text:
    if marker not in text:
        raise SystemExit('Expected i18n import marker was not found; refusing to patch.')
    text = text.replace(marker, replacement, 1)
    main.write_text(text, encoding='utf-8')

runtime = Path('frontend/src/uiLanguageRuntime.js')
if not runtime.exists():
    runtime.write_text(r'''import { applyNovaLanguage, normalizeLanguage } from "./i18n.js";

const SOURCE_BY_TRANSLATION = new Map();
const ATTRIBUTES = ["title", "aria-label", "placeholder"];

function remember(source, translated) {
    if (!source || !translated) return;
    SOURCE_BY_TRANSLATION.set(source, source);
    SOURCE_BY_TRANSLATION.set(translated, source);
}

function getSourceText(value) {
    const text = String(value || "").replace(/\\s+/g, " ").trim();
    return SOURCE_BY_TRANSLATION.get(text) || text;
}

function translateElement(element) {
    if (!(element instanceof Element)) return;

    const currentLanguage = normalizeLanguage(localStorage.getItem("nova_language") || "English");

    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) nodes.push(node);

    for (const textNode of nodes) {
        const parent = textNode.parentElement;
        if (!parent || ["SCRIPT", "STYLE", "NOSCRIPT"].includes(parent.tagName)) continue;
        const raw = textNode.nodeValue || "";
        const source = getSourceText(raw);
        if (!source) continue;
        const translated = translateKnownText(source, currentLanguage.code);
        if (translated && translated !== source) {
            remember(source, translated);
            textNode.nodeValue = raw.replace(raw.trim(), translated);
        }
    }

    const elements = [element, ...element.querySelectorAll("*")];
    for (const item of elements) {
        for (const attribute of ATTRIBUTES) {
            if (!item.hasAttribute(attribute)) continue;
            const raw = item.getAttribute(attribute) || "";
            const source = getSourceText(raw);
            const translated = translateKnownText(source, currentLanguage.code);
            if (translated && translated !== source) {
                remember(source, translated);
                item.setAttribute(attribute, translated);
            }
        }
    }
}

function translateKnownText(source, code) {
    if (typeof window !== "undefined" && window.__novaUiTranslations) {
        const table = window.__novaUiTranslations;
        return table[code]?.[source] || table.en?.[source] || source;
    }
    return source;
}

function refresh() {
    if (typeof document === "undefined") return;
    const language = normalizeLanguage(localStorage.getItem("nova_language") || "English");
    applyNovaLanguage(language.code);
    translateElement(document.body);
    document.documentElement.dataset.novaUiLanguage = language.code;
}

if (typeof window !== "undefined" && !window.__novaUiLanguageRuntimeInstalled) {
    window.__novaUiLanguageRuntimeInstalled = true;
    window.addEventListener("nova-language-changed", refresh);
    const observer = new MutationObserver(() => {
        if (window.__novaUiLanguageRuntimeBusy) return;
        window.__novaUiLanguageRuntimeBusy = true;
        requestAnimationFrame(() => {
            window.__novaUiLanguageRuntimeBusy = false;
            translateElement(document.body);
        });
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
    window.setTimeout(refresh, 0);
}
''', encoding='utf-8')

print('UI language runtime scaffold installed.')

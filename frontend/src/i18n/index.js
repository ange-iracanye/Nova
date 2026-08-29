import { NOVA_LANGUAGES } from "./languages";

const STORAGE_KEY = "nova_settings";
const DEFAULT_LANGUAGE = "en";

const NAME_TO_CODE = Object.fromEntries(
  NOVA_LANGUAGES.map(({ code, name }) => [name.toLowerCase(), code])
);

export function getLanguageCode(value) {
  if (!value) return DEFAULT_LANGUAGE;
  const normalized = String(value).trim().toLowerCase();
  if (NOVA_LANGUAGES.some((language) => language.code === normalized)) return normalized;
  return NAME_TO_CODE[normalized] || DEFAULT_LANGUAGE;
}

export function getStoredLanguage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_LANGUAGE;
    const parsed = JSON.parse(raw);
    return getLanguageCode(parsed?.settings?.language || parsed?.language);
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

export function applyNovaLanguage(value) {
  const code = getLanguageCode(value);
  document.documentElement.lang = code;
  document.documentElement.dir = code === "ar" ? "rtl" : "ltr";
  document.documentElement.dataset.novaLanguage = code;
  window.dispatchEvent(new CustomEvent("nova-language-change", { detail: { code } }));
  return code;
}

export function initializeNovaLanguage() {
  return applyNovaLanguage(getStoredLanguage());
}

export { NOVA_LANGUAGES };

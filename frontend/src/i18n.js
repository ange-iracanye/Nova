export const NOVA_LANGUAGES = [
  { code: "en", name: "English", nativeName: "English", rtl: false },
  { code: "es", name: "Spanish", nativeName: "Español", rtl: false },
  { code: "zh", name: "Chinese", nativeName: "中文", rtl: false },
  { code: "hi", name: "Hindi", nativeName: "हिन्दी", rtl: false },
  { code: "fr", name: "French", nativeName: "Français", rtl: false },
  { code: "ar", name: "Arabic", nativeName: "العربية", rtl: true },
  { code: "pt", name: "Portuguese", nativeName: "Português", rtl: false },
  { code: "ru", name: "Russian", nativeName: "Русский", rtl: false },
  { code: "de", name: "German", nativeName: "Deutsch", rtl: false },
  { code: "ja", name: "Japanese", nativeName: "日本語", rtl: false },
  { code: "ko", name: "Korean", nativeName: "한국어", rtl: false },
  { code: "it", name: "Italian", nativeName: "Italiano", rtl: false },
  { code: "tr", name: "Turkish", nativeName: "Türkçe", rtl: false },
  { code: "nl", name: "Dutch", nativeName: "Nederlands", rtl: false },
  { code: "pl", name: "Polish", nativeName: "Polski", rtl: false },
  { code: "uk", name: "Ukrainian", nativeName: "Українська", rtl: false },
  { code: "vi", name: "Vietnamese", nativeName: "Tiếng Việt", rtl: false },
  { code: "th", name: "Thai", nativeName: "ไทย", rtl: false },
  { code: "id", name: "Indonesian", nativeName: "Bahasa Indonesia", rtl: false },
  { code: "sv", name: "Swedish", nativeName: "Svenska", rtl: false },
  { code: "el", name: "Greek", nativeName: "Ελληνικά", rtl: false },
  { code: "cs", name: "Czech", nativeName: "Čeština", rtl: false },
  { code: "ro", name: "Romanian", nativeName: "Română", rtl: false },
  { code: "hu", name: "Hungarian", nativeName: "Magyar", rtl: false },
];

const LANGUAGE_KEY = "nova_language";
const SETTINGS_KEY = "nova_settings";

export function normalizeLanguage(value) {
  const raw = String(value || "English").trim().toLowerCase();
  const found = NOVA_LANGUAGES.find(language => language.code === raw || language.name.toLowerCase() === raw || language.nativeName.toLowerCase() === raw);
  return found || NOVA_LANGUAGES[0];
}

export function readNovaLanguage() {
  try {
    const direct = localStorage.getItem(LANGUAGE_KEY);
    if (direct) return normalizeLanguage(direct);
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      return normalizeLanguage(parsed?.settings?.language || parsed?.language);
    }
  } catch { /* local preference is optional */ }
  return NOVA_LANGUAGES[0];
}

export function applyNovaLanguage(value) {
  const language = normalizeLanguage(value);
  try { localStorage.setItem(LANGUAGE_KEY, language.code); } catch { /* ignore storage failures */ }
  document.documentElement.lang = language.code;
  document.documentElement.dir = language.rtl ? "rtl" : "ltr";
  document.documentElement.dataset.novaLanguage = language.code;
  window.dispatchEvent(new CustomEvent("nova-language-changed", { detail: language }));
  return language;
}

export function initializeNovaLanguage() {
  return applyNovaLanguage(readNovaLanguage().code);
}

// Nova V1 multilingual runtime: language preference is persisted globally.

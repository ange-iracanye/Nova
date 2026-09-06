import { normalizeLanguage, readNovaLanguage } from "./i18n.js";

let lastLanguage = normalizeLanguage(readNovaLanguage()).code;
let reloadQueued = false;

function checkLanguage() {
  const next = normalizeLanguage(readNovaLanguage()).code;
  if (next === lastLanguage || reloadQueued) return;
  lastLanguage = next;
  reloadQueued = true;
  window.location.reload();
}

/* Settings persistence happens in the same tab, so the storage event alone is
 * not enough. The short poll also covers language changes made by React. */
setInterval(checkLanguage, 250);
window.addEventListener("storage", event => {
  if (event.key === "nova_language" || event.key === "nova_settings") checkLanguage();
});

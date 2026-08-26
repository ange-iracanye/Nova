import { useEffect, useState } from "react";
import { getLanguage } from "../i18n";
export default function useNovaLanguage() {
  const [language, setLanguage] = useState(getLanguage());
  useEffect(() => {
    const onStorage = () => setLanguage(getLanguage());
    window.addEventListener("storage", onStorage);
    const timer = setInterval(onStorage, 500);
    return () => { window.removeEventListener("storage", onStorage); clearInterval(timer); };
  }, []);
  return language;
}

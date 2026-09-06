import { applyNovaLanguage, normalizeLanguage, uiText } from "./i18n.js";

const SOURCE_BY_NODE = new WeakMap();
const KEY_BY_SOURCE = new Map([
    ["Back", "Back"],
    ["Settings", "Settings"],
    ["Profile", "Profile"],
    ["Language", "Language"],
    ["Save", "Save"],
    ["Saved", "Saved"],
    ["Cancel", "Cancel"],
    ["Reset", "Reset"],
    ["Search", "Search"],
    ["Loading…", "Loading"],
    ["Chat", "Chat"],
    ["Dashboard", "Dashboard"],
    ["Progress", "Progress"],
    ["Analytics", "Analytics"],
    ["Capabilities", "Capabilities"],
    ["About Nova", "About"],
    ["Send", "Send"],
    ["New chat", "New"],
    ["Jump to latest", "Latest"],
    ["Retry", "Retry"],
    ["Regenerate", "Regenerate"],
    ["Log out", "Logout"],
    ["Name", "Name"],
    ["Learning level", "Level"],
    ["Teaching style", "Teaching"],
    ["Difficulty", "Difficulty"],
    ["Response length", "Length"],
    ["Tone", "Tone"],
    ["Custom instructions", "Custom"],
    ["Welcome to Nova", "Welcome"],
    ["Learn more", "LearnMore"]
]);

const ATTRIBUTES = ["title", "aria-label", "placeholder"];

function normalizeText(value) {
    return String(value || "").replace(/\s+/g, " ").trim();
}

function translatedText(source, language) {
    const key = KEY_BY_SOURCE.get(normalizeText(source));
    if (!key) return null;
    return uiTextForLanguage(key, language);
}

function uiTextForLanguage(key, language) {
    if (language.code === "en") return uiText(key);
    return languageTranslations[language.code]?.[key] || uiText(key);
}

const languageTranslations = {
    fr: { Back:"Retour", Settings:"Paramètres", Profile:"Profil", Language:"Langue", Save:"Enregistrer", Saved:"Enregistré", Cancel:"Annuler", Reset:"Réinitialiser", Search:"Rechercher", Loading:"Chargement…", Chat:"Discussion", Dashboard:"Tableau de bord", Progress:"Progression", Analytics:"Analyses", Capabilities:"Fonctionnalités", About:"À propos de Nova", Send:"Envoyer", New:"Nouvelle discussion", Latest:"Aller au dernier message", Retry:"Réessayer", Regenerate:"Régénérer", Logout:"Se déconnecter", Name:"Nom", Level:"Niveau d’apprentissage", Teaching:"Style d’enseignement", Difficulty:"Difficulté", Length:"Longueur des réponses", Tone:"Ton", Custom:"Instructions personnalisées", Welcome:"Bienvenue sur Nova", LearnMore:"En savoir plus" },
    es: { Back:"Atrás", Settings:"Configuración", Profile:"Perfil", Language:"Idioma", Save:"Guardar", Saved:"Guardado", Cancel:"Cancelar", Reset:"Restablecer", Search:"Buscar", Loading:"Cargando…", Chat:"Chat", Dashboard:"Panel", Progress:"Progreso", Analytics:"Análisis", Capabilities:"Funciones", About:"Sobre Nova", Send:"Enviar", New:"Nuevo chat", Latest:"Ir al último mensaje", Retry:"Reintentar", Regenerate:"Regenerar", Logout:"Cerrar sesión", Name:"Nombre", Level:"Nivel de aprendizaje", Teaching:"Estilo de enseñanza", Difficulty:"Dificultad", Length:"Longitud de respuesta", Tone:"Tono", Custom:"Instrucciones personalizadas", Welcome:"Bienvenido a Nova", LearnMore:"Más información" },
    de: { Back:"Zurück", Settings:"Einstellungen", Profile:"Profil", Language:"Sprache", Save:"Speichern", Saved:"Gespeichert", Cancel:"Abbrechen", Reset:"Zurücksetzen", Search:"Suchen", Loading:"Wird geladen…", Chat:"Chat", Dashboard:"Dashboard", Progress:"Fortschritt", Analytics:"Analysen", Capabilities:"Funktionen", About:"Über Nova", Send:"Senden", New:"Neuer Chat", Latest:"Zum neuesten", Retry:"Erneut versuchen", Regenerate:"Neu generieren", Logout:"Abmelden", Name:"Name", Level:"Lernniveau", Teaching:"Lehrstil", Difficulty:"Schwierigkeit", Length:"Antwortlänge", Tone:"Ton", Custom:"Eigene Anweisungen", Welcome:"Willkommen bei Nova", LearnMore:"Mehr erfahren" },
    it: { Back:"Indietro", Settings:"Impostazioni", Profile:"Profilo", Language:"Lingua", Save:"Salva", Saved:"Salvato", Cancel:"Annulla", Reset:"Reimposta", Search:"Cerca", Loading:"Caricamento…", Chat:"Chat", Dashboard:"Dashboard", Progress:"Progressi", Analytics:"Analisi", Capabilities:"Funzionalità", About:"Informazioni su Nova", Send:"Invia", New:"Nuova chat", Latest:"Vai all’ultimo", Retry:"Riprova", Regenerate:"Rigenera", Logout:"Esci", Name:"Nome", Level:"Livello di apprendimento", Teaching:"Stile di insegnamento", Difficulty:"Difficoltà", Length:"Lunghezza risposta", Tone:"Ton", Custom:"Istruzioni personalizzate", Welcome:"Benvenuto in Nova", LearnMore:"Scopri di più" },
    pt: { Back:"Voltar", Settings:"Configurações", Profile:"Perfil", Language:"Idioma", Save:"Salvar", Saved:"Salvo", Cancel:"Cancelar", Reset:"Redefinir", Search:"Pesquisar", Loading:"Carregando…", Chat:"Chat", Dashboard:"Painel", Progress:"Progresso", Analytics:"Análises", Capabilities:"Recursos", About:"Sobre a Nova", Send:"Enviar", New:"Novo chat", Latest:"Ir para o mais recente", Retry:"Tentar novamente", Regenerate:"Regenerar", Logout:"Sair", Name:"Nome", Level:"Nível de aprendizagem", Teaching:"Estilo de ensino", Difficulty:"Dificuldade", Length:"Tamanho da resposta", Tone:"Tom", Custom:"Instruções personalizadas", Welcome:"Bem-vindo à Nova", LearnMore:"Saiba mais" },
    zh: { Back:"返回", Settings:"设置", Profile:"个人资料", Language:"语言", Save:"保存", Saved:"已保存", Cancel:"取消", Reset:"重置", Search:"搜索", Loading:"加载中…", Chat:"聊天", Dashboard:"控制面板", Progress:"进度", Analytics:"分析", Capabilities:"功能", About:"关于 Nova", Send:"发送", New:"新对话", Latest:"跳到最新", Retry:"重试", Regenerate:"重新生成", Logout:"退出登录", Name:"姓名", Level:"学习水平", Teaching:"教学风格", Difficulty:"难度", Length:"回答长度", Tone:"语气", Custom:"自定义指令", Welcome:"欢迎使用 Nova", LearnMore:"了解更多" },
    ja: { Back:"戻る", Settings:"設定", Profile:"プロフィール", Language:"言語", Save:"保存", Saved:"保存しました", Cancel:"キャンセル", Reset:"リセット", Search:"検索", Loading:"読み込み中…", Chat:"チャット", Dashboard:"ダッシュボード", Progress:"進捗", Analytics:"分析", Capabilities:"機能", About:"Novaについて", Send:"送信", New:"新しいチャット", Latest:"最新へ", Retry:"再試行", Regenerate:"再生成", Logout:"ログアウト", Name:"名前", Level:"学習レベル", Teaching:"指導スタイル", Difficulty:"難易度", Length:"回答の長さ", Tone:"トーン", Custom:"カスタム指示", Welcome:"Novaへようこそ", LearnMore:"詳しく見る" },
    ko: { Back:"뒤로", Settings:"설정", Profile:"프로필", Language:"언어", Save:"저장", Saved:"저장됨", Cancel:"취소", Reset:"재설정", Search:"검색", Loading:"로드 중…", Chat:"채팅", Dashboard:"대시보드", Progress:"진행 상황", Analytics:"분석", Capabilities:"기능", About:"Nova 정보", Send:"보내기", New:"새 채팅", Latest:"최신으로 이동", Retry:"다시 시도", Regenerate:"다시 생성", Logout:"로그아웃", Name:"이름", Level:"학습 수준", Teaching:"학습 방식", Difficulty:"난이도", Length:"응답 길이", Tone:"말투", Custom:"사용자 지정 지침", Welcome:"Nova에 오신 것을 환영합니다", LearnMore:"자세히 보기" },
    ar: { Back:"رجوع", Settings:"الإعدادات", Profile:"الملف الشخصي", Language:"اللغة", Save:"حفظ", Saved:"تم الحفظ", Cancel:"إلغاء", Reset:"إعادة تعيين", Search:"بحث", Loading:"جارٍ التحميل…", Chat:"الدردشة", Dashboard:"لوحة التحكم", Progress:"التقدم", Analytics:"التحليلات", Capabilities:"القدرات", About:"حول Nova", Send:"إرسال", New:"محادثة جديدة", Latest:"الانتقال إلى الأحدث", Retry:"إعادة المحاولة", Regenerate:"إعادة الإنشاء", Logout:"تسجيل الخروج", Name:"الاسم", Level:"مستوى التعلم", Teaching:"أسلوب التدريس", Difficulty:"الصعوبة", Length:"طول الإجابة", Tone:"النبرة", Custom:"تعليمات مخصصة", Welcome:"مرحبًا بك في Nova", LearnMore:"معرفة المزيد" },
    hi: { Back:"वापस", Settings:"सेटिंग्स", Profile:"प्रोफ़ाइल", Language:"भाषा", Save:"सहेजें", Saved:"सहेजा गया", Cancel:"रद्द करें", Reset:"रीसेट", Search:"खोजें", Loading:"लोड हो रहा है…", Chat:"चैट", Dashboard:"डैशबोर्ड", Progress:"प्रगति", Analytics:"विश्लेषण", Capabilities:"सुविधाएँ", About:"Nova के बारे में", Send:"भेजें", New:"नई चैट", Latest:"नवीनतम पर जाएँ", Retry:"फिर कोशिश करें", Regenerate:"फिर से बनाएँ", Logout:"लॉग आउट", Name:"नाम", Level:"सीखने का स्तर", Teaching:"शिक्षण शैली", Difficulty:"कठिनाई", Length:"उत्तर की लंबाई", Tone:"टोन", Custom:"कस्टम निर्देश", Welcome:"Nova में आपका स्वागत है", LearnMore:"और जानें" },
    ru: { Back:"Назад", Settings:"Настройки", Profile:"Профиль", Language:"Язык", Save:"Сохранить", Saved:"Сохранено", Cancel:"Отмена", Reset:"Сбросить", Search:"Поиск", Loading:"Загрузка…", Chat:"Чат", Dashboard:"Панель управления", Progress:"Прогресс", Analytics:"Аналитика", Capabilities:"Возможности", About:"О Nova", Send:"Отправить", New:"Новый чат", Latest:"К последнему", Retry:"Повторить", Regenerate:"Создать заново", Logout:"Выйти", Name:"Имя", Level:"Уровень обучения", Teaching:"Стиль обучения", Difficulty:"Сложность", Length:"Длина ответа", Tone:"Тон", Custom:"Пользовательские инструкции", Welcome:"Добро пожаловать в Nova", LearnMore:"Подробнее" },
    tr: { Back:"Geri", Settings:"Ayarlar", Profile:"Profil", Language:"Dil", Save:"Kaydet", Saved:"Kaydedildi", Cancel:"İptal", Reset:"Sıfırla", Search:"Ara", Loading:"Yükleniyor…", Chat:"Sohbet", Dashboard:"Kontrol paneli", Progress:"İlerleme", Analytics:"Analiz", Capabilities:"Yetenekler", About:"Nova hakkında", Send:"Gönder", New:"Yeni sohbet", Latest:"Son mesaja git", Retry:"Tekrar dene", Regenerate:"Yeniden oluştur", Logout:"Çıkış yap", Name:"Ad", Level:"Öğrenme seviyesi", Teaching:"Öğretim stili", Difficulty:"Zorluk", Length:"Yanıt uzunluğu", Tone:"Ton", Custom:"Özel talimatlar", Welcome:"Nova'ya hoş geldiniz", LearnMore:"Daha fazla bilgi" },
    nl: { Back:"Terug", Settings:"Instellingen", Profile:"Profiel", Language:"Taal", Save:"Opslaan", Saved:"Opgeslagen", Cancel:"Annuleren", Reset:"Resetten", Search:"Zoeken", Loading:"Laden…", Chat:"Chat", Dashboard:"Dashboard", Progress:"Voortgang", Analytics:"Analyses", Capabilities:"Functies", About:"Over Nova", Send:"Versturen", New:"Nieuwe chat", Latest:"Naar nieuwste", Retry:"Opnieuw proberen", Regenerate:"Opnieuw genereren", Logout:"Uitloggen", Name:"Naam", Level:"Leer niveau", Teaching:"Onderwijsstijl", Difficulty:"Moeilijkheid", Length:"Antwoordlengte", Tone:"Toon", Custom:"Aangepaste instructies", Welcome:"Welkom bij Nova", LearnMore:"Meer informatie" },
    pl: { Back:"Wstecz", Settings:"Ustawienia", Profile:"Profil", Language:"Język", Save:"Zapisz", Saved:"Zapisano", Cancel:"Anuluj", Reset:"Resetuj", Search:"Szukaj", Loading:"Ładowanie…", Chat:"Czat", Dashboard:"Panel", Progress:"Postęp", Analytics:"Analizy", Capabilities:"Funkcje", About:"O Nova", Send:"Wyślij", New:"Nowy czat", Latest:"Przejdź do najnowszych", Retry:"Spróbuj ponownie", Regenerate:"Wygeneruj ponownie", Logout:"Wyloguj", Name:"Imię", Level:"Poziom nauki", Teaching:"Styl nauczania", Difficulty:"Trudność", Length:"Długość odpowiedzi", Tone:"Ton", Custom:"Własne instrukcje", Welcome:"Witamy w Nova", LearnMore:"Dowiedz się więcej" },
    uk: { Back:"Назад", Settings:"Налаштування", Profile:"Профіль", Language:"Мова", Save:"Зберегти", Saved:"Збережено", Cancel:"Скасувати", Reset:"Скинути", Search:"Пошук", Loading:"Завантаження…", Chat:"Чат", Dashboard:"Панель", Progress:"Прогрес", Analytics:"Аналітика", Capabilities:"Можливості", About:"Про Nova", Send:"Надіслати", New:"Новий чат", Latest:"До останнього", Retry:"Повторити", Regenerate:"Створити знову", Logout:"Вийти", Name:"Ім’я", Level:"Рівень навчання", Teaching:"Стиль навчання", Difficulty:"Складність", Length:"Довжина відповіді", Tone:"Тон", Custom:"Власні інструкції", Welcome:"Ласкаво просимо до Nova", LearnMore:"Дізнатися більше" },
    vi: { Back:"Quay lại", Settings:"Cài đặt", Profile:"Hồ sơ", Language:"Ngôn ngữ", Save:"Lưu", Saved:"Đã lưu", Cancel:"Hủy", Reset:"Đặt lại", Search:"Tìm kiếm", Loading:"Đang tải…", Chat:"Trò chuyện", Dashboard:"Bảng điều khiển", Progress:"Tiến độ", Analytics:"Phân tích", Capabilities:"Tính năng", About:"Về Nova", Send:"Gửi", New:"Cuộc trò chuyện mới", Latest:"Đến mới nhất", Retry:"Thử lại", Regenerate:"Tạo lại", Logout:"Đăng xuất", Name:"Tên", Level:"Trình độ học tập", Teaching:"Phong cách giảng dạy", Difficulty:"Độ khó", Length:"Độ dài câu trả lời", Tone:"Giọng điệu", Custom:"Hướng dẫn tùy chỉnh", Welcome:"Chào mừng đến với Nova", LearnMore:"Tìm hiểu thêm" },
    th: { Back:"ย้อนกลับ", Settings:"การตั้งค่า", Profile:"โปรไฟล์", Language:"ภาษา", Save:"บันทึก", Saved:"บันทึกแล้ว", Cancel:"ยกเลิก", Reset:"รีเซ็ต", Search:"ค้นหา", Loading:"กำลังโหลด…", Chat:"แชต", Dashboard:"แดชบอร์ด", Progress:"ความคืบหน้า", Analytics:"การวิเคราะห์", Capabilities:"ความสามารถ", About:"เกี่ยวกับ Nova", Send:"ส่ง", New:"แชตใหม่", Latest:"ไปยังล่าสุด", Retry:"ลองอีกครั้ง", Regenerate:"สร้างใหม่", Logout:"ออกจากระบบ", Name:"ชื่อ", Level:"ระดับการเรียนรู้", Teaching:"รูปแบบการสอน", Difficulty:"ความยาก", Length:"ความยาวคำตอบ", Tone:"โทน", Custom:"คำสั่งกำหนดเอง", Welcome:"ยินดีต้อนรับสู่ Nova", LearnMore:"เรียนรู้เพิ่มเติม" },
    id: { Back:"Kembali", Settings:"Pengaturan", Profile:"Profil", Language:"Bahasa", Save:"Simpan", Saved:"Tersimpan", Cancel:"Batal", Reset:"Atur ulang", Search:"Cari", Loading:"Memuat…", Chat:"Obrolan", Dashboard:"Dasbor", Progress:"Kemajuan", Analytics:"Analitik", Capabilities:"Fitur", About:"Tentang Nova", Send:"Kirim", New:"Obrolan baru", Latest:"Ke terbaru", Retry:"Coba lagi", Regenerate:"Buat ulang", Logout:"Keluar", Name:"Nama", Level:"Tingkat belajar", Teaching:"Gaya mengajar", Difficulty:"Kesulitan", Length:"Panjang jawaban", Tone:"Nada", Custom:"Instruksi khusus", Welcome:"Selamat datang di Nova", LearnMore:"Pelajari lebih lanjut" },
    sv: { Back:"Tillbaka", Settings:"Inställningar", Profile:"Profil", Language:"Språk", Save:"Spara", Saved:"Sparat", Cancel:"Avbryt", Reset:"Återställ", Search:"Sök", Loading:"Laddar…", Chat:"Chatt", Dashboard:"Instrumentpanel", Progress:"Framsteg", Analytics:"Analys", Capabilities:"Funktioner", About:"Om Nova", Send:"Skicka", New:"Ny chatt", Latest:"Till senaste", Retry:"Försök igen", Regenerate:"Skapa igen", Logout:"Logga ut", Name:"Namn", Level:"Lärandenivå", Teaching:"Undervisningsstil", Difficulty:"Svårighetsgrad", Length:"Svarslängd", Tone:"Ton", Custom:"Egna instruktioner", Welcome:"Välkommen till Nova", LearnMore:"Läs mer" },
    el: { Back:"Πίσω", Settings:"Ρυθμίσεις", Profile:"Προφίλ", Language:"Γλώσσα", Save:"Αποθήκευση", Saved:"Αποθηκεύτηκε", Cancel:"Ακύρωση", Reset:"Επαναφορά", Search:"Αναζήτηση", Loading:"Φόρτωση…", Chat:"Συνομιλία", Dashboard:"Πίνακας", Progress:"Πρόοδος", Analytics:"Αναλύσεις", Capabilities:"Δυνατότητες", About:"Σχετικά με τη Nova", Send:"Αποστολή", New:"Νέα συνομιλία", Latest:"Στα πιο πρόσφατα", Retry:"Δοκιμή ξανά", Regenerate:"Νέα δημιουργία", Logout:"Αποσύνδεση", Name:"Όνομα", Level:"Επίπεδο μάθησης", Teaching:"Στυλ διδασκαλίας", Difficulty:"Δυσκολία", Length:"Μήκος απάντησης", Tone:"Τόνος", Custom:"Προσαρμοσμένες οδηγίες", Welcome:"Καλώς ήρθατε στη Nova", LearnMore:"Μάθετε περισσότερα" },
    cs: { Back:"Zpět", Settings:"Nastavení", Profile:"Profil", Language:"Jazyk", Save:"Uložit", Saved:"Uloženo", Cancel:"Zrušit", Reset:"Obnovit", Search:"Hledat", Loading:"Načítání…", Chat:"Chat", Dashboard:"Přehled", Progress:"Pokrok", Analytics:"Analytika", Capabilities:"Funkce", About:"O Nova", Send:"Odeslat", New:"Nový chat", Latest:"Na nejnovější", Retry:"Zkusit znovu", Regenerate:"Vygenerovat znovu", Logout:"Odhlásit", Name:"Jméno", Level:"Úroveň učení", Teaching:"Styl výuky", Difficulty:"Obtížnost", Length:"Délka odpovědi", Tone:"Tón", Custom:"Vlastní pokyny", Welcome:"Vítejte v Nova", LearnMore:"Zjistit více" },
    ro: { Back:"Înapoi", Settings:"Setări", Profile:"Profil", Language:"Limbă", Save:"Salvează", Saved:"Salvat", Cancel:"Anulează", Reset:"Resetează", Search:"Caută", Loading:"Se încarcă…", Chat:"Chat", Dashboard:"Panou", Progress:"Progres", Analytics:"Analize", Capabilities:"Funcții", About:"Despre Nova", Send:"Trimite", New:"Chat nou", Latest:"La cel mai recent", Retry:"Încearcă din nou", Regenerate:"Generează din nou", Logout:"Deconectare", Name:"Nume", Level:"Nivel de învățare", Teaching:"Stil de predare", Difficulty:"Dificultate", Length:"Lungimea răspunsului", Tone:"Ton", Custom:"Instrucțiuni personalizate", Welcome:"Bine ai venit la Nova", LearnMore:"Află mai multe" },
    hu: { Back:"Vissza", Settings:"Beállítások", Profile:"Profil", Language:"Nyelv", Save:"Mentés", Saved:"Mentve", Cancel:"Mégse", Reset:"Visszaállítás", Search:"Keresés", Loading:"Betöltés…", Chat:"Csevegés", Dashboard:"Irányítópult", Progress:"Haladás", Analytics:"Elemzések", Capabilities:"Funkciók", About:"A Nováról", Send:"Küldés", New:"Új csevegés", Latest:"Legújabbhoz", Retry:"Újra", Regenerate:"Újragenerálás", Logout:"Kijelentkezés", Name:"Név", Level:"Tanulási szint", Teaching:"Tanítási stílus", Difficulty:"Nehézség", Length:"Válasz hossza", Tone:"Hangnem", Custom:"Egyéni utasítások", Welcome:"Üdvözlünk a Novában", LearnMore:"További információ" }
};

function translateDocument() {
    const language = normalizeLanguage(localStorage.getItem("nova_language") || "English");
    applyNovaLanguage(language.code);
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;
    while ((node = walker.nextNode())) nodes.push(node);

    for (const textNode of nodes) {
        const parent = textNode.parentElement;
        if (!parent || ["SCRIPT", "STYLE", "NOSCRIPT"].includes(parent.tagName)) continue;
        const current = normalizeText(textNode.nodeValue);
        const source = SOURCE_BY_NODE.get(textNode) || current;
        const translated = translatedText(source, language);
        if (translated && translated !== current) {
            SOURCE_BY_NODE.set(textNode, source);
            const raw = textNode.nodeValue || "";
            textNode.nodeValue = raw.replace(raw.trim(), translated);
        }
    }

    for (const element of document.querySelectorAll("*")) {
        for (const attribute of ATTRIBUTES) {
            if (!element.hasAttribute(attribute)) continue;
            const current = normalizeText(element.getAttribute(attribute));
            const translated = translatedText(current, language);
            if (translated && translated !== current) element.setAttribute(attribute, translated);
        }
    }
}

if (typeof window !== "undefined" && !window.__novaUiLanguageRuntimeInstalled) {
    window.__novaUiLanguageRuntimeInstalled = true;
    window.addEventListener("nova-language-changed", () => requestAnimationFrame(translateDocument));
    const observer = new MutationObserver(() => {
        if (window.__novaUiLanguageRuntimeBusy) return;
        window.__novaUiLanguageRuntimeBusy = true;
        requestAnimationFrame(() => {
            window.__novaUiLanguageRuntimeBusy = false;
            translateDocument();
        });
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
    window.setTimeout(translateDocument, 0);
}

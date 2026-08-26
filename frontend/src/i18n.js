const dictionaries = {
  English: { back:"Back", settings:"Settings", dashboard:"Dashboard", progress:"Progress", newChat:"New chat", jumpToLatest:"Jump to latest", send:"Send", stop:"Stop", regenerate:"Regenerate", typeMessage:"Message Nova...", welcome:"How can I help you learn today?" },
  Spanish: { back:"Volver", settings:"Configuración", dashboard:"Panel", progress:"Progreso", newChat:"Nuevo chat", jumpToLatest:"Ir al último mensaje", send:"Enviar", stop:"Detener", regenerate:"Regenerar", typeMessage:"Escribe a Nova...", welcome:"¿Cómo puedo ayudarte a aprender hoy?" },
  French: { back:"Retour", settings:"Paramètres", dashboard:"Tableau de bord", progress:"Progrès", newChat:"Nouvelle discussion", jumpToLatest:"Aller au dernier message", send:"Envoyer", stop:"Arrêter", regenerate:"Régénérer", typeMessage:"Écrivez à Nova...", welcome:"Comment puis-je vous aider à apprendre aujourd'hui ?" },
  German: { back:"Zurück", settings:"Einstellungen", dashboard:"Dashboard", progress:"Fortschritt", newChat:"Neuer Chat", jumpToLatest:"Zum neuesten Beitrag", send:"Senden", stop:"Stoppen", regenerate:"Neu generieren", typeMessage:"Nova schreiben...", welcome:"Wie kann ich dir heute beim Lernen helfen?" },
  Italian: { back:"Indietro", settings:"Impostazioni", dashboard:"Dashboard", progress:"Progressi", newChat:"Nuova chat", jumpToLatest:"Vai all'ultimo messaggio", send:"Invia", stop:"Ferma", regenerate:"Rigenera", typeMessage:"Scrivi a Nova...", welcome:"Come posso aiutarti a imparare oggi?" },
  Portuguese: { back:"Voltar", settings:"Configurações", dashboard:"Painel", progress:"Progresso", newChat:"Novo chat", jumpToLatest:"Ir para a mensagem mais recente", send:"Enviar", stop:"Parar", regenerate:"Regenerar", typeMessage:"Escreva para Nova...", welcome:"Como posso ajudar você a aprender hoje?" },
  Chinese: { back:"返回", settings:"设置", dashboard:"仪表板", progress:"学习进度", newChat:"新对话", jumpToLatest:"跳转到最新消息", send:"发送", stop:"停止", regenerate:"重新生成", typeMessage:"给 Nova 发消息...", welcome:"今天我可以怎样帮助你学习？" },
  Japanese: { back:"戻る", settings:"設定", dashboard:"ダッシュボード", progress:"進捗", newChat:"新しいチャット", jumpToLatest:"最新へ移動", send:"送信", stop:"停止", regenerate:"再生成", typeMessage:"Nova にメッセージ...", welcome:"今日はどのような学習をお手伝いしましょうか？" },
  Korean: { back:"뒤로", settings:"설정", dashboard:"대시보드", progress:"진행 상황", newChat:"새 채팅", jumpToLatest:"최신으로 이동", send:"보내기", stop:"중지", regenerate:"다시 생성", typeMessage:"Nova에게 메시지...", welcome:"오늘은 무엇을 배우는 데 도움을 드릴까요?" },
  Arabic: { back:"رجوع", settings:"الإعدادات", dashboard:"لوحة التحكم", progress:"التقدم", newChat:"محادثة جديدة", jumpToLatest:"الانتقال إلى الأحدث", send:"إرسال", stop:"إيقاف", regenerate:"إعادة الإنشاء", typeMessage:"اكتب إلى Nova...", welcome:"كيف يمكنني مساعدتك في التعلم اليوم؟" },
  Hindi: { back:"वापस", settings:"सेटिंग्स", dashboard:"डैशबोर्ड", progress:"प्रगति", newChat:"नई चैट", jumpToLatest:"नवीनतम पर जाएँ", send:"भेजें", stop:"रोकें", regenerate:"फिर से बनाएँ", typeMessage:"Nova को संदेश दें...", welcome:"आज मैं आपकी सीखने में कैसे मदद कर सकता हूँ?" },
};
const fallback = dictionaries.English;
export function getLanguage() { try { return JSON.parse(localStorage.getItem("nova_settings") || "{}").settings?.language || "English"; } catch { return "English"; } }
export function t(key) { return (dictionaries[getLanguage()] || fallback)[key] || fallback[key] || key; }
export function getDictionary(language) { return dictionaries[language] || fallback; }
export { dictionaries };

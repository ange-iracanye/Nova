import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  AlertCircle,
  ArrowDown,
  ArrowLeft,
  Bot,
  Check,
  CheckCircle2,
  ChevronDown,
  Clipboard,
  Copy,
  Download,
  Edit3,
  FileText,
  History,
  Lightbulb,
  LoaderCircle,
  LogOut,
  Menu,
  MessageSquare,
  PanelLeft,
  PanelLeftClose,
  Plus,
  RefreshCw,
  Search,
  Send,
  Settings,
  Sparkles,
  StopCircle,
  Trash2,
  User,
  Wifi,
  WifiOff,
  X,
  Zap,
} from "lucide-react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useLocation, useNavigate } from "react-router-dom";
import CodeBlock from "../components/CodeBlock";

/* =========================================================
   NOVA CHAT
   ========================================================= */

const API_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const STREAM_TIMEOUT = 45000;
const BACKEND_TIMEOUT = 5000;
const MAX_INPUT = 12000;

const STORAGE = {
  USER: "nova_user",
  LAST_PAGE: "nova_last_page",
  CURRENT: "nova_current_conversation",
  SIDEBAR: "nova_sidebar_state",
  DRAFT_PREFIX: "nova_chat_draft_",
};

const MODES = [
  {
    id: "adaptive",
    label: "Adaptive Tutor",
    description: "Adjusts explanations to your level.",
    icon: Sparkles,
  },
  {
    id: "personal",
    label: "Personal Tutor",
    description: "Guided, step-by-step help.",
    icon: User,
  },
  {
    id: "practice",
    label: "Practice Coach",
    description: "Exercises, hints and feedback.",
    icon: Zap,
  },
];

const STARTERS = [
  [
    "Explain a difficult concept",
    "Explain this concept to me step by step, using simple examples.",
  ],
  [
    "Help me study",
    "Help me study this topic. Start by checking what I already understand.",
  ],
  [
    "Quiz me",
    "Quiz me on this topic one question at a time and adapt to my answers.",
  ],
  [
    "Give me a hint",
    "Give me a small hint without giving me the full answer.",
  ],
];

const QUICK_ACTIONS = [
  [
    "Explain",
    Lightbulb,
    "Explain this in simple terms with an example.",
  ],
  [
    "Quiz me",
    Zap,
    "Quiz me on what we are discussing, one question at a time.",
  ],
  [
    "Hint",
    Sparkles,
    "Give me a hint without giving me the complete answer.",
  ],
  [
    "Summarize",
    FileText,
    "Summarize the key points from your last answer.",
  ],
];

/* =========================================================
   SAFE STORAGE
   ========================================================= */

function getStorage(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function setStorage(key, value) {
  try {
    localStorage.setItem(key, String(value));
    return true;
  } catch {
    return false;
  }
}

function removeStorage(key) {
  try {
    localStorage.removeItem(key);
  } catch {
    // Storage can be disabled. Nothing else to do.
  }
}

function getUser() {
  try {
    const value = getStorage(STORAGE.USER);
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

/* =========================================================
   HELPERS
   ========================================================= */

function draftKey(conversationId, mode) {
  return `${STORAGE.DRAFT_PREFIX}${conversationId || "new"}_${mode}`;
}

function friendlyError(error) {
  if (!error) {
    return "Something went wrong while contacting Nova.";
  }

  if (error.name === "AbortError") {
    return "Generation stopped.";
  }

  const message = String(error.message || "");

  if (/offline/i.test(message)) {
    return "You're offline. Nova cannot send the message right now.";
  }

  if (/Failed to fetch|NetworkError|Load failed/i.test(message)) {
    return "Nova could not reach the backend. Make sure the Nova backend is running.";
  }

  if (/timeout|timed out|inactive/i.test(message)) {
    return "Nova stopped responding because the connection was inactive for too long.";
  }

  if (/401/.test(message)) {
    return "Your session is no longer valid. Please sign in again.";
  }

  if (/403/.test(message)) {
    return "Nova refused this request because you do not have permission.";
  }

  if (/404/.test(message)) {
    return "Nova could not find that conversation.";
  }

  if (/429/.test(message)) {
    return "Nova is receiving too many requests. Wait a moment and try again.";
  }

  if (/500|502|503|504/.test(message)) {
    return "Nova's backend encountered an internal error.";
  }

  return message || "Something went wrong while contacting Nova.";
}

function normalizeMessage(message) {
  return {
    role: message?.role === "user" ? "user" : "nova",
    text: typeof message?.text === "string" ? message.text : "",
    streaming: Boolean(message?.streaming),
    error: Boolean(message?.error),
  };
}

function conversationPreview(item) {
  const messages = Array.isArray(item?.messages)
    ? item.messages
    : [];

  const last = messages[messages.length - 1];

  return last?.text || "No messages yet";
}

function formatDate(value) {
  if (!value) return "";

  try {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "";
    }

    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
    }).format(date);
  } catch {
    return "";
  }
}

function sortHistory(items) {
  return [...items].sort((a, b) => {
    const aDate = new Date(
      a?.updated_at || a?.created_at || 0
    ).getTime();

    const bDate = new Date(
      b?.updated_at || b?.created_at || 0
    ).getTime();

    return bDate - aDate;
  });
}

function messagesToText(messages) {
  return messages
    .filter((message) => message?.text)
    .map((message) => {
      const speaker =
        message.role === "user" ? "You" : "Nova";

      return `${speaker}:\n${message.text}`;
    })
    .join("\n\n------------------------------\n\n");
}

function messagesToMarkdown(messages) {
  return messages
    .filter((message) => message?.text)
    .map((message) => {
      const speaker =
        message.role === "user" ? "## You" : "## Nova";

      return `${speaker}\n\n${message.text}`;
    })
    .join("\n\n---\n\n");
}

/* =========================================================
   STREAMING
   ========================================================= */

async function streamText(
  response,
  onChunk,
  signal
) {
  if (!response.body) {
    throw new Error("Nova returned an empty response stream.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let timer = null;
  let timedOut = false;

  const clearTimer = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  };

  const armTimer = () => {
    clearTimer();

    timer = setTimeout(() => {
      timedOut = true;

      try {
        reader.cancel();
      } catch {
        // Ignore cancellation errors.
      }
    }, STREAM_TIMEOUT);
  };

  try {
    armTimer();

    while (true) {
      if (signal?.aborted) {
        try {
          await reader.cancel();
        } catch {
          // Ignore.
        }

        throw new DOMException(
          "Request aborted.",
          "AbortError"
        );
      }

      const { done, value } = await reader.read();

      if (timedOut) {
        throw new Error(
          "Nova stream timeout: the connection was inactive."
        );
      }

      if (done) {
        break;
      }

      armTimer();

      if (value) {
        const text = decoder.decode(value, {
          stream: true,
        });

        if (text) {
          onChunk(text);
        }
      }
    }

    const tail = decoder.decode();

    if (tail) {
      onChunk(tail);
    }
  } finally {
    clearTimer();

    try {
      reader.releaseLock();
    } catch {
      // Ignore.
    }
  }
}

/* =========================================================
   MESSAGE COMPONENT
   ========================================================= */

function Message({
  message,
  index,
  copy,
  regenerate,
  continuePrompt,
  retry,
}) {
  const isUser = message.role === "user";

  return (
    <article
      className={`flex w-full ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`flex w-full max-w-5xl gap-3 md:gap-4 ${
          isUser ? "flex-row-reverse" : ""
        }`}
      >
        <div
          className={`mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border ${
            isUser
              ? "border-sky-400/20 bg-sky-500/10 text-sky-300"
              : message.error
              ? "border-red-400/20 bg-red-500/10 text-red-300"
              : "border-white/10 bg-white/[0.06] text-slate-200"
          }`}
        >
          {isUser ? (
            <User size={17} />
          ) : (
            <Sparkles size={17} />
          )}
        </div>

        <div
          className={`min-w-0 max-w-[calc(100%-3.5rem)] rounded-2xl border px-4 py-3 md:px-5 md:py-4 ${
            isUser
              ? "rounded-tr-md border-sky-400/20 bg-sky-600 text-white"
              : message.error
              ? "rounded-tl-md border-red-400/20 bg-red-500/[0.06] text-red-100"
              : "rounded-tl-md border-white/[0.07] bg-white/[0.035] text-slate-200"
          }`}
        >
          {!isUser && (
            <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.16em] text-slate-600">
              Nova

              {message.streaming && (
                <span className="normal-case tracking-normal">
                  • generating
                </span>
              )}
            </div>
          )}

          {isUser ? (
            <p className="whitespace-pre-wrap break-words text-sm leading-7">
              {message.text}
            </p>
          ) : message.text ? (
            <div className="nova-markdown text-sm leading-7">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({
                    inline,
                    className,
                    children,
                    ...props
                  }) {
                    const code = String(children).replace(
                      /\n$/,
                      ""
                    );

                    if (inline) {
                      return (
                        <code
                          className="rounded-md border border-white/10 bg-black/20 px-1.5 py-0.5 text-[.9em]"
                          {...props}
                        >
                          {children}
                        </code>
                      );
                    }

                    return (
                      <CodeBlock
                        code={code}
                        language={
                          className?.replace(
                            "language-",
                            ""
                          ) || "text"
                        }
                      />
                    );
                  },

                  a({ children, ...props }) {
                    return (
                      <a
                        {...props}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sky-300 underline underline-offset-4"
                      >
                        {children}
                      </a>
                    );
                  },

                  ul({ children }) {
                    return (
                      <ul className="my-3 list-disc space-y-1 pl-6">
                        {children}
                      </ul>
                    );
                  },

                  ol({ children }) {
                    return (
                      <ol className="my-3 list-decimal space-y-1 pl-6">
                        {children}
                      </ol>
                    );
                  },

                  blockquote({ children }) {
                    return (
                      <blockquote className="my-4 border-l-2 border-white/15 pl-4 text-slate-400">
                        {children}
                      </blockquote>
                    );
                  },

                  table({ children }) {
                    return (
                      <div className="my-4 overflow-x-auto rounded-xl border border-white/10">
                        <table className="min-w-full text-left text-xs">
                          {children}
                        </table>
                      </div>
                    );
                  },

                  th({ children }) {
                    return (
                      <th className="border-b border-white/10 bg-white/[.04] px-3 py-2">
                        {children}
                      </th>
                    );
                  },

                  td({ children }) {
                    return (
                      <td className="border-b border-white/[.06] px-3 py-2">
                        {children}
                      </td>
                    );
                  },
                }}
              >
                {message.text}
              </ReactMarkdown>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <LoaderCircle
                size={15}
                className="animate-spin"
              />
              Nova is thinking...
            </div>
          )}

          {!isUser &&
            message.text &&
            !message.streaming && (
              <div className="mt-4 flex flex-wrap gap-1 border-t border-white/[.06] pt-2 opacity-70 hover:opacity-100">
                <button
                  type="button"
                  onClick={() => copy(message.text)}
                  className="nova-action"
                >
                  <Copy size={13} />
                  Copy
                </button>

                <button
                  type="button"
                  onClick={() => regenerate(index)}
                  className="nova-action"
                >
                  <RefreshCw size={13} />
                  Regenerate
                </button>

                <button
                  type="button"
                  onClick={() =>
                    continuePrompt(message.text)
                  }
                  className="nova-action"
                >
                  <Lightbulb size={13} />
                  Continue
                </button>

                {message.error && (
                  <button
                    type="button"
                    onClick={retry}
                    className="nova-action text-red-300"
                  >
                    <RefreshCw size={13} />
                    Retry
                  </button>
                )}
              </div>
            )}
        </div>
      </div>
    </article>
  );
}

/* =========================================================
   MAIN CHAT
   ========================================================= */

export default function Chat() {
  const location = useLocation();
  const navigate = useNavigate();

  const params = useMemo(
    () => new URLSearchParams(location.search),
    [location.search]
  );

  const demo = params.get("demo") === "true";

  const requestedMode =
    params.get("mode") || "adaptive";

  const initialMode = MODES.some(
    (mode) => mode.id === requestedMode
  )
    ? requestedMode
    : "adaptive";

  const [
    messages,
    setMessages,
  ] = useState([]);

  const [
    history,
    setHistory,
  ] = useState([]);

  const [
    conversationId,
    setConversationId,
  ] = useState(null);

  const [
    demoSession,
    setDemoSession,
  ] = useState(null);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sidebar, setSidebar] = useState(true);
  const [search, setSearch] = useState("");
  const [messageSearch, setMessageSearch] = useState("");
  const [account, setAccount] = useState(false);
  const [modeOpen, setModeOpen] = useState(false);
  const [mode, setMode] = useState(initialMode);
  const [backend, setBackend] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [showLatest, setShowLatest] = useState(false);
  const [deleteItem, setDeleteItem] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [online, setOnline] = useState(
    typeof navigator === "undefined"
      ? true
      : navigator.onLine
  );
  const [draftSaved, setDraftSaved] = useState(false);

  const container = useRef(null);
  const end = useRef(null);
  const inputRef = useRef(null);
  const accountRef = useRef(null);
  const modeRef = useRef(null);
  const abortRef = useRef(null);
  const mountedRef = useRef(true);
  const generationRef = useRef(0);
  const textareaRef = useRef(null);

  const currentUser = getUser();

  const userLabel =
    currentUser?.name ||
    currentUser?.username ||
    currentUser?.email ||
    "Nova User";

  /* =======================================================
     CLEANUP
     ======================================================= */

  useEffect(() => {
    mountedRef.current = true;

    return () => {
      mountedRef.current = false;

      try {
        abortRef.current?.abort();
      } catch {
        // Ignore.
      }
    };
  }, []);

  /* =======================================================
     SIDEBAR STORAGE
     IMPORTANT:
     NEVER return the result of setStorage from useEffect.
     ======================================================= */

  useEffect(() => {
    if (getStorage(STORAGE.SIDEBAR) === "closed") {
      setSidebar(false);
    }
  }, []);

  useEffect(() => {
    setStorage(
      STORAGE.SIDEBAR,
      sidebar ? "open" : "closed"
    );
  }, [sidebar]);

  /* =======================================================
     LAST PAGE STORAGE
     ======================================================= */

  useEffect(() => {
    setStorage(
      STORAGE.LAST_PAGE,
      `${location.pathname}${location.search}`
    );
  }, [location.pathname, location.search]);

  /* =======================================================
     MODE
     ======================================================= */

  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  /* =======================================================
     ONLINE / OFFLINE
     ======================================================= */

  useEffect(() => {
    const handleOnline = () => {
      setOnline(true);
      setError("");
    };

    const handleOffline = () => {
      setOnline(false);
      setError(
        "You are offline. Nova cannot reach the backend."
      );
    };

    window.addEventListener(
      "online",
      handleOnline
    );

    window.addEventListener(
      "offline",
      handleOffline
    );

    return () => {
      window.removeEventListener(
        "online",
        handleOnline
      );

      window.removeEventListener(
        "offline",
        handleOffline
      );
    };
  }, []);

  /* =======================================================
     CLICK OUTSIDE MENUS
     ======================================================= */

  useEffect(() => {
    const handleClick = (event) => {
      if (
        accountRef.current &&
        !accountRef.current.contains(event.target)
      ) {
        setAccount(false);
      }

      if (
        modeRef.current &&
        !modeRef.current.contains(event.target)
      ) {
        setModeOpen(false);
      }
    };

    document.addEventListener(
      "mousedown",
      handleClick
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        handleClick
      );
    };
  }, []);

  /* =======================================================
     AUTO RESIZE TEXTAREA
     ======================================================= */

  useEffect(() => {
    const textarea = textareaRef.current;

    if (!textarea) return;

    textarea.style.height = "auto";

    const nextHeight = Math.min(
      textarea.scrollHeight,
      192
    );

    textarea.style.height = `${nextHeight}px`;
  }, [input]);

  /* =======================================================
     DRAFT
     ======================================================= */

  useEffect(() => {
    const key = draftKey(conversationId, mode);

    if (input) {
      setStorage(key, input);
      setDraftSaved(true);

      const timer = setTimeout(() => {
        if (mountedRef.current) {
          setDraftSaved(false);
        }
      }, 1200);

      return () => clearTimeout(timer);
    }

    removeStorage(key);
    setDraftSaved(false);

    return undefined;
  }, [input, conversationId, mode]);

  useEffect(() => {
    if (loading) return;

    const key = draftKey(conversationId, mode);
    const saved = getStorage(key);

    if (saved && !input) {
      setInput(saved);
    }
  }, [conversationId, mode]);

  /* =======================================================
     KEYBOARD SHORTCUTS
     ======================================================= */

  const stop = useCallback(() => {
    try {
      abortRef.current?.abort();
    } catch {
      // Ignore.
    }

    abortRef.current = null;

    if (mountedRef.current) {
      setLoading(false);
    }
  }, []);

  const scrollBottom = useCallback(
    (behavior = "smooth") => {
      end.current?.scrollIntoView({
        behavior,
        block: "end",
      });

      setShowLatest(false);
    },
    []
  );

  /* =======================================================
     SCROLL
     ======================================================= */

  useEffect(() => {
    const element = container.current;

    if (!element) return;

    const handleScroll = () => {
      const distance =
        element.scrollHeight -
        element.scrollTop -
        element.clientHeight;

      setShowLatest(distance > 350);
    };

    element.addEventListener(
      "scroll",
      handleScroll,
      { passive: true }
    );

    return () => {
      element.removeEventListener(
        "scroll",
        handleScroll
      );
    };
  }, []);

  useEffect(() => {
    const element = container.current;

    if (!element) return;

    const distance =
      element.scrollHeight -
      element.scrollTop -
      element.clientHeight;

    if (distance < 260) {
      scrollBottom(
        loading ? "auto" : "smooth"
      );
    }
  }, [
    messages,
    loading,
    scrollBottom,
  ]);

  /* =======================================================
     BACKEND CHECK
     ======================================================= */

  const checkBackend = useCallback(async () => {
    if (!navigator.onLine) {
      if (mountedRef.current) {
        setBackend(false);
      }

      return;
    }

    const controller = new AbortController();

    const timeout = setTimeout(() => {
      controller.abort();
    }, BACKEND_TIMEOUT);

    try {
      const response = await fetch(
        `${API_URL}/`,
        {
          signal: controller.signal,
        }
      );

      if (mountedRef.current) {
        setBackend(response.ok);
      }
    } catch {
      if (mountedRef.current) {
        setBackend(false);
      }
    } finally {
      clearTimeout(timeout);
    }
  }, []);

  useEffect(() => {
    checkBackend();

    const interval = setInterval(
      checkBackend,
      3000
    );

    return () => {
      clearInterval(interval);
    };
  }, [checkBackend]);

  /* =======================================================
     DEMO SESSION
     ======================================================= */

  const createDemo = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_URL}/demo/session`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(
          `Demo session failed: HTTP ${response.status}`
        );
      }

      const data = await response.json();

      if (!data?.session_id) {
        throw new Error(
          "Nova returned an invalid demo session."
        );
      }

      if (mountedRef.current) {
        setDemoSession(data.session_id);
      }

      return data.session_id;
    } catch (error) {
      if (mountedRef.current) {
        setError(friendlyError(error));
      }

      return null;
    }
  }, []);

  /* =======================================================
     LOAD HISTORY
     ======================================================= */

  const loadHistory = useCallback(async () => {
    if (demo) return;

    const user = getUser();

    if (!user?.email) {
      navigate("/login", {
        replace: true,
      });

      return;
    }

    setHistoryLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/conversations/${encodeURIComponent(
          user.email
        )}`
      );

      if (!response.ok) {
        throw new Error(
          `History request failed: HTTP ${response.status}`
        );
      }

      const data = await response.json();

      const items = Object.entries(
        data || {}
      ).map(([id, conversation]) => ({
        id,
        ...conversation,
      }));

      if (mountedRef.current) {
        setHistory(sortHistory(items));
      }
    } catch (error) {
      if (mountedRef.current) {
        setError(friendlyError(error));
      }
    } finally {
      if (mountedRef.current) {
        setHistoryLoading(false);
      }
    }
  }, [demo, navigate]);

  /* =======================================================
     OPEN CONVERSATION
     ======================================================= */

  const openConversation = useCallback(
    async (id) => {
      if (
        loading ||
        demo ||
        !id
      ) {
        return;
      }

      const user = getUser();

      if (!user?.email) {
        navigate("/login", {
          replace: true,
        });

        return;
      }

      try {
        const response = await fetch(
          `${API_URL}/conversation/${encodeURIComponent(
            user.email
          )}/${encodeURIComponent(id)}`
        );

        if (!response.ok) {
          throw new Error(
            `Could not open conversation: HTTP ${response.status}`
          );
        }

        const conversation =
          await response.json();

        if (!mountedRef.current) {
          return;
        }

        setConversationId(id);

        setStorage(
          STORAGE.CURRENT,
          id
        );

        const normalized = Array.isArray(
          conversation?.messages
        )
          ? conversation.messages.map(
              normalizeMessage
            )
          : [];

        setMessages(normalized);
        setError("");

        const savedDraft = getStorage(
          draftKey(id, mode)
        );

        setInput(savedDraft || "");

        if (window.innerWidth < 768) {
          setSidebar(false);
        }

        requestAnimationFrame(() => {
          scrollBottom("auto");
        });
      } catch (error) {
        if (mountedRef.current) {
          setError(friendlyError(error));
        }
      }
    },
    [
      loading,
      demo,
      navigate,
      scrollBottom,
      mode,
    ]
  );

  /* =======================================================
     CREATE CONVERSATION
     ======================================================= */

  const createConversation =
    useCallback(async () => {
      if (demo) {
        return null;
      }

      const user = getUser();

      if (!user?.email) {
        navigate("/login", {
          replace: true,
        });

        return null;
      }

      try {
        const response = await fetch(
          `${API_URL}/conversation/new`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              email: user.email,
            }),
          }
        );

        if (!response.ok) {
          throw new Error(
            `Conversation creation failed: HTTP ${response.status}`
          );
        }

        const data =
          await response.json();

        if (!data?.id) {
          throw new Error(
            "Nova created an invalid conversation."
          );
        }

        setStorage(
          STORAGE.CURRENT,
          data.id
        );

        if (mountedRef.current) {
          setConversationId(data.id);
        }

        return data.id;
      } catch (error) {
        if (mountedRef.current) {
          setError(friendlyError(error));
        }

        return null;
      }
    }, [demo, navigate]);

  /* =======================================================
     INITIAL LOAD
     ======================================================= */

  useEffect(() => {
    let cancelled = false;

    const initialize = async () => {
      if (demo) {
        setMessages([]);
        setHistory([]);
        setConversationId(null);

        const session =
          await createDemo();

        if (
          !cancelled &&
          session
        ) {
          setDemoSession(session);
        }

        return;
      }

      const user = getUser();

      if (!user?.email) {
        navigate("/login", {
          replace: true,
        });

        return;
      }

      await loadHistory();

      if (cancelled) return;

      const storedConversation =
        getStorage(STORAGE.CURRENT);

      if (storedConversation) {
        await openConversation(
          storedConversation
        );
      }
    };

    initialize();

    return () => {
      cancelled = true;
    };
  }, [
    demo,
    navigate,
    createDemo,
    loadHistory,
    openConversation,
  ]);

  /* =======================================================
     NEW CHAT
     ======================================================= */

  const newChat = useCallback(async () => {
    if (loading) return;

    stop();

    setError("");
    setSearch("");
    setMessageSearch("");

    if (demo) {
      setMessages([]);
      setConversationId(null);
      setInput("");

      const session =
        await createDemo();

      if (session) {
        setDemoSession(session);
      }

      requestAnimationFrame(() => {
        inputRef.current?.focus();
      });

      return;
    }

    const id =
      await createConversation();

    if (!id) return;

    setMessages([]);
    setInput("");

    await loadHistory();

    requestAnimationFrame(() => {
      inputRef.current?.focus();
    });
  }, [
    loading,
    stop,
    demo,
    createDemo,
    createConversation,
    loadHistory,
  ]);

  /* =======================================================
     SEND MESSAGE
     ======================================================= */

  const send = useCallback(
    async (override = null) => {
      const text = String(
        override ?? input
      ).trim();

      if (!text || loading) {
        return;
      }

      if (text.length > MAX_INPUT) {
        setError(
          `Your message is too long. Keep it under ${MAX_INPUT.toLocaleString()} characters.`
        );

        return;
      }

      if (!navigator.onLine) {
        setOnline(false);
        setError(
          "You're offline. Nova cannot send the message right now."
        );

        return;
      }

      const generation =
        ++generationRef.current;

      setMessages((previous) => [
        ...previous,
        {
          role: "user",
          text,
        },
      ]);

      setInput("");
      removeStorage(
        draftKey(conversationId, mode)
      );

      setLoading(true);
      setError("");

      const controller =
        new AbortController();

      abortRef.current = controller;

      try {
        let response;

        if (demo) {
          let session =
            demoSession;

          if (!session) {
            session =
              await createDemo();
          }

          if (!session) {
            throw new Error(
              "Could not create demo session."
            );
          }

          response = await fetch(
            `${API_URL}/demo/chat/stream`,
            {
              method: "POST",
              headers: {
                "Content-Type":
                  "application/json",
                Accept: "text/plain",
              },
              body: JSON.stringify({
                message: text,
                session_id: session,
                tutor_mode: mode,
              }),
              signal:
                controller.signal,
            }
          );
        } else {
          const user = getUser();

          if (!user?.email) {
            navigate("/login", {
              replace: true,
            });

            return;
          }

          let currentId =
            getStorage(
              STORAGE.CURRENT
            );

          if (!currentId) {
            currentId =
              await createConversation();
          }

          if (!currentId) {
            throw new Error(
              "Could not create conversation."
            );
          }

          if (mountedRef.current) {
            setConversationId(
              currentId
            );
          }

          response = await fetch(
            `${API_URL}/chat/stream`,
            {
              method: "POST",
              headers: {
                "Content-Type":
                  "application/json",
                Accept: "text/plain",
              },
              body: JSON.stringify({
                message: text,
                email: user.email,
                conversation_id:
                  currentId,
                tutor_mode: mode,
              }),
              signal:
                controller.signal,
            }
          );
        }

        if (!response.ok) {
          let body = "";

          try {
            body =
              await response.text();
          } catch {
            // Ignore.
          }

          throw new Error(
            body ||
              `Nova request failed: HTTP ${response.status}`
          );
        }

        const returnedConversation =
          response.headers.get(
            "X-Conversation-ID"
          );

        if (
          returnedConversation &&
          !demo
        ) {
          setConversationId(
            returnedConversation
          );

          setStorage(
            STORAGE.CURRENT,
            returnedConversation
          );
        }

        if (
          !mountedRef.current ||
          generationRef.current !==
            generation
        ) {
          return;
        }

        setMessages((previous) => [
          ...previous,
          {
            role: "nova",
            text: "",
            streaming: true,
          },
        ]);

        let answer = "";

        await streamText(
          response,
          (chunk) => {
            answer += chunk;

            if (
              !mountedRef.current ||
              generationRef.current !==
                generation
            ) {
              return;
            }

            setMessages((previous) => {
              const copy = [
                ...previous,
              ];

              const lastIndex =
                copy.length - 1;

              if (
                lastIndex < 0 ||
                copy[lastIndex].role !==
                  "nova"
              ) {
                return previous;
              }

              copy[lastIndex] = {
                ...copy[lastIndex],
                text: answer,
                streaming: true,
                error: false,
              };

              return copy;
            });
          },
          controller.signal
        );

        if (
          mountedRef.current &&
          generationRef.current ===
            generation
        ) {
          setMessages((previous) => {
            const copy = [
              ...previous,
            ];

            const lastIndex =
              copy.length - 1;

            if (
              lastIndex < 0 ||
              copy[lastIndex].role !==
                "nova"
            ) {
              return previous;
            }

            copy[lastIndex] = {
              ...copy[lastIndex],
              text:
                answer ||
                "Nova returned an empty response.",
              streaming: false,
              error: false,
            };

            return copy;
          });
        }

        if (!demo) {
          await loadHistory();
        }
      } catch (error) {
        if (
          error?.name !==
          "AbortError"
        ) {
          const message =
            friendlyError(error);

          if (mountedRef.current) {
            setError(message);

            setMessages((previous) => [
              ...previous,
              {
                role: "nova",
                text: message,
                error: true,
                streaming: false,
              },
            ]);
          }
        } else if (
          mountedRef.current
        ) {
          setMessages((previous) => {
            const copy = [
              ...previous,
            ];

            const lastIndex =
              copy.length - 1;

            if (
              lastIndex >= 0 &&
              copy[lastIndex].streaming
            ) {
              copy[lastIndex] = {
                ...copy[lastIndex],
                streaming: false,
                text:
                  copy[lastIndex].text ||
                  "Generation stopped.",
              };
            }

            return copy;
          });
        }
      } finally {
        if (
          abortRef.current ===
          controller
        ) {
          abortRef.current = null;
        }

        if (
          mountedRef.current &&
          generationRef.current ===
            generation
        ) {
          setLoading(false);
        }
      }
    },
    [
      input,
      loading,
      conversationId,
      mode,
      demo,
      demoSession,
      createDemo,
      createConversation,
      loadHistory,
      navigate,
    ]
  );

  /* =======================================================
     REGENERATE
     ======================================================= */

  const regenerate = useCallback(
    async (index) => {
      if (loading) return;

      const previousUserMessage =
        messages
          .slice(0, index)
          .reverse()
          .find(
            (message) =>
              message.role === "user"
          );

      if (!previousUserMessage?.text) {
        return;
      }

      setMessages((previous) =>
        previous.slice(0, index)
      );

      await send(
        previousUserMessage.text
      );
    },
    [
      loading,
      messages,
      send,
    ]
  );

  /* =======================================================
     RETRY LAST USER MESSAGE
     ======================================================= */

  const retryLast = useCallback(async () => {
    if (loading) return;

    const lastUser =
      [...messages]
        .reverse()
        .find(
          (message) =>
            message.role === "user"
        );

    if (!lastUser?.text) return;

    setMessages((previous) => {
      const lastIndex =
        [...previous]
          .map(
            (message, index) => ({
              message,
              index,
            })
          )
          .reverse()
          .find(
            ({ message }) =>
              message.role === "nova" &&
              message.error
          )?.index;

      if (
        typeof lastIndex ===
        "number"
      ) {
        return previous.slice(
          0,
          lastIndex
        );
      }

      return previous;
    });

    await send(lastUser.text);
  }, [
    loading,
    messages,
    send,
  ]);

  /* =======================================================
     COPY
     ======================================================= */

  const copy = useCallback(
    async (text) => {
      try {
        await navigator.clipboard.writeText(
          text
        );

        setCopied(true);

        setTimeout(() => {
          if (mountedRef.current) {
            setCopied(false);
          }
        }, 1600);
      } catch {
        setError(
          "Nova could not copy that response."
        );
      }
    },
    []
  );

  /* =======================================================
     RENAME
     ======================================================= */

  const rename = useCallback(
    async (id, title) => {
      if (loading || demo) return;

      const user = getUser();

      if (!user?.email) return;

      const next =
        window.prompt(
          "Conversation name:",
          title || "New Chat"
        );

      if (!next?.trim()) return;

      try {
        const response =
          await fetch(
            `${API_URL}/conversation/${encodeURIComponent(
              user.email
            )}/${encodeURIComponent(
              id
            )}/rename`,
            {
              method: "PUT",
              headers: {
                "Content-Type":
                  "application/json",
              },
              body: JSON.stringify({
                email: user.email,
                title: next.trim(),
              }),
            }
          );

        if (!response.ok) {
          throw new Error(
            `Rename failed: HTTP ${response.status}`
          );
        }

        await loadHistory();
      } catch (error) {
        setError(
          friendlyError(error)
        );
      }
    },
    [
      loading,
      demo,
      loadHistory,
    ]
  );

  /* =======================================================
     DELETE
     ======================================================= */

  const deleteConversation =
    useCallback(
      async (id) => {
        if (loading || demo) {
          return;
        }

        const user = getUser();

        if (!user?.email) return;

        try {
          const response =
            await fetch(
              `${API_URL}/conversation/${encodeURIComponent(
                user.email
              )}/${encodeURIComponent(
                id
              )}`,
              {
                method: "DELETE",
              }
            );

          if (!response.ok) {
            throw new Error(
              `Delete failed: HTTP ${response.status}`
            );
          }

          if (
            getStorage(
              STORAGE.CURRENT
            ) === id
          ) {
            removeStorage(
              STORAGE.CURRENT
            );

            setConversationId(null);
            setMessages([]);
            setInput("");
          }

          setDeleteItem(null);

          await loadHistory();
        } catch (error) {
          setDeleteItem(null);
          setError(
            friendlyError(error)
          );
        }
      },
      [
        loading,
        demo,
        loadHistory,
      ]
    );

  /* =======================================================
     EXPORT
     ======================================================= */

  const downloadFile = useCallback(
    (content, filename, type) => {
      try {
        const blob = new Blob(
          [content],
          { type }
        );

        const url =
          URL.createObjectURL(blob);

        const link =
          document.createElement("a");

        link.href = url;
        link.download = filename;

        document.body.appendChild(
          link
        );

        link.click();

        link.remove();

        setTimeout(() => {
          URL.revokeObjectURL(url);
        }, 1000);
      } catch {
        setError(
          "Nova could not export this conversation."
        );
      }
    },
    []
  );

  const exportText = useCallback(() => {
    if (!messages.length) return;

    const date =
      new Date()
        .toISOString()
        .slice(0, 10);

    downloadFile(
      messagesToText(messages),
      `nova-chat-${date}.txt`,
      "text/plain;charset=utf-8"
    );
  }, [
    messages,
    downloadFile,
  ]);

  const exportMarkdown =
    useCallback(() => {
      if (!messages.length) return;

      const date =
        new Date()
          .toISOString()
          .slice(0, 10);

      downloadFile(
        messagesToMarkdown(messages),
        `nova-chat-${date}.md`,
        "text/markdown;charset=utf-8"
      );
    }, [
      messages,
      downloadFile,
    ]);

  /* =======================================================
     LOGOUT
     ======================================================= */

  const logout = useCallback(() => {
    stop();

    removeStorage(
      STORAGE.USER
    );

    removeStorage(
      STORAGE.CURRENT
    );

    removeStorage(
      STORAGE.LAST_PAGE
    );

    navigate("/login", {
      replace: true,
    });
  }, [navigate, stop]);

  /* =======================================================
     PROMPT
     ======================================================= */

  const usePrompt = useCallback(
    (text) => {
      setInput(text);

      requestAnimationFrame(() => {
        inputRef.current?.focus();
      });
    },
    []
  );

  /* =======================================================
     ENTER
     ======================================================= */

  const handleKeyDown =
    useCallback(
      (event) => {
        if (
          event.key === "Enter" &&
          !event.shiftKey
        ) {
          event.preventDefault();
          send();
        }
      },
      [send]
    );

  /* =======================================================
     KEYBOARD SHORTCUTS
     ======================================================= */

  useEffect(() => {
    const handleKeyDown = (event) => {
      const target =
        event.target;

      const typing =
        target?.isContentEditable ||
        ["INPUT", "TEXTAREA", "SELECT"].includes(
          target?.tagName
        );

      if (
        (event.ctrlKey ||
          event.metaKey) &&
        event.key.toLowerCase() ===
          "k"
      ) {
        event.preventDefault();

        setSidebar(true);

        setTimeout(() => {
          document
            .querySelector(
              "[data-chat-search]"
            )
            ?.focus();
        }, 0);

        return;
      }

      if (
        (event.ctrlKey ||
          event.metaKey) &&
        event.key.toLowerCase() ===
          "n"
      ) {
        event.preventDefault();

        if (!loading) {
          newChat();
        }

        return;
      }

      if (
        (event.ctrlKey ||
          event.metaKey) &&
        event.key.toLowerCase() ===
          "e"
      ) {
        event.preventDefault();

        exportMarkdown();

        return;
      }

      if (
        event.key === "Escape"
      ) {
        setAccount(false);
        setModeOpen(false);

        if (loading) {
          stop();
        }

        return;
      }

      if (
        !typing &&
        event.key === "/"
      ) {
        event.preventDefault();
        inputRef.current?.focus();
      }
    };

    window.addEventListener(
      "keydown",
      handleKeyDown
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleKeyDown
      );
    };
  }, [
    loading,
    newChat,
    exportMarkdown,
    stop,
  ]);

  /* =======================================================
     FILTER HISTORY
     ======================================================= */

  const filteredHistory =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      if (!query) {
        return history;
      }

      return history.filter(
        (item) =>
          String(
            item.title || ""
          )
            .toLowerCase()
            .includes(query) ||
          conversationPreview(item)
            .toLowerCase()
            .includes(query)
      );
    }, [history, search]);

  /* =======================================================
     FILTER CURRENT MESSAGES
     ======================================================= */

  const visibleMessages =
    useMemo(() => {
      const query =
        messageSearch
          .trim()
          .toLowerCase();

      if (!query) {
        return messages;
      }

      return messages.filter(
        (message) =>
          message.text
            ?.toLowerCase()
            .includes(query)
      );
    }, [
      messages,
      messageSearch,
    ]);

  const activeMode =
    MODES.find(
      (item) => item.id === mode
    ) || MODES[0];

  const ModeIcon =
    activeMode.icon;

  /* =======================================================
     RENDER
     ======================================================= */

  return (
    <div className="nova-chat-shell flex h-[100dvh] min-h-[560px] overflow-hidden bg-[#04060b] text-white">
      {/* BACKGROUND */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -left-32 -top-40 h-[520px] w-[520px] rounded-full bg-sky-500/[.045] blur-[110px]" />

        <div className="absolute -right-40 top-20 h-[500px] w-[500px] rounded-full bg-violet-500/[.035] blur-[120px]" />

        <div className="absolute bottom-[-250px] left-1/2 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-cyan-500/[.02] blur-[130px]" />
      </div>

      {/* MOBILE SIDEBAR OVERLAY */}
      {sidebar && (
        <button
          className="fixed inset-0 z-30 bg-black/65 backdrop-blur-sm md:hidden"
          onClick={() =>
            setSidebar(false)
          }
          aria-label="Close sidebar"
        />
      )}

      {/* ===================================================
          SIDEBAR
          =================================================== */}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-[320px] shrink-0 flex-col border-r border-white/[.07] bg-[#070a11]/95 shadow-2xl backdrop-blur-2xl transition-transform duration-300 md:relative md:z-auto md:translate-x-0 ${
          sidebar
            ? "translate-x-0"
            : "-translate-x-full md:-ml-[320px]"
        }`}
      >
        {/* SIDEBAR HEADER */}
        <div className="flex h-[68px] shrink-0 items-center justify-between border-b border-white/[.07] px-4">
          <button
            onClick={() =>
              navigate("/")
            }
            className="group flex items-center gap-3 rounded-xl px-2 py-2 text-slate-300 hover:bg-white/[.05] hover:text-white"
          >
            <ArrowLeft size={18} />

            <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-white/10 bg-white/[.05]">
              <Sparkles size={15} />
            </div>

            <div className="text-left">
              <div className="text-sm font-bold">
                NOVA AI
              </div>

              <div className="text-[10px] text-slate-600">
                Learning workspace
              </div>
            </div>
          </button>

          <button
            onClick={() =>
              setSidebar(false)
            }
            className="rounded-lg p-2 text-slate-500 hover:bg-white/[.05] hover:text-white md:hidden"
          >
            <X size={18} />
          </button>
        </div>

        {/* NEW CHAT */}
        <div className="px-4 pt-4">
          <button
            onClick={newChat}
            disabled={loading}
            className="flex w-full items-center justify-center gap-2.5 rounded-2xl border border-white/10 bg-white/[.065] px-4 py-3.5 text-sm font-semibold transition hover:bg-white/[.1] disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Plus size={17} />
            New Chat

            <span className="ml-auto hidden text-[9px] text-slate-600 lg:block">
              Ctrl N
            </span>
          </button>
        </div>

        {/* SEARCH */}
        {!demo && (
          <div className="px-4 pb-3 pt-4">
            <div className="relative">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600"
              />

              <input
                data-chat-search
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
                placeholder="Search chats..."
                className="w-full rounded-xl border border-white/[.07] bg-black/20 py-2.5 pl-9 pr-12 text-xs outline-none placeholder:text-slate-600 focus:border-sky-400/20"
              />

              <kbd className="absolute right-2.5 top-1/2 hidden -translate-y-1/2 rounded-md border border-white/10 px-1.5 py-0.5 text-[9px] text-slate-600 lg:block">
                Ctrl K
              </kbd>
            </div>
          </div>
        )}

        {/* STATS */}
        {!demo && (
          <div className="mx-4 mb-2 grid grid-cols-2 gap-2">
            <div className="rounded-xl border border-white/[.06] bg-white/[.025] px-3 py-2.5">
              <div className="text-[9px] uppercase tracking-[.14em] text-slate-600">
                Chats
              </div>

              <div className="mt-1 text-sm font-semibold text-slate-300">
                {history.length}
              </div>
            </div>

            <div className="rounded-xl border border-white/[.06] bg-white/[.025] px-3 py-2.5">
              <div className="text-[9px] uppercase tracking-[.14em] text-slate-600">
                Status
              </div>

              <div className="mt-1 flex items-center gap-1.5 text-sm text-slate-300">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    backend === true
                      ? "bg-emerald-400"
                      : backend === false
                      ? "bg-red-400"
                      : "bg-slate-600"
                  }`}
                />

                {backend === true
                  ? "Online"
                  : backend === false
                  ? "Offline"
                  : "Checking"}
              </div>
            </div>
          </div>
        )}

        {/* HISTORY */}
        <div className="nova-scrollbar min-h-0 flex-1 overflow-y-auto px-2 pb-3">
          {demo ? (
            <div className="mx-2 mt-3 rounded-2xl border border-white/[.06] bg-white/[.025] p-4 text-xs leading-5 text-slate-500">
              <div className="mb-2 flex items-center gap-2 text-slate-300">
                <MessageSquare size={14} />
                Demo conversation
              </div>

              Messages use a temporary demo
              session.
            </div>
          ) : historyLoading &&
            !history.length ? (
            <div className="space-y-2 px-2 pt-3">
              {[1, 2, 3, 4].map(
                (item) => (
                  <div
                    key={item}
                    className="h-16 animate-pulse rounded-xl bg-white/[.025]"
                  />
                )
              )}
            </div>
          ) : !filteredHistory.length ? (
            <div className="px-5 py-12 text-center">
              <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-2xl border border-white/[.07] bg-white/[.025] text-slate-600">
                <History size={18} />
              </div>

              <p className="mt-4 text-xs text-slate-500">
                {search
                  ? "No matching chats"
                  : "No conversations yet"}
              </p>
            </div>
          ) : (
            <div className="space-y-1 pt-2">
              {filteredHistory.map(
                (item) => {
                  const active =
                    item.id ===
                    conversationId;

                  return (
                    <div
                      key={item.id}
                      className={`group relative rounded-xl border ${
                        active
                          ? "border-white/[.09] bg-white/[.055]"
                          : "border-transparent hover:border-white/[.05] hover:bg-white/[.025]"
                      }`}
                    >
                      <button
                        onClick={() =>
                          openConversation(
                            item.id
                          )
                        }
                        disabled={loading}
                        className="w-full px-3 py-3 text-left"
                      >
                        <div className="flex items-start gap-2.5">
                          <MessageSquare
                            size={14}
                            className={`mt-0.5 ${
                              active
                                ? "text-slate-300"
                                : "text-slate-600"
                            }`}
                          />

                          <div className="min-w-0 flex-1">
                            <div className="flex gap-2">
                              <span className="min-w-0 flex-1 truncate text-xs font-medium text-slate-300">
                                {item.title ||
                                  "New Chat"}
                              </span>

                              <span className="text-[9px] text-slate-700">
                                {formatDate(
                                  item.updated_at ||
                                    item.created_at
                                )}
                              </span>
                            </div>

                            <p className="mt-1 truncate text-[10px] text-slate-600">
                              {conversationPreview(
                                item
                              )}
                            </p>
                          </div>
                        </div>
                      </button>

                      {!loading && (
                        <div className="absolute right-2 top-2 hidden gap-0.5 rounded-lg border border-white/[.06] bg-[#0b0e15] p-0.5 shadow-xl group-hover:flex">
                          <button
                            onClick={() =>
                              rename(
                                item.id,
                                item.title
                              )
                            }
                            className="rounded-md p-1.5 text-slate-600 hover:bg-white/[.06] hover:text-slate-200"
                            title="Rename"
                          >
                            <Edit3 size={12} />
                          </button>

                          <button
                            onClick={() =>
                              setDeleteItem(
                                item
                              )
                            }
                            className="rounded-md p-1.5 text-slate-600 hover:bg-red-500/10 hover:text-red-300"
                            title="Delete"
                          >
                            <Trash2 size={12} />
                          </button>
                        </div>
                      )}
                    </div>
                  );
                }
              )}
            </div>
          )}
        </div>

        {/* ACCOUNT */}
        <div className="shrink-0 border-t border-white/[.07] p-3">
          <div
            ref={accountRef}
            className="relative"
          >
            {account && (
              <div className="absolute bottom-full left-0 right-0 mb-2 rounded-2xl border border-white/10 bg-[#0b0e15] p-1.5 shadow-2xl">
                <button
                  onClick={() => {
                    setAccount(false);
                    navigate(
                      "/settings"
                    );
                  }}
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-xs text-slate-400 hover:bg-white/[.05] hover:text-white"
                >
                  <Settings size={15} />
                  Settings
                </button>

                <button
                  onClick={logout}
                  className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-xs text-slate-400 hover:bg-red-500/[.07] hover:text-red-300"
                >
                  <LogOut size={15} />
                  Log out
                </button>
              </div>
            )}

            <button
              onClick={() =>
                setAccount(
                  (value) => !value
                )
              }
              className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left hover:bg-white/[.04]"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-white/10 bg-white/[.05] text-xs">
                {userLabel
                  .slice(0, 1)
                  .toUpperCase()}
              </div>

              <div className="min-w-0 flex-1">
                <div className="truncate text-xs text-slate-300">
                  {userLabel}
                </div>

                <div className="text-[10px] text-slate-600">
                  {demo
                    ? "Demo account"
                    : "Nova learner"}
                </div>
              </div>

              <ChevronDown
                size={14}
                className={
                  account
                    ? "rotate-180 text-slate-600"
                    : "text-slate-600"
                }
              />
            </button>
          </div>
        </div>
      </aside>

      {/* ===================================================
          MAIN
          =================================================== */}

      <section className="relative z-10 flex min-w-0 flex-1 flex-col">
        {/* HEADER */}
        <header className="flex h-[68px] shrink-0 items-center justify-between border-b border-white/[.07] bg-[#05070c]/80 px-3 backdrop-blur-2xl sm:px-5">
          <div className="flex min-w-0 items-center gap-2.5">
            <button
              onClick={() =>
                setSidebar(
                  (value) => !value
                )
              }
              className="rounded-xl p-2.5 text-slate-500 hover:bg-white/[.05] hover:text-white"
              title="Toggle sidebar"
            >
              {sidebar ? (
                <PanelLeftClose
                  size={19}
                />
              ) : (
                <PanelLeft size={19} />
              )}
            </button>

            <div className="hidden h-7 w-px bg-white/[.07] sm:block" />

            <div className="flex min-w-0 items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/[.05]">
                <Sparkles size={16} />
              </div>

              <div className="min-w-0">
                <div className="truncate text-sm font-semibold">
                  {demo
                    ? "Nova Demo"
                    : "Nova AI"}
                </div>

                <div className="flex items-center gap-1.5 text-[10px] text-slate-600">
                  {demo
                    ? "Demo Mode"
                    : activeMode.label}

                  <span>•</span>

                  <span
                    className={
                      backend === true
                        ? "text-emerald-500"
                        : backend === false
                        ? "text-red-400"
                        : "text-slate-600"
                    }
                  >
                    ●{" "}
                    {backend === true
                      ? "Online"
                      : backend === false
                      ? "Offline"
                      : "Connecting"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* MODE */}
            <div
              ref={modeRef}
              className="relative hidden sm:block"
            >
              <button
                onClick={() =>
                  setModeOpen(
                    (value) => !value
                  )
                }
                className="flex items-center gap-2 rounded-xl border border-white/[.07] bg-white/[.025] px-3 py-2 text-xs text-slate-400 hover:bg-white/[.05]"
              >
                <ModeIcon size={14} />

                {activeMode.label}

                <ChevronDown size={13} />
              </button>

              {modeOpen && (
                <div className="absolute right-0 top-full z-50 mt-2 w-72 rounded-2xl border border-white/10 bg-[#0b0e15] p-1.5 shadow-2xl">
                  {MODES.map(
                    (item) => {
                      const Icon =
                        item.icon;

                      return (
                        <button
                          key={
                            item.id
                          }
                          onClick={() => {
                            setMode(
                              item.id
                            );

                            setModeOpen(
                              false
                            );
                          }}
                          className={`flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left ${
                            mode ===
                            item.id
                              ? "bg-white/[.06] text-white"
                              : "text-slate-400 hover:bg-white/[.04]"
                          }`}
                        >
                          <Icon
                            size={15}
                            className="mt-1"
                          />

                          <div>
                            <div className="flex gap-2 text-xs font-semibold">
                              {item.label}

                              {mode ===
                                item.id && (
                                <Check
                                  size={
                                    13
                                  }
                                  className="text-emerald-400"
                                />
                              )}
                            </div>

                            <div className="mt-1 text-[10px] text-slate-600">
                              {
                                item.description
                              }
                            </div>
                          </div>
                        </button>
                      );
                    }
                  )}
                </div>
              )}
            </div>

            {/* EXPORT */}
            {messages.length > 0 && (
              <div className="relative hidden lg:block">
                <button
                  onClick={
                    exportMarkdown
                  }
                  className="rounded-xl p-2.5 text-slate-600 hover:bg-white/[.05] hover:text-slate-200"
                  title="Export conversation"
                >
                  <Download size={17} />
                </button>
              </div>
            )}

            <button
              onClick={() =>
                navigate("/settings")
              }
              className="hidden rounded-xl p-2.5 text-slate-600 hover:bg-white/[.05] hover:text-slate-200 sm:block"
            >
              <Settings size={17} />
            </button>

            <button
              onClick={() =>
                setSidebar(true)
              }
              className="rounded-xl p-2.5 text-slate-500 hover:bg-white/[.05] md:hidden"
            >
              <Menu size={19} />
            </button>
          </div>
        </header>

        {/* ERROR */}
        {error && (
          <div className="border-b border-red-500/10 bg-red-500/[.035] px-4 py-2.5">
            <div className="mx-auto flex max-w-5xl items-center gap-2 text-xs text-red-300">
              <AlertCircle size={14} />

              <span className="flex-1">
                {error}
              </span>

              <button
                onClick={() =>
                  setError("")
                }
              >
                <X size={13} />
              </button>
            </div>
          </div>
        )}

        {/* OFFLINE */}
        {!online && (
          <div className="border-b border-amber-500/10 bg-amber-500/[.035] px-4 py-2">
            <div className="mx-auto flex max-w-5xl items-center justify-center gap-2 text-[11px] text-amber-300">
              <WifiOff size={13} />
              Offline mode
            </div>
          </div>
        )}

        {/* CURRENT SEARCH */}
        {messages.length > 0 && (
          <div className="border-b border-white/[.05] bg-[#05070c]/70 px-4 py-2">
            <div className="mx-auto flex max-w-5xl items-center gap-2">
              <Search
                size={13}
                className="text-slate-700"
              />

              <input
                value={
                  messageSearch
                }
                onChange={(event) =>
                  setMessageSearch(
                    event.target.value
                  )
                }
                placeholder="Search in this conversation..."
                className="min-w-0 flex-1 bg-transparent text-xs text-slate-400 outline-none placeholder:text-slate-700"
              />

              {messageSearch && (
                <button
                  onClick={() =>
                    setMessageSearch(
                      ""
                    )
                  }
                  className="text-slate-600 hover:text-white"
                >
                  <X size={13} />
                </button>
              )}

              <span className="hidden text-[9px] text-slate-700 sm:block">
                {visibleMessages.length}{" "}
                / {messages.length}
              </span>
            </div>
          </div>
        )}

        {/* =================================================
            CHAT CONTENT
            ================================================= */}

        <main
          ref={container}
          className="nova-scrollbar min-h-0 flex-1 overflow-y-auto"
        >
          {!messages.length ? (
            <div className="mx-auto flex min-h-full w-full max-w-4xl items-center justify-center px-4 py-12">
              <div className="w-full">
                <div className="text-center">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-[22px] border border-white/10 bg-white/[.045] shadow-2xl">
                    <Sparkles size={26} />
                  </div>

                  <p className="mt-7 text-[10px] font-bold uppercase tracking-[.25em] text-slate-600">
                    NOVA AI
                  </p>

                  <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                    What are you learning
                    today?
                  </h1>

                  <p className="mx-auto mt-4 max-w-xl text-sm leading-6 text-slate-500">
                    Ask Nova to explain a
                    concept, guide you
                    through a problem, quiz
                    you, or help you study.
                  </p>

                  <div className="mt-3 flex items-center justify-center gap-2 text-[10px] text-slate-700">
                    {backend === true ? (
                      <>
                        <Wifi
                          size={11}
                        />
                        Backend connected
                      </>
                    ) : (
                      <>
                        <WifiOff
                          size={11}
                        />
                        Backend unavailable
                      </>
                    )}
                  </div>
                </div>

                {/* STARTERS */}
                <div className="mt-10 grid gap-2 sm:grid-cols-2">
                  {STARTERS.map(
                    ([label, prompt]) => (
                      <button
                        key={label}
                        onClick={() =>
                          usePrompt(
                            prompt
                          )
                        }
                        className="group rounded-2xl border border-white/[.07] bg-white/[.025] p-4 text-left transition hover:-translate-y-0.5 hover:bg-white/[.045]"
                      >
                        <div className="flex items-center gap-2.5">
                          <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/[.07] bg-white/[.03] text-slate-500">
                            <Lightbulb
                              size={
                                15
                              }
                            />
                          </div>

                          <span className="text-xs font-semibold text-slate-300">
                            {label}
                          </span>
                        </div>

                        <p className="mt-3 text-[11px] leading-5 text-slate-600">
                          {prompt}
                        </p>
                      </button>
                    )
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="mx-auto flex w-full max-w-5xl flex-col gap-7 px-4 py-6 md:px-6 md:py-8">
              {visibleMessages.map(
                (message, index) => (
                  <Message
                    key={`${index}-${message.role}-${message.text.slice(
                      0,
                      20
                    )}`}
                    message={message}
                    index={index}
                    copy={copy}
                    regenerate={
                      regenerate
                    }
                    continuePrompt={
                      usePrompt
                    }
                    retry={retryLast}
                  />
                )
              )}

              <div ref={end} />
            </div>
          )}
        </main>

        {/* JUMP TO LATEST */}
        {showLatest && (
          <button
            onClick={() =>
              scrollBottom()
            }
            className="absolute bottom-40 left-1/2 z-20 flex -translate-x-1/2 items-center gap-2 rounded-full border border-white/10 bg-[#0b0e15]/95 px-3.5 py-2 text-xs text-slate-300 shadow-2xl"
          >
            <ArrowDown size={14} />
            Jump to latest
          </button>
        )}

        {/* =================================================
            COMPOSER
            ================================================= */}

        <div className="relative z-20 shrink-0 bg-gradient-to-t from-[#04060b] via-[#04060b]/98 to-transparent px-3 pb-3 pt-4 sm:px-5 sm:pb-5">
          <div className="mx-auto w-full max-w-4xl">
            {/* QUICK ACTIONS */}
            <div className="mb-2 flex gap-1.5 overflow-x-auto pb-1">
              {QUICK_ACTIONS.map(
                ([label, Icon, text]) => (
                  <button
                    key={label}
                    onClick={() =>
                      usePrompt(text)
                    }
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-white/[.06] bg-white/[.02] px-3 py-1.5 text-[10px] text-slate-600 hover:text-slate-300"
                  >
                    <Icon size={11} />
                    {label}
                  </button>
                )
              )}
            </div>

            {/* COMPOSER */}
            <div
              className={`rounded-[22px] border bg-[#090c13]/95 p-2 shadow-2xl ${
                loading
                  ? "border-sky-400/15"
                  : "border-white/[.09]"
              }`}
            >
              <div className="flex items-end gap-2">
                <textarea
                  ref={(element) => {
                    textareaRef.current =
                      element;
                    inputRef.current =
                      element;
                  }}
                  value={input}
                  onChange={(event) => {
                    if (
                      event.target
                        .value.length <=
                      MAX_INPUT
                    ) {
                      setInput(
                        event.target
                          .value
                      );
                    }
                  }}
                  onKeyDown={
                    handleKeyDown
                  }
                  disabled={loading}
                  rows={1}
                  maxLength={
                    MAX_INPUT
                  }
                  placeholder={
                    loading
                      ? "Nova is working..."
                      : "Ask Nova anything..."
                  }
                  className="min-h-[52px] max-h-48 flex-1 resize-none overflow-y-auto bg-transparent px-3 py-3.5 text-sm leading-6 outline-none placeholder:text-slate-600"
                />

                <div className="mb-1 flex items-center gap-1">
                  {input && (
                    <button
                      onClick={() =>
                        setInput("")
                      }
                      disabled={
                        loading
                      }
                      className="rounded-xl p-2.5 text-slate-600 hover:bg-white/[.05] hover:text-slate-300"
                      title="Clear"
                    >
                      <X size={16} />
                    </button>
                  )}

                  {loading ? (
                    <button
                      onClick={stop}
                      className="flex h-11 w-11 items-center justify-center rounded-xl border border-red-400/20 bg-red-500/10 text-red-300"
                      title="Stop generation"
                    >
                      <StopCircle
                        size={18}
                      />
                    </button>
                  ) : (
                    <button
                      onClick={() =>
                        send()
                      }
                      disabled={
                        !input.trim() ||
                        !online
                      }
                      className="flex h-11 w-11 items-center justify-center rounded-xl bg-white text-slate-950 transition hover:bg-slate-200 disabled:bg-white/[.07] disabled:text-slate-600"
                      title="Send"
                    >
                      <Send size={17} />
                    </button>
                  )}
                </div>
              </div>

              {/* COMPOSER FOOTER */}
              <div className="flex items-center justify-between border-t border-white/[.05] px-3 pt-2 text-[10px] text-slate-700">
                <span className="flex items-center gap-2">
                  <span>
                    Enter to send
                  </span>

                  <span className="hidden sm:inline">
                    •
                  </span>

                  <span className="hidden sm:inline">
                    Shift + Enter for a
                    new line
                  </span>

                  {draftSaved && (
                    <span className="text-emerald-500/60">
                      • Draft saved
                    </span>
                  )}
                </span>

                <span
                  className={
                    input.length >
                    MAX_INPUT * 0.9
                      ? "text-amber-500"
                      : ""
                  }
                >
                  {input.length.toLocaleString()}{" "}
                  /{" "}
                  {MAX_INPUT.toLocaleString()}
                </span>
              </div>
            </div>

            <div className="mt-2 flex items-center justify-center gap-2 text-[9px] text-slate-700">
              <Bot size={10} />
              Nova can make mistakes. Check
              important information.
            </div>
          </div>
        </div>
      </section>

      {/* ===================================================
          COPY TOAST
          =================================================== */}

      {copied && (
        <div className="fixed bottom-28 left-1/2 z-[250] flex -translate-x-1/2 items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-500/10 px-4 py-2.5 text-xs text-emerald-300">
          <CheckCircle2 size={14} />
          Copied to clipboard
        </div>
      )}

      {/* ===================================================
          DELETE MODAL
          =================================================== */}

      {deleteItem && (
        <div className="fixed inset-0 z-[500] flex items-center justify-center bg-black/65 p-4 backdrop-blur-md">
          <div className="w-full max-w-md rounded-3xl border border-white/10 bg-[#0b0e15] p-6 shadow-2xl">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-red-400/15 bg-red-500/10 text-red-300">
              <Trash2 size={18} />
            </div>

            <h2 className="mt-5 text-lg font-semibold">
              Delete conversation?
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              This will permanently
              remove{" "}
              <span className="text-slate-300">
                {deleteItem.title ||
                  "this conversation"}
              </span>
              .
            </p>

            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={() =>
                  setDeleteItem(
                    null
                  )
                }
                className="rounded-xl border border-white/[.07] px-4 py-2.5 text-xs text-slate-400 hover:bg-white/[.04]"
              >
                Cancel
              </button>

              <button
                onClick={() =>
                  deleteConversation(
                    deleteItem.id
                  )
                }
                className="rounded-xl bg-red-500 px-4 py-2.5 text-xs font-semibold text-white hover:bg-red-400"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ===================================================
          STYLES
          =================================================== */}

      <style>
        {`
          .nova-action {
            display: inline-flex;
            align-items: center;
            gap: .375rem;
            border-radius: .5rem;
            padding: .375rem .5rem;
            font-size: .75rem;
            color: #64748b;
            transition: background .15s ease, color .15s ease;
          }

          .nova-action:hover {
            background: rgba(255,255,255,.06);
            color: #e2e8f0;
          }

          .nova-scrollbar::-webkit-scrollbar {
            width: 7px;
          }

          .nova-scrollbar::-webkit-scrollbar-track {
            background: transparent;
          }

          .nova-scrollbar::-webkit-scrollbar-thumb {
            background: rgba(148,163,184,.16);
            border-radius: 999px;
            border: 2px solid transparent;
            background-clip: padding-box;
          }

          .nova-markdown > :first-child {
            margin-top: 0;
          }

          .nova-markdown > :last-child {
            margin-bottom: 0;
          }

          .nova-markdown p {
            margin: .7rem 0;
          }

          .nova-markdown h1,
          .nova-markdown h2,
          .nova-markdown h3 {
            margin: 1.2rem 0 .6rem;
            font-weight: 650;
            color: #f1f5f9;
          }

          .nova-markdown strong {
            color: #f1f5f9;
          }

          .nova-markdown hr {
            margin: 1.2rem 0;
            border-color: rgba(255,255,255,.08);
          }

          .nova-markdown pre {
            max-width: 100%;
            overflow-x: auto;
          }

          .nova-markdown img {
            max-width: 100%;
            border-radius: 12px;
          }

          .nova-markdown input[type="checkbox"] {
            margin-right: .5rem;
          }

          @media(max-width:640px) {
            .nova-chat-shell {
              min-height: 100svh;
            }
          }

          @media(prefers-reduced-motion:reduce) {
            *,
            *::before,
            *::after {
              animation-duration: .01ms !important;
              transition-duration: .01ms !important;
              scroll-behavior: auto !important;
            }
          }
        `}
      </style>
    </div>
  );
}
import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState
} from "react";

import {
    useNavigate
} from "react-router-dom";

import {
    Activity,
    AlertCircle,
    AlertTriangle,
    ArrowLeft,
    ArrowRight,
    Award,
    BarChart3,
    Brain,
    BookOpen,
    CheckCircle2,
    ChevronDown,
    ChevronRight,
    Clock3,
    Database,
    Flame,
    Gauge,
    GraduationCap,
    Info,
    Layers3,
    MessageSquare,
    Network,
    RefreshCw,
    Search,
    Sparkles,
    Target,
    TrendingDown,
    TrendingUp,
    Trophy,
    X,
    XCircle
} from "lucide-react";


const API_URL =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";

const REQUEST_TIMEOUT = 12000;
const AUTO_REFRESH_INTERVAL = 60000;
const MAX_CONVERSATIONS = 50;

function safeNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
}

function safeString(value, fallback = "") {
    if (typeof value === "string" && value.trim()) {
        return value;
    }
    return fallback;
}

function readStoredUser() {
    try {
        const raw = localStorage.getItem("nova_user");
        if (!raw) return null;
        return JSON.parse(raw);
    } catch {
        return null;
    }
}

function normalizeDashboard(raw) {
    const source = raw && typeof raw === "object" ? raw : {};
    const stats = source.stats || source.statistics || {};
    const recent = Array.isArray(source.recent_conversations)
        ? source.recent_conversations
        : Array.isArray(source.conversations)
            ? source.conversations.slice(0, MAX_CONVERSATIONS)
            : [];

    return {
        ...source,
        stats: {
            questions: safeNumber(stats.questions ?? source.questions),
            sessions: safeNumber(stats.sessions ?? source.sessions),
            study_time: safeNumber(stats.study_time ?? source.study_time),
            streak: safeNumber(stats.streak ?? source.streak),
            ...stats
        },
        recent_conversations: recent
    };
}

async function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
        return await fetch(url, {
            ...options,
            signal: options.signal || controller.signal,
            credentials: "include"
        });
    } finally {
        clearTimeout(timeoutId);
    }
}

function ActionButton({ action, onClick, children, disabled = false }) {
    return (
        <button
            type="button"
            className={`nova-action-button nova-action-${action}`}
            onClick={onClick}
            disabled={disabled}
        >
            {children}
        </button>
    );
}

export default function Dashboard() {
    const navigate = useNavigate();
    const mountedRef = useRef(true);
    const abortRef = useRef(null);
    const loadRequestId = useRef(0);

    const [dashboard, setDashboard] = useState(null);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState(null);
    const [apiOnline, setApiOnline] = useState(false);
    const [lastUpdated, setLastUpdated] = useState(null);

    useEffect(() => () => {
        mountedRef.current = false;
        abortRef.current?.abort();
    }, []);

    useEffect(() => {
        const syncUser = () => setUser(readStoredUser());
        syncUser();
        window.addEventListener("storage", syncUser);
        window.addEventListener("nova-auth-changed", syncUser);
        return () => {
            window.removeEventListener("storage", syncUser);
            window.removeEventListener("nova-auth-changed", syncUser);
        };
    }, []);

    const loadDashboard = useCallback(async (options = {}) => {
        const { silent = false, retry = true } = options;
        const currentUser = readStoredUser();

        if (!currentUser?.email) {
            if (mountedRef.current) setLoading(false);
            navigate("/login", { replace: true });
            return;
        }

        abortRef.current?.abort();
        const controller = new AbortController();
        abortRef.current = controller;
        const requestId = ++loadRequestId.current;

        if (mountedRef.current) {
            if (silent) setRefreshing(true);
            else setLoading(true);
            setError(null);
        }

        const endpoint = `${API_URL}/dashboard?email=${encodeURIComponent(currentUser.email)}`;

        try {
            const response = await fetchWithTimeout(endpoint, { signal: controller.signal });

            if (!response.ok) {
                let serverMessage = "";
                try {
                    const body = await response.json();
                    serverMessage = safeString(body?.detail || body?.message || body?.error);
                } catch {
                    // Response might not be JSON.
                }
                throw new Error(serverMessage || `Dashboard request failed with HTTP ${response.status}.`);
            }

            const raw = await response.json();
            if (!mountedRef.current || requestId !== loadRequestId.current) return;

            setDashboard(normalizeDashboard(raw));
            setUser(currentUser);
            setApiOnline(true);
            setLastUpdated(new Date());
            setError(null);
        } catch (err) {
            if (err?.name === "AbortError") return;
            console.error("Nova Dashboard:", err);

            if (retry && !controller.signal.aborted) {
                await new Promise(resolve => setTimeout(resolve, 700));
                if (!controller.signal.aborted && mountedRef.current) {
                    return loadDashboard({ silent: true, retry: false });
                }
            }

            if (mountedRef.current) {
                setApiOnline(false);
                setError(safeString(err?.message, "Unable to load the dashboard."));
            }
        } finally {
            if (mountedRef.current) {
                setLoading(false);
                setRefreshing(false);
            }
        }
    }, [navigate]);

    useEffect(() => {
        loadDashboard();
        const interval = setInterval(() => loadDashboard({ silent: true }), AUTO_REFRESH_INTERVAL);
        return () => clearInterval(interval);
    }, [loadDashboard]);

    const stats = dashboard?.stats || {};
    const conversations = dashboard?.recent_conversations || [];
    const subjects = dashboard?.subjects || [];

    const statCards = useMemo(() => [
        { label: "Questions", value: safeNumber(stats.questions), icon: MessageSquare },
        { label: "Sessions", value: safeNumber(stats.sessions), icon: Activity },
        { label: "Study time", value: safeNumber(stats.study_time), icon: Clock3 },
        { label: "Streak", value: safeNumber(stats.streak), icon: Flame }
    ], [stats.questions, stats.sessions, stats.study_time, stats.streak]);

    const startLearning = () => navigate("/chat");
    const openDemo = () => navigate("/demo");
    const continueLearning = () => navigate("/chat");
    const startFresh = () => navigate("/chat");

    if (loading && !dashboard) {
        return (
            <main className="dashboard-page dashboard-loading">
                <div className="dashboard-spinner" aria-label="Loading dashboard" />
                <p>Loading Nova…</p>
            </main>
        );
    }

    return (
        <main className="dashboard-page">
            <header className="dashboard-header">
                <div>
                    <p className="dashboard-eyebrow">Nova workspace</p>
                    <h1>Welcome back{user?.name ? `, ${user.name}` : ""}.</h1>
                    <p>Keep learning, review your progress, and pick up where you left off.</p>
                </div>
                <div className="dashboard-status" aria-live="polite">
                    <span className={apiOnline ? "status-dot online" : "status-dot"} />
                    {apiOnline ? "Nova online" : "Nova offline"}
                    <button type="button" onClick={() => loadDashboard({ silent: true })} disabled={refreshing}>
                        <RefreshCw size={16} className={refreshing ? "spin" : ""} />
                        Refresh
                    </button>
                </div>
            </header>

            {error && (
                <section className="dashboard-error" role="alert">
                    <AlertCircle size={20} />
                    <div>
                        <strong>Dashboard unavailable</strong>
                        <p>{error}</p>
                    </div>
                    <button type="button" onClick={() => loadDashboard()}>Retry</button>
                </section>
            )}

            <section className="dashboard-stats" aria-label="Learning statistics">
                {statCards.map(({ label, value, icon: Icon }) => (
                    <article className="dashboard-stat" key={label}>
                        <Icon size={20} />
                        <span>{label}</span>
                        <strong>{value}</strong>
                    </article>
                ))}
            </section>

            <section className="dashboard-actions">
                <ActionButton action="start" onClick={startLearning}>
                    <Brain size={20} /> Start learning
                </ActionButton>
                <ActionButton action="continue" onClick={continueLearning}>
                    <TrendingUp size={20} /> Continue learning
                </ActionButton>
                <ActionButton action="demo" onClick={openDemo}>
                    <Sparkles size={20} /> Try demo
                </ActionButton>
                <ActionButton action="new" onClick={startFresh}>
                    <BookOpen size={20} /> New session
                </ActionButton>
            </section>

            <section className="dashboard-grid">
                <article className="dashboard-card dashboard-progress">
                    <div className="card-heading">
                        <div><Gauge size={20} /><h2>Progress</h2></div>
                        <span>{lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : ""}</span>
                    </div>
                    <div className="progress-summary">
                        <strong>{safeNumber(stats.progress ?? dashboard?.progress)}%</strong>
                        <p>Overall learning progress</p>
                    </div>
                    <div className="progress-bar"><span style={{ width: `${Math.min(100, Math.max(0, safeNumber(stats.progress ?? dashboard?.progress)))}%` }} /></div>
                </article>

                <article className="dashboard-card">
                    <div className="card-heading"><div><GraduationCap size={20} /><h2>Subjects</h2></div></div>
                    {subjects.length ? (
                        <ul className="dashboard-list">
                            {subjects.slice(0, 6).map((subject, index) => (
                                <li key={subject.id || subject.name || index}>
                                    <span>{safeString(subject.name || subject.subject, "Subject")}</span>
                                    <strong>{safeNumber(subject.progress)}%</strong>
                                </li>
                            ))}
                        </ul>
                    ) : <p className="empty-state">Your subject progress will appear here as you learn.</p>}
                </article>

                <article className="dashboard-card dashboard-wide">
                    <div className="card-heading"><div><MessageSquare size={20} /><h2>Recent conversations</h2></div></div>
                    {conversations.length ? (
                        <ul className="dashboard-conversations">
                            {conversations.slice(0, MAX_CONVERSATIONS).map((conversation, index) => (
                                <li key={conversation.id || conversation.conversation_id || index}>
                                    <div><strong>{safeString(conversation.title || conversation.subject, "Conversation")}</strong><span>{safeString(conversation.preview || conversation.last_message, "Continue your conversation with Nova")}</span></div>
                                    <ChevronRight size={18} />
                                </li>
                            ))}
                        </ul>
                    ) : <p className="empty-state">No recent conversations yet. Start a session with Nova.</p>}
                </article>
            </section>

            <footer className="dashboard-footer">
                <span><Database size={16} /> Your learning data stays associated with your Nova account.</span>
                <span><Info size={16} /> Nova adapts as you learn.</span>
            </footer>
        </main>
    );
}

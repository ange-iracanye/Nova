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
    Check,
    CheckCircle2,
    ChevronDown,
    ChevronRight,
    CircleDot,
    Clock3,
    Database,
    Flame,
    Gauge,
    GraduationCap,
    Info,
    Layers3,
    LineChart,
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
    XCircle,
    Zap
} from "lucide-react";


// ============================================================
// CONFIGURATION
// ============================================================

const API_URL =
    "http://127.0.0.1:8000";

const REQUEST_TIMEOUT =
    12000;

const AUTO_REFRESH_INTERVAL =
    60000;

const MAX_CONVERSATIONS =
    50;


// ============================================================
// SAFE HELPERS
// ============================================================

function safeNumber(
    value,
    fallback = 0
) {

    const number =
        Number(value);

    if (
        !Number.isFinite(number)
    ) {

        return fallback;

    }

    return number;
}


function safeInteger(
    value,
    fallback = 0
) {

    const number =
        safeNumber(
            value,
            fallback
        );

    return Math.max(
        0,
        Math.round(number)
    );

}


function clamp(
    value,
    min = 0,
    max = 100
) {

    return Math.min(
        max,
        Math.max(
            min,
            safeNumber(value)
        )
    );

}


function safeString(
    value,
    fallback = ""
) {

    if (
        value === null ||
        value === undefined
    ) {

        return fallback;

    }

    const result =
        String(value).trim();

    return result ||
        fallback;

}


function formatNumber(
    value
) {

    return safeInteger(
        value
    ).toLocaleString(
        "en-US"
    );

}


function formatPercent(
    value
) {

    return `${Math.round(
        clamp(value)
    )}%`;

}


function formatDate(
    value
) {

    if (!value) {

        return "Unknown";

    }

    const date =
        new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return "Unknown";

    }

    return date.toLocaleString(
        undefined,
        {
            dateStyle: "medium",
            timeStyle: "short"
        }
    );

}


function formatRelativeTime(
    value
) {

    if (!value) {

        return "No recent activity";

    }

    const date =
        new Date(value);

    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return "Recently";

    }

    const difference =
        Date.now() -
        date.getTime();

    const seconds =
        Math.floor(
            difference / 1000
        );

    if (seconds < 30) {

        return "Just now";

    }

    if (seconds < 60) {

        return `${seconds}s ago`;

    }

    const minutes =
        Math.floor(
            seconds / 60
        );

    if (minutes < 60) {

        return `${minutes}m ago`;

    }

    const hours =
        Math.floor(
            minutes / 60
        );

    if (hours < 24) {

        return `${hours}h ago`;

    }

    const days =
        Math.floor(
            hours / 24
        );

    if (days < 7) {

        return `${days}d ago`;

    }

    return formatDate(
        value
    );

}


function getInitials(
    value
) {

    const text =
        safeString(
            value,
            "N"
        );

    const parts =
        text
            .split(
                /[\s@._-]+/
            )
            .filter(Boolean);

    if (
        parts.length >= 2
    ) {

        return (
            parts[0][0] +
            parts[1][0]
        ).toUpperCase();

    }

    return text
        .slice(0, 2)
        .toUpperCase();

}


function getMasteryLabel(
    value
) {

    const mastery =
        clamp(value);

    if (
        mastery >= 90
    ) {

        return "Excellent";

    }

    if (
        mastery >= 75
    ) {

        return "Strong";

    }

    if (
        mastery >= 50
    ) {

        return "Developing";

    }

    if (
        mastery >= 25
    ) {

        return "Needs practice";

    }

    return "Getting started";

}


function getMasteryTone(
    value
) {

    const mastery =
        clamp(value);

    if (
        mastery >= 75
    ) {

        return "success";

    }

    if (
        mastery >= 50
    ) {

        return "info";

    }

    if (
        mastery >= 25
    ) {

        return "warning";

    }

    return "danger";

}


// ============================================================
// SAFE LOCAL STORAGE
// ============================================================

function readStoredUser() {

    try {

        const raw =
            localStorage.getItem(
                "nova_user"
            );

        if (!raw) {

            return null;

        }

        const parsed =
            JSON.parse(raw);

        if (
            !parsed ||
            typeof parsed !== "object"
        ) {

            return null;

        }

        return parsed;

    } catch {

        return null;

    }

}


function readLastRoute() {

    try {

        return localStorage.getItem(
            "nova_last_route"
        );

    } catch {

        return null;

    }

}


function saveCurrentConversation(
    id
) {

    try {

        if (
            id !== undefined &&
            id !== null
        ) {

            localStorage.setItem(
                "nova_current_conversation",
                String(id)
            );

        }

    } catch {

        // Storage can fail in restricted environments.
        // The dashboard should not crash because humanity invented private browsing.
    }

}


// ============================================================
// API REQUEST
// ============================================================

async function fetchWithTimeout(
    url,
    options = {},
    timeout = REQUEST_TIMEOUT
) {

    const controller =
        new AbortController();

    const externalSignal =
        options.signal;

    let externalAbortHandler =
        null;

    if (externalSignal) {

        externalAbortHandler =
            () => controller.abort();

        if (
            externalSignal.aborted
        ) {

            controller.abort();

        } else {

            externalSignal.addEventListener(
                "abort",
                externalAbortHandler,
                {
                    once: true
                }
            );

        }

    }

    const timeoutId =
        setTimeout(
            () => {
                controller.abort();
            },
            timeout
        );

    try {

        const response =
            await fetch(
                url,
                {
                    ...options,
                    signal:
                        controller.signal,
                    headers: {
                        Accept:
                            "application/json",
                        ...(options.headers || {})
                    }
                }
            );

        return response;

    } catch (error) {

        if (
            error?.name ===
            "AbortError"
        ) {

            throw error;

        }

        throw new Error(
            "Unable to connect to the Nova backend."
        );

    } finally {

        clearTimeout(
            timeoutId
        );

        if (
            externalSignal &&
            externalAbortHandler
        ) {

            externalSignal.removeEventListener(
                "abort",
                externalAbortHandler
            );

        }

    }

}


// ============================================================
// NORMALIZE API DATA
// ============================================================

function normalizeSubjects(
    subjects
) {

    if (
        !subjects ||
        typeof subjects !== "object"
    ) {

        return {};

    }

    const normalized = {};

    Object.entries(
        subjects
    ).forEach(
        ([name, raw]) => {

            const data =
                raw &&
                typeof raw === "object"
                    ? raw
                    : {};

            normalized[name] = {

                mastery:
                    clamp(
                        data.mastery
                    ),

                topics_count:
                    safeInteger(
                        data.topics_count
                    ),

                correct_answers:
                    safeInteger(
                        data.correct_answers
                    ),

                wrong_answers:
                    safeInteger(
                        data.wrong_answers
                    ),

                attempts:
                    safeInteger(
                        data.attempts
                    ),

                questions:
                    safeInteger(
                        data.questions
                    ),

                confidence:
                    clamp(
                        data.confidence
                    )

            };

        }
    );

    return normalized;

}


function normalizeKnowledgeSubjects(
    subjects
) {

    if (
        !Array.isArray(
            subjects
        )
    ) {

        return [];

    }

    return subjects
        .filter(Boolean)
        .map(
            (
                item,
                index
            ) => {

                const object =
                    typeof item === "object"
                        ? item
                        : {};

                return {

                    id:
                        safeString(
                            object.id,
                            `knowledge-${index}`
                        ),

                    name:
                        safeString(
                            object.name,
                            "Unknown subject"
                        ),

                    confidence:
                        clamp(
                            object.confidence
                        ),

                    topics:
                        safeInteger(
                            object.topics
                        ),

                    attempts:
                        safeInteger(
                            object.attempts
                        )

                };

            }
        );

}


function normalizeConversations(
    conversations
) {

    if (
        !Array.isArray(
            conversations
        )
    ) {

        return [];

    }

    return conversations
        .slice(
            0,
            MAX_CONVERSATIONS
        )
        .filter(Boolean)
        .map(
            (
                item,
                index
            ) => {

                const object =
                    typeof item === "object"
                        ? item
                        : {};

                return {

                    id:
                        object.id ??
                        `conversation-${index}`,

                    title:
                        safeString(
                            object.title,
                            "New conversation"
                        ),

                    last_message:
                        safeString(
                            object.last_message,
                            "No messages yet"
                        ),

                    message_count:
                        safeInteger(
                            object.message_count
                        ),

                    updated_at:
                        object.updated_at ||
                        object.updatedAt ||
                        object.created_at ||
                        null

                };

            }
        );

}


function normalizeDashboard(
    raw
) {

    const source =
        raw &&
        typeof raw === "object"
            ? raw
            : {};

    const rawStats =
        source.stats &&
        typeof source.stats === "object"
            ? source.stats
            : {};

    const rawDifficulty =
        source.difficulty &&
        typeof source.difficulty === "object"
            ? source.difficulty
            : {};

    const rawSession =
        source.session &&
        typeof source.session === "object"
            ? source.session
            : {};

    const normalized = {

        ...source,

        stats: {

            questions:
                safeInteger(
                    rawStats.questions
                ),

            total_subjects:
                safeInteger(
                    rawStats.total_subjects
                ),

            total_topics:
                safeInteger(
                    rawStats.total_topics
                ),

            overall_mastery:
                clamp(
                    rawStats.overall_mastery
                ),

            correct_answers:
                safeInteger(
                    rawStats.correct_answers
                ),

            wrong_answers:
                safeInteger(
                    rawStats.wrong_answers
                ),

            study_attempts:
                safeInteger(
                    rawStats.study_attempts
                ),

            average_confidence:
                clamp(
                    rawStats.average_confidence
                ),

            understanding_attempts:
                safeInteger(
                    rawStats.understanding_attempts
                ),

            memory_count:
                safeInteger(
                    rawStats.memory_count
                ),

            conversation_count:
                safeInteger(
                    rawStats.conversation_count
                )

        },

        subjects:
            normalizeSubjects(
                source.subjects
            ),

        knowledge_subjects:
            normalizeKnowledgeSubjects(
                source.knowledge_subjects
            ),

        strengths:
            Array.isArray(
                source.strengths
            )
                ? source.strengths
                    .map(
                        item =>
                            safeString(
                                item
                            )
                    )
                    .filter(Boolean)
                : [],

        weaknesses:
            Array.isArray(
                source.weaknesses
            )
                ? source.weaknesses
                    .map(
                        item =>
                            safeString(
                                item
                            )
                    )
                    .filter(Boolean)
                : [],

        difficulty: {

            easy:
                safeInteger(
                    rawDifficulty.easy
                ),

            medium:
                safeInteger(
                    rawDifficulty.medium
                ),

            hard:
                safeInteger(
                    rawDifficulty.hard
                )

        },

        session: {

            subject:
                safeString(
                    rawSession.subject,
                    "None"
                ),

            topic:
                safeString(
                    rawSession.topic,
                    "None"
                ),

            mode:
                safeString(
                    rawSession.mode,
                    "None"
                ),

            score:
                rawSession.score ??
                0

        },

        recent_conversations:
            normalizeConversations(
                source.recent_conversations
            )

    };

    return normalized;

}


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function Dashboard() {

    const navigate =
        useNavigate();


    const [
        dashboard,
        setDashboard
    ] = useState(null);


    const [
        loading,
        setLoading
    ] = useState(true);


    const [
        refreshing,
        setRefreshing
    ] = useState(false);


    const [
        error,
        setError
    ] = useState(null);


    const [
        user,
        setUser
    ] = useState(
        readStoredUser()
    );


    const [
        apiOnline,
        setApiOnline
    ] = useState(
        null
    );


    const [
        lastUpdated,
        setLastUpdated
    ] = useState(
        null
    );


    const [
        searchQuery,
        setSearchQuery
    ] = useState("");


    const [
        conversationSort,
        setConversationSort
    ] = useState(
        "recent"
    );


    const [
        showAllConversations,
        setShowAllConversations
    ] = useState(
        false
    );


    const [
        selectedSubject,
        setSelectedSubject
    ] = useState(null);


    const abortRef =
        useRef(null);


    const mountedRef =
        useRef(true);


    const loadRequestId =
        useRef(0);


    // ========================================================
    // MOUNT / UNMOUNT
    // ========================================================

    useEffect(() => {

        mountedRef.current =
            true;

        return () => {

            mountedRef.current =
                false;

            if (
                abortRef.current
            ) {

                abortRef.current.abort();

            }

        };

    }, []);


    // ========================================================
    // SYNC USER
    // ========================================================

    useEffect(() => {

        function syncUser() {

            setUser(
                readStoredUser()
            );

        }

        syncUser();

        window.addEventListener(
            "storage",
            syncUser
        );

        window.addEventListener(
            "nova-auth-changed",
            syncUser
        );

        return () => {

            window.removeEventListener(
                "storage",
                syncUser
            );

            window.removeEventListener(
                "nova-auth-changed",
                syncUser
            );

        };

    }, []);


    // ========================================================
    // LOAD DASHBOARD
    // ========================================================

    const loadDashboard =
        useCallback(
            async (
                options = {}
            ) => {

                const {
                    silent = false,
                    retry = true
                } = options;


                const currentUser =
                    readStoredUser();


                if (
                    !currentUser?.email
                ) {

                    if (
                        mountedRef.current
                    ) {

                        setLoading(false);

                    }

                    navigate(
                        "/login",
                        {
                            replace: true
                        }
                    );

                    return;

                }


                if (
                    abortRef.current
                ) {

                    abortRef.current.abort();

                }


                const controller =
                    new AbortController();

                abortRef.current =
                    controller;


                const requestId =
                    ++loadRequestId.current;


                if (
                    mountedRef.current
                ) {

                    if (silent) {

                        setRefreshing(
                            true
                        );

                    } else {

                        setLoading(
                            true
                        );

                    }

                    setError(
                        null
                    );

                }


                const endpoint =
                    `${API_URL}/dashboard?email=${encodeURIComponent(
                        currentUser.email
                    )}`;


                try {

                    const response =
                        await fetchWithTimeout(
                            endpoint,
                            {
                                signal:
                                    controller.signal
                            }
                        );


                    if (
                        !response.ok
                    ) {

                        let serverMessage =
                            "";

                        try {

                            const body =
                                await response.json();

                            serverMessage =
                                safeString(
                                    body?.detail ||
                                    body?.message ||
                                    body?.error
                                );

                        } catch {

                            // Response might not be JSON.
                        }


                        throw new Error(
                            serverMessage ||
                            `Dashboard request failed with HTTP ${response.status}.`
                        );

                    }


                    const raw =
                        await response.json();


                    if (
                        !mountedRef.current ||
                        requestId !==
                            loadRequestId.current
                    ) {

                        return;

                    }


                    const normalized =
                        normalizeDashboard(
                            raw
                        );


                    setDashboard(
                        normalized
                    );

                    setUser(
                        currentUser
                    );

                    setApiOnline(
                        true
                    );

                    setLastUpdated(
                        new Date()
                    );

                    setError(
                        null
                    );


                } catch (err) {

                    if (
                        err?.name ===
                        "AbortError"
                    ) {

                        return;

                    }


                    console.error(
                        "Nova Dashboard:",
                        err
                    );


                    if (
                        retry
                    ) {

                        try {

                            await new Promise(
                                resolve =>
                                    setTimeout(
                                        resolve,
                                        700
                                    )
                            );


                            if (
                                !controller.signal.aborted
                            ) {

                                return loadDashboard(
                                    {
                                        silent: true,
                                        retry: false
                                    }
                                );

                            }

                        } catch {

                            // Retry failure handled below.
                        }

                    }


                    if (
                        mountedRef.current
                    ) {

                        setApiOnline(
                            false
                        );

                        setError(
                            safeString(
                                err?.message,
                                "Unable to load the dashboard."
                            )
                        );

                    }

                } finally {

                    if (
                        mountedRef.current
                    ) {

                        setLoading(
                            false
                        );

                        setRefreshing(
                            false
                        );

                    }

                }

            },
            [
                navigate
            ]
        );


    // ========================================================
    // INITIAL LOAD
    // ========================================================

    useEffect(() => {

        loadDashboard();

    }, [
        loadDashboard
    ]);


    // ========================================================
    // AUTO REFRESH
    // ========================================================

    useEffect(() => {

        const interval =
            window.setInterval(
                () => {

                    if (
                        document.visibilityState ===
                        "visible"
                    ) {

                        loadDashboard(
                            {
                                silent: true,
                                retry: false
                            }
                        );

                    }

                },
                AUTO_REFRESH_INTERVAL
            );


        return () => {

            window.clearInterval(
                interval
            );

        };

    }, [
        loadDashboard
    ]);


    // ========================================================
    // KEYBOARD SHORTCUTS
    // ========================================================

    useEffect(() => {

        function handleKeyDown(
            event
        ) {

            if (
                event.key === "/" &&
                !event.ctrlKey &&
                !event.metaKey &&
                !event.altKey
            ) {

                const target =
                    event.target;

                if (
                    target instanceof
                        HTMLInputElement ||
                    target instanceof
                        HTMLTextAreaElement
                ) {

                    return;

                }

                event.preventDefault();

                const input =
                    document.querySelector(
                        "[data-dashboard-search]"
                    );

                input?.focus();

            }

            if (
                event.key === "Escape"
            ) {

                setSearchQuery("");

            }

        }


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

    }, []);


    // ========================================================
    // DERIVED DATA
    // ========================================================

    const stats =
        dashboard?.stats || {};


    const subjects =
        dashboard?.subjects || {};


    const difficulty =
        dashboard?.difficulty || {};


    const session =
        dashboard?.session || {};


    const strengths =
        dashboard?.strengths || [];


    const weaknesses =
        dashboard?.weaknesses || [];


    const knowledgeSubjects =
        dashboard?.knowledge_subjects || [];


    const conversations =
        dashboard?.recent_conversations || [];


    const subjectEntries =
        useMemo(
            () =>
                Object.entries(
                    subjects
                ).sort(
                    (
                        [, a],
                        [, b]
                    ) =>
                        safeNumber(
                            b.mastery
                        ) -
                        safeNumber(
                            a.mastery
                        )
                ),
            [
                subjects
            ]
        );


    const totalDifficulty =
        safeInteger(
            difficulty.easy
        ) +
        safeInteger(
            difficulty.medium
        ) +
        safeInteger(
            difficulty.hard
        );


    const correctAnswers =
        safeInteger(
            stats.correct_answers
        );


    const wrongAnswers =
        safeInteger(
            stats.wrong_answers
        );


    const totalAnswers =
        correctAnswers +
        wrongAnswers;


    const accuracy =
        totalAnswers > 0
            ? (
                correctAnswers /
                totalAnswers
            ) * 100
            : 0;


    const mastery =
        clamp(
            stats.overall_mastery
        );


    const confidence =
        clamp(
            stats.average_confidence
        );


    const bestSubject =
        subjectEntries.length > 0
            ? subjectEntries[0]
            : null;


    const weakestSubject =
        subjectEntries.length > 0
            ? [...subjectEntries]
                .sort(
                    (
                        [, a],
                        [, b]
                    ) =>
                        safeNumber(
                            a.mastery
                        ) -
                        safeNumber(
                            b.mastery
                        )
                )[0]
            : null;


    const difficultyDistribution =
        useMemo(
            () => {

                if (
                    totalDifficulty <= 0
                ) {

                    return [];

                }

                return [

                    {
                        label: "Easy",
                        value:
                            difficulty.easy,
                        percentage:
                            (
                                difficulty.easy /
                                totalDifficulty
                            ) *
                            100
                    },

                    {
                        label: "Medium",
                        value:
                            difficulty.medium,
                        percentage:
                            (
                                difficulty.medium /
                                totalDifficulty
                            ) *
                            100
                    },

                    {
                        label: "Hard",
                        value:
                            difficulty.hard,
                        percentage:
                            (
                                difficulty.hard /
                                totalDifficulty
                            ) *
                            100
                    }

                ];

            },
            [
                difficulty,
                totalDifficulty
            ]
        );


    const filteredConversations =
        useMemo(
            () => {

                const query =
                    searchQuery
                        .trim()
                        .toLowerCase();


                let result =
                    conversations;


                if (query) {

                    result =
                        result.filter(
                            conversation =>
                                conversation.title
                                    .toLowerCase()
                                    .includes(query) ||
                                conversation.last_message
                                    .toLowerCase()
                                    .includes(query)
                        );

                }


                result =
                    [...result].sort(
                        (
                            a,
                            b
                        ) => {

                            if (
                                conversationSort ===
                                "messages"
                            ) {

                                return (
                                    b.message_count -
                                    a.message_count
                                );

                            }

                            if (
                                conversationSort ===
                                "title"
                            ) {

                                return a.title
                                    .localeCompare(
                                        b.title
                                    );

                            }


                            const dateA =
                                new Date(
                                    a.updated_at ||
                                    0
                                ).getTime();


                            const dateB =
                                new Date(
                                    b.updated_at ||
                                    0
                                ).getTime();


                            return (
                                dateB -
                                dateA
                            );

                        }
                    );


                return showAllConversations
                    ? result
                    : result.slice(
                        0,
                        5
                    );

            },
            [
                conversations,
                searchQuery,
                conversationSort,
                showAllConversations
            ]
        );


    // ========================================================
    // NAVIGATION
    // ========================================================

    function openChat() {

        navigate(
            "/chat"
        );

    }


    function openNewChat() {

        navigate(
            "/chat?new=true"
        );

    }


    function openSettings() {

        navigate(
            "/settings"
        );

    }


    function continueLearning() {

        const lastRoute =
            readLastRoute();


        if (
            lastRoute &&
            lastRoute !== "/" &&
            lastRoute !== "/dashboard"
        ) {

            navigate(
                lastRoute
            );

            return;

        }

        openChat();

    }


    function openConversation(
        id
    ) {

        saveCurrentConversation(
            id
        );

        navigate(
            "/chat"
        );

    }


    // ========================================================
    // LOADING SCREEN
    // ========================================================

    if (
        loading &&
        !dashboard
    ) {

        return (
            <DashboardLoading />

        );

    }


    // ========================================================
    // ERROR SCREEN
    // ========================================================

    if (
        error &&
        !dashboard
    ) {

        return (

            <DashboardError
                error={error}
                onRetry={() =>
                    loadDashboard()
                }
                onHome={() =>
                    navigate("/")
                }
            />

        );

    }


    // ========================================================
    // EMPTY / NULL
    // ========================================================

    if (
        !dashboard
    ) {

        return (
            <DashboardError
                error="No dashboard data was returned by Nova."
                onRetry={() =>
                    loadDashboard()
                }
                onHome={() =>
                    navigate("/")
                }
            />
        );

    }


    // ========================================================
    // MAIN UI
    // ========================================================

    return (

        <div
            className="
                min-h-screen
                bg-[#070b12]
                text-white
                selection:bg-blue-500/30
            "
        >

            {/* ==================================================
                AMBIENT BACKGROUND
            ================================================== */}

            <div
                className="
                    fixed
                    inset-0
                    pointer-events-none
                    overflow-hidden
                "
                aria-hidden="true"
            >

                <div
                    className="
                        absolute
                        -top-40
                        left-1/3
                        w-[500px]
                        h-[500px]
                        rounded-full
                        bg-blue-600/5
                        blur-[140px]
                    "
                />

                <div
                    className="
                        absolute
                        top-1/2
                        -right-40
                        w-[420px]
                        h-[420px]
                        rounded-full
                        bg-indigo-600/5
                        blur-[140px]
                    "
                />

            </div>


            {/* ==================================================
                HEADER
            ================================================== */}

            <header
                className="
                    sticky
                    top-0
                    z-50
                    h-16
                    border-b
                    border-white/[0.06]
                    bg-[#070b12]/80
                    backdrop-blur-2xl
                "
            >

                <div
                    className="
                        max-w-[1500px]
                        mx-auto
                        h-full
                        px-4
                        sm:px-6
                        lg:px-8
                        flex
                        items-center
                        justify-between
                        gap-4
                    "
                >

                    <button
                        onClick={() =>
                            navigate("/")
                        }
                        className="
                            group
                            flex
                            items-center
                            gap-2
                            text-slate-400
                            hover:text-white
                            transition
                        "
                        aria-label="Return home"
                    >

                        <div
                            className="
                                w-8
                                h-8
                                rounded-lg
                                border
                                border-white/[0.06]
                                bg-white/[0.03]
                                flex
                                items-center
                                justify-center
                                group-hover:bg-white/[0.06]
                                transition
                            "
                        >

                            <ArrowLeft
                                size={16}
                            />

                        </div>


                        <span
                            className="
                                hidden
                                sm:block
                                text-sm
                                font-medium
                            "
                        >
                            Home
                        </span>

                    </button>


                    <div
                        className="
                            flex
                            items-center
                            gap-3
                        "
                    >

                        <div
                            className="
                                w-9
                                h-9
                                rounded-xl
                                bg-blue-500/10
                                border
                                border-blue-500/20
                                flex
                                items-center
                                justify-center
                            "
                        >

                            <Brain
                                size={20}
                                className="
                                    text-blue-400
                                "
                            />

                        </div>


                        <div
                            className="
                                hidden
                                sm:block
                            "
                        >

                            <div
                                className="
                                    text-sm
                                    font-semibold
                                    leading-none
                                "
                            >
                                Nova Dashboard
                            </div>


                            <div
                                className="
                                    text-[11px]
                                    text-slate-500
                                    mt-1
                                "
                            >
                                Learning intelligence
                            </div>

                        </div>

                    </div>


                    <div
                        className="
                            flex
                            items-center
                            gap-2
                        "
                    >

                        {/* API STATUS */}

                        <div
                            className="
                                hidden
                                md:flex
                                items-center
                                gap-2
                                px-3
                                py-2
                                rounded-xl
                                border
                                border-white/[0.06]
                                bg-white/[0.02]
                            "
                        >

                            <span
                                className={`
                                    w-2
                                    h-2
                                    rounded-full
                                    ${
                                        apiOnline === true
                                            ? "bg-emerald-400"
                                            : apiOnline === false
                                                ? "bg-red-400"
                                                : "bg-slate-500"
                                    }
                                `}
                            />


                            <span
                                className="
                                    text-xs
                                    text-slate-500
                                "
                            >
                                {apiOnline === true
                                    ? "Backend online"
                                    : apiOnline === false
                                        ? "Backend offline"
                                        : "Checking backend"}
                            </span>

                        </div>


                        {/* REFRESH */}

                        <button
                            onClick={() =>
                                loadDashboard({
                                    silent: true
                                })
                            }
                            disabled={
                                refreshing
                            }
                            className="
                                flex
                                items-center
                                gap-2
                                px-3
                                py-2
                                rounded-xl
                                border
                                border-white/[0.06]
                                bg-white/[0.02]
                                text-slate-400
                                hover:text-white
                                hover:bg-white/[0.05]
                                disabled:opacity-50
                                transition
                            "
                            title="Refresh dashboard"
                        >

                            <RefreshCw
                                size={16}
                                className={
                                    refreshing
                                        ? "animate-spin"
                                        : ""
                                }
                            />


                            <span
                                className="
                                    hidden
                                    sm:block
                                    text-sm
                                "
                            >
                                Refresh
                            </span>

                        </button>

                    </div>

                </div>

            </header>


            {/* ==================================================
                MAIN
            ================================================== */}

            <main
                className="
                    relative
                    z-10
                    max-w-[1500px]
                    mx-auto
                    px-4
                    sm:px-6
                    lg:px-8
                    py-8
                "
            >

                {/* ==================================================
                    HERO
                ================================================== */}

                <section
                    className="
                        relative
                        overflow-hidden
                        rounded-3xl
                        border
                        border-white/[0.07]
                        bg-gradient-to-br
                        from-blue-500/[0.09]
                        via-white/[0.02]
                        to-transparent
                        p-6
                        sm:p-8
                        mb-6
                    "
                >

                    <div
                        className="
                            absolute
                            top-0
                            right-0
                            w-64
                            h-64
                            rounded-full
                            bg-blue-500/5
                            blur-3xl
                        "
                    />


                    <div
                        className="
                            relative
                            flex
                            flex-col
                            lg:flex-row
                            lg:items-center
                            justify-between
                            gap-8
                        "
                    >

                        <div>

                            <div
                                className="
                                    inline-flex
                                    items-center
                                    gap-2
                                    px-3
                                    py-1.5
                                    rounded-full
                                    bg-blue-500/10
                                    border
                                    border-blue-500/20
                                    text-blue-300
                                    text-xs
                                    font-medium
                                    mb-4
                                "
                            >

                                <Sparkles
                                    size={13}
                                />

                                LEARNING OVERVIEW

                            </div>


                            <h1
                                className="
                                    text-3xl
                                    sm:text-4xl
                                    lg:text-5xl
                                    font-bold
                                    tracking-tight
                                "
                            >

                                Welcome back,
                                {" "}

                                <span
                                    className="
                                        text-blue-400
                                    "
                                >
                                    {
                                        getInitials(
                                            user?.email
                                        )
                                    }
                                </span>

                            </h1>


                            <p
                                className="
                                    mt-3
                                    text-slate-400
                                    max-w-2xl
                                    leading-7
                                "
                            >
                                Nova is tracking your
                                progress, understanding,
                                strengths and areas that
                                still need work.
                            </p>


                            {lastUpdated && (

                                <div
                                    className="
                                        mt-4
                                        flex
                                        items-center
                                        gap-2
                                        text-xs
                                        text-slate-600
                                    "
                                >

                                    <Clock3
                                        size={13}
                                    />

                                    Updated
                                    {" "}
                                    {
                                        formatRelativeTime(
                                            lastUpdated
                                        )
                                    }

                                </div>

                            )}

                        </div>


                        <div
                            className="
                                flex
                                flex-col
                                sm:flex-row
                                lg:flex-col
                                xl:flex-row
                                gap-3
                                shrink-0
                            "
                        >

                            <button
                                onClick={
                                    continueLearning
                                }
                                className="
                                    group
                                    flex
                                    items-center
                                    justify-center
                                    gap-2
                                    px-5
                                    py-3
                                    rounded-xl
                                    bg-blue-600
                                    hover:bg-blue-500
                                    text-white
                                    font-semibold
                                    shadow-lg
                                    shadow-blue-950/30
                                    hover:-translate-y-0.5
                                    transition
                                "
                            >

                                Continue learning

                                <ArrowRight
                                    size={17}
                                    className="
                                        group-hover:translate-x-1
                                        transition
                                    "
                                />

                            </button>


                            <button
                                onClick={
                                    openNewChat
                                }
                                className="
                                    flex
                                    items-center
                                    justify-center
                                    gap-2
                                    px-5
                                    py-3
                                    rounded-xl
                                    border
                                    border-white/[0.08]
                                    bg-white/[0.03]
                                    hover:bg-white/[0.06]
                                    text-slate-200
                                    font-medium
                                    transition
                                "
                            >

                                <Sparkles
                                    size={17}
                                />

                                New session

                            </button>

                        </div>

                    </div>

                </section>


                {/* ==================================================
                    QUICK STATS
                ================================================== */}

                <section
                    className="
                        grid
                        grid-cols-2
                        xl:grid-cols-4
                        gap-3
                        sm:gap-4
                        mb-6
                    "
                >

                    <DashboardStat
                        icon={
                            <Target
                                size={19}
                            />
                        }
                        label="Overall mastery"
                        value={
                            formatPercent(
                                mastery
                            )
                        }
                        detail={
                            getMasteryLabel(
                                mastery
                            )
                        }
                        tone="blue"
                    />


                    <DashboardStat
                        icon={
                            <CheckCircle2
                                size={19}
                            />
                        }
                        label="Accuracy"
                        value={
                            formatPercent(
                                accuracy
                            )
                        }
                        detail={
                            `${formatNumber(
                                correctAnswers
                            )} correct answers`
                        }
                        tone="emerald"
                    />


                    <DashboardStat
                        icon={
                            <Brain
                                size={19}
                            />
                        }
                        label="Confidence"
                        value={
                            formatPercent(
                                confidence
                            )
                        }
                        detail={
                            `${formatNumber(
                                stats.understanding_attempts
                            )} checks`
                        }
                        tone="purple"
                    />


                    <DashboardStat
                        icon={
                            <MessageSquare
                                size={19}
                            />
                        }
                        label="Questions"
                        value={
                            formatNumber(
                                stats.questions
                            )
                        }
                        detail={
                            `${formatNumber(
                                stats.conversation_count
                            )} conversations`
                        }
                        tone="orange"
                    />

                </section>


                {/* ==================================================
                    MAIN ANALYTICS GRID
                ================================================== */}

                <section
                    className="
                        grid
                        xl:grid-cols-3
                        gap-6
                        mb-6
                    "
                >

                    {/* =================================================
                        MASTERY
                    ================================================= */}

                    <div
                        className="
                            xl:col-span-2
                            nova-card
                        "
                    >

                        <SectionHeader
                            icon={
                                <Gauge
                                    size={19}
                                />
                            }
                            iconClass="text-blue-400"
                            title="Learning performance"
                            subtitle="A high-level view of your current progress."
                        />


                        <div
                            className="
                                grid
                                md:grid-cols-[220px_1fr]
                                gap-8
                                items-center
                            "
                        >

                            <ProgressRing
                                value={
                                    mastery
                                }
                                label="Mastery"
                                size={190}
                            />


                            <div
                                className="
                                    space-y-5
                                "
                            >

                                <div>

                                    <div
                                        className="
                                            flex
                                            items-center
                                            justify-between
                                            mb-2
                                        "
                                    >

                                        <span
                                            className="
                                                text-sm
                                                text-slate-400
                                            "
                                        >
                                            Overall understanding
                                        </span>

                                        <span
                                            className="
                                                text-sm
                                                font-semibold
                                            "
                                        >
                                            {
                                                formatPercent(
                                                    mastery
                                                )
                                            }
                                        </span>

                                    </div>


                                    <ProgressBar
                                        value={
                                            mastery
                                        }
                                        tone="blue"
                                        height="h-3"
                                    />

                                </div>


                                <div
                                    className="
                                        grid
                                        grid-cols-2
                                        gap-3
                                    "
                                >

                                    <MetricBox
                                        icon={
                                            <CheckCircle2
                                                size={16}
                                            />
                                        }
                                        label="Correct"
                                        value={
                                            formatNumber(
                                                correctAnswers
                                            )
                                        }
                                    />


                                    <MetricBox
                                        icon={
                                            <XCircle
                                                size={16}
                                            />
                                        }
                                        label="Wrong"
                                        value={
                                            formatNumber(
                                                wrongAnswers
                                            )
                                        }
                                    />


                                    <MetricBox
                                        icon={
                                            <Activity
                                                size={16}
                                            />
                                        }
                                        label="Attempts"
                                        value={
                                            formatNumber(
                                                stats.study_attempts
                                            )
                                        }
                                    />


                                    <MetricBox
                                        icon={
                                            <Layers3
                                                size={16}
                                            />
                                        }
                                        label="Topics"
                                        value={
                                            formatNumber(
                                                stats.total_topics
                                            )
                                        }
                                    />

                                </div>


                                <div
                                    className="
                                        flex
                                        items-start
                                        gap-3
                                        p-4
                                        rounded-xl
                                        bg-white/[0.025]
                                        border
                                        border-white/[0.05]
                                    "
                                >

                                    <Info
                                        size={17}
                                        className="
                                            mt-0.5
                                            text-slate-500
                                            shrink-0
                                        "
                                    />

                                    <p
                                        className="
                                            text-xs
                                            text-slate-500
                                            leading-5
                                        "
                                    >
                                        Mastery is based on
                                        Nova's recorded learning
                                        data. It is an estimate,
                                        not an absolute measure
                                        of what you know.
                                    </p>

                                </div>

                            </div>

                        </div>

                    </div>


                    {/* =================================================
                        CONFIDENCE
                    ================================================= */}

                    <div
                        className="
                            nova-card
                        "
                    >

                        <SectionHeader
                            icon={
                                <Brain
                                    size={19}
                                />
                            }
                            iconClass="text-purple-400"
                            title="Understanding"
                            subtitle="Nova's current confidence estimate."
                        />


                        <div
                            className="
                                flex
                                justify-center
                                py-4
                            "
                        >

                            <ProgressRing
                                value={
                                    confidence
                                }
                                label="Confidence"
                                size={170}
                                tone="purple"
                            />

                        </div>


                        <div
                            className="
                                mt-4
                                grid
                                grid-cols-2
                                gap-3
                            "
                        >

                            <MetricBox
                                label="Checks"
                                value={
                                    formatNumber(
                                        stats.understanding_attempts
                                    )
                                }
                            />


                            <MetricBox
                                label="Memory"
                                value={
                                    formatNumber(
                                        stats.memory_count
                                    )
                                }
                            />

                        </div>


                        <button
                            onClick={
                                openChat
                            }
                            className="
                                mt-5
                                w-full
                                flex
                                items-center
                                justify-center
                                gap-2
                                px-4
                                py-3
                                rounded-xl
                                border
                                border-purple-500/20
                                bg-purple-500/5
                                text-purple-300
                                hover:bg-purple-500/10
                                transition
                                text-sm
                                font-medium
                            "
                        >

                            Practice with Nova

                            <ArrowRight
                                size={15}
                            />

                        </button>

                    </div>

                </section>


                {/* ==================================================
                    SUBJECTS + PERFORMANCE
                ================================================== */}

                <section
                    className="
                        grid
                        xl:grid-cols-3
                        gap-6
                        mb-6
                    "
                >

                    {/* =================================================
                        SUBJECTS
                    ================================================= */}

                    <div
                        className="
                            xl:col-span-2
                            nova-card
                        "
                    >

                        <SectionHeader
                            icon={
                                <BookOpen
                                    size={19}
                                />
                            }
                            iconClass="text-emerald-400"
                            title="Subjects"
                            subtitle="Your strongest and weakest areas at a glance."
                            action={
                                subjectEntries.length > 0
                                    ? `${subjectEntries.length} tracked`
                                    : null
                            }
                        />


                        {subjectEntries.length === 0 ? (

                            <EmptyState
                                icon={
                                    <BookOpen
                                        size={24}
                                    />
                                }
                                title="No subject data yet"
                                text="Start a learning session and Nova will begin building your subject profile."
                                action={
                                    <button
                                        onClick={
                                            openChat
                                        }
                                        className="
                                            px-4
                                            py-2.5
                                            rounded-xl
                                            bg-blue-600
                                            hover:bg-blue-500
                                            text-sm
                                            font-medium
                                            transition
                                        "
                                    >
                                        Start learning
                                    </button>
                                }
                            />

                        ) : (

                            <div
                                className="
                                    space-y-3
                                "
                            >

                                {subjectEntries
                                    .slice(
                                        0,
                                        8
                                    )
                                    .map(
                                        ([
                                            subject,
                                            data
                                        ]) => (

                                            <SubjectRow
                                                key={
                                                    subject
                                                }
                                                subject={
                                                    subject
                                                }
                                                data={
                                                    data
                                                }
                                                selected={
                                                    selectedSubject ===
                                                    subject
                                                }
                                                onClick={() =>
                                                    setSelectedSubject(
                                                        previous =>
                                                            previous ===
                                                            subject
                                                                ? null
                                                                : subject
                                                    )
                                                }
                                            />

                                        )
                                    )}

                            </div>

                        )}

                    </div>


                    {/* =================================================
                        BEST / WEAKEST
                    ================================================= */}

                    <div
                        className="
                            nova-card
                        "
                    >

                        <SectionHeader
                            icon={
                                <TrendingUp
                                    size={19}
                                />
                            }
                            iconClass="text-cyan-400"
                            title="Performance snapshot"
                            subtitle="Where your current data points."
                        />


                        {bestSubject ? (

                            <div
                                className="
                                    space-y-4
                                "
                            >

                                <PerformanceHighlight
                                    icon={
                                        <Trophy
                                            size={18}
                                        />
                                    }
                                    title="Strongest subject"
                                    name={
                                        bestSubject[0]
                                    }
                                    value={
                                        bestSubject[1].mastery
                                    }
                                    tone="emerald"
                                />


                                {weakestSubject && (

                                    <PerformanceHighlight
                                        icon={
                                            <TrendingDown
                                                size={18}
                                            />
                                        }
                                        title="Needs attention"
                                        name={
                                            weakestSubject[0]
                                        }
                                        value={
                                            weakestSubject[1].mastery
                                        }
                                        tone="orange"
                                    />

                                )}


                                <div
                                    className="
                                        pt-4
                                        border-t
                                        border-white/[0.06]
                                    "
                                >

                                    <p
                                        className="
                                            text-xs
                                            text-slate-600
                                            leading-5
                                        "
                                    >
                                        Nova can use these
                                        patterns to adapt future
                                        explanations and practice.
                                    </p>

                                </div>

                            </div>

                        ) : (

                            <EmptyState
                                icon={
                                    <BarChart3
                                        size={23}
                                    />
                                }
                                title="Not enough data"
                                text="More learning activity is needed before Nova can identify patterns."
                            />

                        )}

                    </div>

                </section>


                {/* ==================================================
                    STRENGTHS / WEAKNESSES
                ================================================== */}

                <section
                    className="
                        grid
                        lg:grid-cols-2
                        gap-6
                        mb-6
                    "
                >

                    <InsightCard
                        icon={
                            <Award
                                size={19}
                            />
                        }
                        title="Strengths"
                        subtitle="Areas where your performance is currently strongest."
                        items={
                            strengths
                        }
                        tone="emerald"
                        emptyText="Nova has not identified clear strengths yet."
                    />


                    <InsightCard
                        icon={
                            <AlertTriangle
                                size={19}
                            />
                        }
                        title="Needs attention"
                        subtitle="Topics where more practice could help."
                        items={
                            weaknesses
                        }
                        tone="orange"
                        emptyText="Nova has not identified clear weak areas yet."
                    />

                </section>


                {/* ==================================================
                    DIFFICULTY + KNOWLEDGE
                ================================================== */}

                <section
                    className="
                        grid
                        lg:grid-cols-2
                        gap-6
                        mb-6
                    "
                >

                    {/* =================================================
                        DIFFICULTY
                    ================================================= */}

                    <div
                        className="
                            nova-card
                        "
                    >

                        <SectionHeader
                            icon={
                                <BarChart3
                                    size={19}
                                />
                            }
                            iconClass="text-orange-400"
                            title="Difficulty profile"
                            subtitle="How your learning interactions have been classified."
                        />


                        {difficultyDistribution.length === 0 ? (

                            <EmptyState
                                icon={
                                    <BarChart3
                                        size={23}
                                    />
                                }
                                title="No difficulty data"
                                text="Nova needs more interactions before this profile becomes useful."
                            />

                        ) : (

                            <div
                                className="
                                    space-y-5
                                "
                            >

                                {difficultyDistribution.map(
                                    item => (

                                        <DifficultyRow
                                            key={
                                                item.label
                                            }
                                            {...item}
                                        />

                                    )
                                )}


                                <div
                                    className="
                                        pt-4
                                        border-t
                                        border-white/[0.06]
                                        flex
                                        justify-between
                                        text-xs
                                        text-slate-600
                                    "
                                >

                                    <span>
                                        Total classified
                                    </span>

                                    <span>
                                        {
                                            formatNumber(
                                                totalDifficulty
                                            )
                                        }
                                    </span>

                                </div>

                            </div>

                        )}

                    </div>


                    {/* =================================================
                        KNOWLEDGE MAP
                    ================================================= */}

                    <div
                        className="
                            nova-card
                        "
                    >

                        <SectionHeader
                            icon={
                                <Network
                                    size={19}
                                />
                            }
                            iconClass="text-cyan-400"
                            title="Knowledge map"
                            subtitle="Nova's current view of your subject knowledge."
                        />


                        {knowledgeSubjects.length === 0 ? (

                            <EmptyState
                                icon={
                                    <Network
                                        size={23}
                                    />
                                }
                                title="Knowledge map is empty"
                                text="Keep learning and Nova will gradually build this map."
                            />

                        ) : (

                            <div
                                className="
                                    space-y-4
                                    max-h-[330px]
                                    overflow-y-auto
                                    nova-scroll
                                    pr-1
                                "
                            >

                                {knowledgeSubjects.map(
                                    item => (

                                        <KnowledgeRow
                                            key={
                                                item.id
                                            }
                                            item={
                                                item
                                            }
                                        />

                                    )
                                )}

                            </div>

                        )}

                    </div>

                </section>


                {/* ==================================================
                    CURRENT SESSION
                ================================================== */}

                <section
                    className="
                        nova-card
                        mb-6
                    "
                >

                    <SectionHeader
                        icon={
                            <Clock3
                                size={19}
                            />
                        }
                        iconClass="text-blue-400"
                        title="Current learning session"
                        subtitle="What Nova currently has in context."
                    />


                    <div
                        className="
                            grid
                            grid-cols-2
                            md:grid-cols-4
                            gap-3
                        "
                    >

                        <SessionCard
                            label="Subject"
                            value={
                                session.subject
                            }
                            icon={
                                <BookOpen
                                    size={16}
                                />
                            }
                        />


                        <SessionCard
                            label="Topic"
                            value={
                                session.topic
                            }
                            icon={
                                <Target
                                    size={16}
                                />
                            }
                        />


                        <SessionCard
                            label="Mode"
                            value={
                                session.mode
                            }
                            icon={
                                <GraduationCap
                                    size={16}
                                />
                            }
                        />


                        <SessionCard
                            label="Score"
                            value={
                                session.score
                            }
                            icon={
                                <Trophy
                                    size={16}
                                />
                            }
                        />

                    </div>

                </section>


                {/* ==================================================
                    CONVERSATIONS
                ================================================== */}

                <section
                    className="
                        nova-card
                        mb-6
                    "
                >

                    <div
                        className="
                            flex
                            flex-col
                            lg:flex-row
                            lg:items-center
                            justify-between
                            gap-4
                            mb-6
                        "
                    >

                        <SectionHeader
                            icon={
                                <MessageSquare
                                    size={19}
                                />
                            }
                            iconClass="text-purple-400"
                            title="Recent conversations"
                            subtitle="Jump back into your previous learning sessions."
                            noMargin
                        />


                        <div
                            className="
                                flex
                                flex-col
                                sm:flex-row
                                gap-2
                            "
                        >

                            {/* SEARCH */}

                            <div
                                className="
                                    relative
                                "
                            >

                                <Search
                                    size={15}
                                    className="
                                        absolute
                                        left-3
                                        top-1/2
                                        -translate-y-1/2
                                        text-slate-600
                                    "
                                />


                                <input
                                    data-dashboard-search
                                    value={
                                        searchQuery
                                    }
                                    onChange={
                                        event =>
                                            setSearchQuery(
                                                event.target.value
                                            )
                                    }
                                    placeholder="Search conversations..."
                                    className="
                                        w-full
                                        sm:w-64
                                        pl-9
                                        pr-9
                                        py-2.5
                                        rounded-xl
                                        border
                                        border-white/[0.07]
                                        bg-white/[0.025]
                                        text-sm
                                        text-white
                                        placeholder:text-slate-600
                                        outline-none
                                        focus:border-blue-500/40
                                        transition
                                    "
                                    aria-label="Search conversations"
                                />


                                {!searchQuery && (

                                    <span
                                        className="
                                            absolute
                                            right-3
                                            top-1/2
                                            -translate-y-1/2
                                            hidden
                                            sm:block
                                            text-[10px]
                                            text-slate-700
                                            border
                                            border-white/[0.05]
                                            rounded
                                            px-1.5
                                            py-0.5
                                        "
                                    >
                                        /
                                    </span>

                                )}


                                {searchQuery && (

                                    <button
                                        onClick={() =>
                                            setSearchQuery("")
                                        }
                                        className="
                                            absolute
                                            right-2
                                            top-1/2
                                            -translate-y-1/2
                                            p-1
                                            text-slate-500
                                            hover:text-white
                                        "
                                        aria-label="Clear search"
                                    >

                                        <X
                                            size={14}
                                        />

                                    </button>

                                )}

                            </div>


                            {/* SORT */}

                            <div
                                className="
                                    relative
                                "
                            >

                                <select
                                    value={
                                        conversationSort
                                    }
                                    onChange={
                                        event =>
                                            setConversationSort(
                                                event.target.value
                                            )
                                    }
                                    className="
                                        appearance-none
                                        w-full
                                        sm:w-auto
                                        pl-3
                                        pr-9
                                        py-2.5
                                        rounded-xl
                                        border
                                        border-white/[0.07]
                                        bg-[#0b1018]
                                        text-sm
                                        text-slate-400
                                        outline-none
                                        focus:border-blue-500/40
                                    "
                                    aria-label="Sort conversations"
                                >

                                    <option value="recent">
                                        Most recent
                                    </option>

                                    <option value="messages">
                                        Most messages
                                    </option>

                                    <option value="title">
                                        Title
                                    </option>

                                </select>


                                <ChevronDown
                                    size={14}
                                    className="
                                        pointer-events-none
                                        absolute
                                        right-3
                                        top-1/2
                                        -translate-y-1/2
                                        text-slate-600
                                    "
                                />

                            </div>

                        </div>

                    </div>


                    {filteredConversations.length === 0 ? (

                        <EmptyState
                            icon={
                                <MessageSquare
                                    size={23}
                                />
                            }
                            title={
                                searchQuery
                                    ? "No matching conversations"
                                    : "No conversations yet"
                            }
                            text={
                                searchQuery
                                    ? "Try a different search term."
                                    : "Your future learning sessions will appear here."
                            }
                            action={
                                !searchQuery
                                    ? (
                                        <button
                                            onClick={
                                                openNewChat
                                            }
                                            className="
                                                px-4
                                                py-2.5
                                                rounded-xl
                                                bg-blue-600
                                                hover:bg-blue-500
                                                text-sm
                                                font-medium
                                                transition
                                            "
                                        >
                                            Start a conversation
                                        </button>
                                    )
                                    : null
                            }
                        />

                    ) : (

                        <div
                            className="
                                space-y-2
                            "
                        >

                            {filteredConversations.map(
                                conversation => (

                                    <ConversationRow
                                        key={
                                            conversation.id
                                        }
                                        conversation={
                                            conversation
                                        }
                                        onClick={() =>
                                            openConversation(
                                                conversation.id
                                            )
                                        }
                                    />

                                )
                            )}


                            {conversations.length > 5 && (

                                <button
                                    onClick={() =>
                                        setShowAllConversations(
                                            previous =>
                                                !previous
                                        )
                                    }
                                    className="
                                        w-full
                                        mt-3
                                        py-3
                                        rounded-xl
                                        border
                                        border-white/[0.05]
                                        bg-white/[0.015]
                                        hover:bg-white/[0.04]
                                        text-sm
                                        text-slate-500
                                        hover:text-white
                                        transition
                                    "
                                >

                                    {showAllConversations
                                        ? "Show less"
                                        : `Show all conversations (${conversations.length})`}

                                </button>

                            )}

                        </div>

                    )}

                </section>


                {/* ==================================================
                    FOOTER METRICS
                ================================================== */}

                <section
                    className="
                        grid
                        grid-cols-2
                        md:grid-cols-4
                        gap-3
                        pb-10
                    "
                >

                    <FooterMetric
                        icon={
                            <Database
                                size={17}
                            />
                        }
                        label="Memory"
                        value={
                            formatNumber(
                                stats.memory_count
                            )
                        }
                    />


                    <FooterMetric
                        icon={
                            <MessageSquare
                                size={17}
                            />
                        }
                        label="Conversations"
                        value={
                            formatNumber(
                                stats.conversation_count
                            )
                        }
                    />


                    <FooterMetric
                        icon={
                            <Brain
                                size={17}
                            />
                        }
                        label="Understanding checks"
                        value={
                            formatNumber(
                                stats.understanding_attempts
                            )
                        }
                    />


                    <FooterMetric
                        icon={
                            <Flame
                                size={17}
                            />
                        }
                        label="Study attempts"
                        value={
                            formatNumber(
                                stats.study_attempts
                            )
                        }
                    />

                </section>


                {/* ==================================================
                    BACKEND WARNING
                ================================================== */}

                {error && (

                    <div
                        className="
                            fixed
                            bottom-5
                            right-5
                            z-[60]
                            max-w-sm
                            p-4
                            rounded-2xl
                            border
                            border-orange-500/20
                            bg-[#11151d]/95
                            backdrop-blur-xl
                            shadow-2xl
                        "
                    >

                        <div
                            className="
                                flex
                                items-start
                                gap-3
                            "
                        >

                            <AlertCircle
                                size={18}
                                className="
                                    text-orange-400
                                    mt-0.5
                                    shrink-0
                                "
                            />


                            <div
                                className="
                                    flex-1
                                "
                            >

                                <p
                                    className="
                                        text-sm
                                        font-medium
                                    "
                                >
                                    Refresh failed
                                </p>


                                <p
                                    className="
                                        text-xs
                                        text-slate-500
                                        mt-1
                                        leading-5
                                    "
                                >
                                    {error}
                                </p>


                                <button
                                    onClick={() =>
                                        loadDashboard({
                                            silent: true
                                        })
                                    }
                                    className="
                                        mt-3
                                        text-xs
                                        text-orange-300
                                        hover:text-orange-200
                                        font-medium
                                    "
                                >
                                    Try again
                                </button>

                            </div>

                        </div>

                    </div>

                )}

            </main>


            {/* ==================================================
                STYLES
            ================================================== */}

            <style>{`

                .nova-card {

                    background:
                        linear-gradient(
                            145deg,
                            rgba(255,255,255,0.035),
                            rgba(255,255,255,0.012)
                        );

                    border:
                        1px solid
                        rgba(255,255,255,0.065);

                    border-radius:
                        1.5rem;

                    padding:
                        1.5rem;

                    box-shadow:
                        0 18px 60px
                        rgba(0,0,0,0.16);

                }


                .nova-card:hover {

                    border-color:
                        rgba(255,255,255,0.09);

                }


                .nova-scroll::-webkit-scrollbar {

                    width:
                        5px;

                }


                .nova-scroll::-webkit-scrollbar-track {

                    background:
                        transparent;

                }


                .nova-scroll::-webkit-scrollbar-thumb {

                    background:
                        rgba(
                            100,
                            116,
                            139,
                            0.25
                        );

                    border-radius:
                        999px;

                }


                .nova-scroll {

                    scrollbar-width:
                        thin;

                    scrollbar-color:
                        rgba(
                            100,
                            116,
                            139,
                            0.25
                        )
                        transparent;

                }


                @keyframes novaDashboardAppear {

                    from {

                        opacity:
                            0;

                        transform:
                            translateY(10px);

                    }

                    to {

                        opacity:
                            1;

                        transform:
                            translateY(0);

                    }

                }


                .nova-dashboard-appear {

                    animation:
                        novaDashboardAppear
                        0.45s
                        ease-out
                        both;

                }


                @media (
                    prefers-reduced-motion:
                    reduce
                ) {

                    *,
                    *::before,
                    *::after {

                        animation-duration:
                            0.01ms
                            !important;

                        animation-iteration-count:
                            1
                            !important;

                        scroll-behavior:
                            auto
                            !important;

                    }

                }

            `}</style>

        </div>

    );

}


// ============================================================
// LOADING SCREEN
// ============================================================

function DashboardLoading() {

    return (

        <div
            className="
                min-h-screen
                bg-[#070b12]
                text-white
                flex
                items-center
                justify-center
                px-6
            "
        >

            <div
                className="
                    w-full
                    max-w-md
                    text-center
                "
            >

                <div
                    className="
                        relative
                        mx-auto
                        w-20
                        h-20
                        flex
                        items-center
                        justify-center
                    "
                >

                    <div
                        className="
                            absolute
                            inset-0
                            rounded-3xl
                            bg-blue-500/10
                            blur-2xl
                            animate-pulse
                        "
                    />


                    <div
                        className="
                            relative
                            w-16
                            h-16
                            rounded-2xl
                            border
                            border-blue-500/20
                            bg-blue-500/10
                            flex
                            items-center
                            justify-center
                        "
                    >

                        <Brain
                            size={30}
                            className="
                                text-blue-400
                                animate-pulse
                            "
                        />

                    </div>

                </div>


                <h1
                    className="
                        mt-6
                        text-xl
                        font-semibold
                    "
                >
                    Loading your dashboard
                </h1>


                <p
                    className="
                        mt-2
                        text-sm
                        text-slate-600
                    "
                >
                    Nova is gathering your learning data...
                </p>


                <div
                    className="
                        mt-6
                        h-1
                        w-full
                        rounded-full
                        bg-white/[0.05]
                        overflow-hidden
                    "
                >

                    <div
                        className="
                            h-full
                            w-1/3
                            rounded-full
                            bg-blue-500
                            animate-pulse
                        "
                    />

                </div>

            </div>

        </div>

    );

}


// ============================================================
// ERROR SCREEN
// ============================================================

function DashboardError({
    error,
    onRetry,
    onHome
}) {

    return (

        <div
            className="
                min-h-screen
                bg-[#070b12]
                text-white
                flex
                items-center
                justify-center
                px-6
            "
        >

            <div
                className="
                    max-w-md
                    w-full
                    p-8
                    rounded-3xl
                    border
                    border-red-500/10
                    bg-white/[0.025]
                    text-center
                "
            >

                <div
                    className="
                        w-14
                        h-14
                        mx-auto
                        rounded-2xl
                        bg-red-500/10
                        border
                        border-red-500/20
                        flex
                        items-center
                        justify-center
                    "
                >

                    <AlertTriangle
                        size={25}
                        className="
                            text-red-400
                        "
                    />

                </div>


                <h1
                    className="
                        mt-5
                        text-xl
                        font-semibold
                    "
                >
                    Dashboard unavailable
                </h1>


                <p
                    className="
                        mt-2
                        text-sm
                        text-slate-500
                        leading-6
                    "
                >
                    {error}
                </p>


                <div
                    className="
                        mt-6
                        flex
                        gap-3
                    "
                >

                    <button
                        onClick={
                            onRetry
                        }
                        className="
                            flex-1
                            flex
                            items-center
                            justify-center
                            gap-2
                            px-4
                            py-3
                            rounded-xl
                            bg-blue-600
                            hover:bg-blue-500
                            font-medium
                            transition
                        "
                    >

                        <RefreshCw
                            size={16}
                        />

                        Try again

                    </button>


                    <button
                        onClick={
                            onHome
                        }
                        className="
                            flex-1
                            flex
                            items-center
                            justify-center
                            gap-2
                            px-4
                            py-3
                            rounded-xl
                            border
                            border-white/[0.08]
                            bg-white/[0.03]
                            text-slate-300
                            hover:bg-white/[0.06]
                            transition
                        "
                    >

                        <ArrowLeft
                            size={16}
                        />

                        Home

                    </button>

                </div>

            </div>

        </div>

    );

}


// ============================================================
// SECTION HEADER
// ============================================================

function SectionHeader({
    icon,
    iconClass = "text-blue-400",
    title,
    subtitle,
    action,
    noMargin = false
}) {

    return (

        <div
            className={`
                flex
                items-start
                justify-between
                gap-4
                ${noMargin ? "" : "mb-6"}
            `}
        >

            <div
                className="
                    flex
                    items-start
                    gap-3
                "
            >

                <div
                    className={`
                        w-9
                        h-9
                        rounded-xl
                        bg-white/[0.035]
                        border
                        border-white/[0.05]
                        flex
                        items-center
                        justify-center
                        shrink-0
                        ${iconClass}
                    `}
                >
                    {icon}
                </div>


                <div>

                    <h2
                        className="
                            text-sm
                            font-semibold
                            text-white
                        "
                    >
                        {title}
                    </h2>


                    {subtitle && (

                        <p
                            className="
                                text-xs
                                text-slate-600
                                mt-1
                                leading-5
                            "
                        >
                            {subtitle}
                        </p>

                    )}

                </div>

            </div>


            {action && (

                <span
                    className="
                        shrink-0
                        text-[11px]
                        text-slate-600
                        px-2.5
                        py-1.5
                        rounded-lg
                        bg-white/[0.025]
                        border
                        border-white/[0.04]
                    "
                >
                    {action}
                </span>

            )}

        </div>

    );

}


// ============================================================
// DASHBOARD STAT
// ============================================================

function DashboardStat({
    icon,
    label,
    value,
    detail,
    tone = "blue"
}) {

    const tones = {

        blue:
            "text-blue-400 bg-blue-500/10 border-blue-500/10",

        emerald:
            "text-emerald-400 bg-emerald-500/10 border-emerald-500/10",

        purple:
            "text-purple-400 bg-purple-500/10 border-purple-500/10",

        orange:
            "text-orange-400 bg-orange-500/10 border-orange-500/10"

    };


    return (

        <div
            className="
                rounded-2xl
                border
                border-white/[0.06]
                bg-white/[0.02]
                p-4
                sm:p-5
                hover:bg-white/[0.035]
                transition
            "
        >

            <div
                className="
                    flex
                    items-start
                    justify-between
                    gap-3
                "
            >

                <div
                    className={`
                        w-9
                        h-9
                        rounded-xl
                        border
                        flex
                        items-center
                        justify-center
                        ${tones[tone]}
                    `}
                >
                    {icon}
                </div>


                <Activity
                    size={14}
                    className="
                        text-slate-700
                    "
                />

            </div>


            <div
                className="
                    mt-4
                    text-2xl
                    sm:text-3xl
                    font-bold
                    tracking-tight
                "
            >
                {value}
            </div>


            <div
                className="
                    mt-1
                    text-xs
                    text-slate-500
                "
            >
                {label}
            </div>


            <div
                className="
                    mt-2
                    text-[11px]
                    text-slate-700
                    truncate
                "
                title={detail}
            >
                {detail}
            </div>

        </div>

    );

}


// ============================================================
// PROGRESS RING
// ============================================================

function ProgressRing({
    value,
    label,
    size = 180,
    tone = "blue"
}) {

    const safeValue =
        clamp(
            value
        );


    const stroke =
        10;


    const radius =
        (
            size -
            stroke
        ) /
        2;


    const circumference =
        2 *
        Math.PI *
        radius;


    const offset =
        circumference -
        (
            safeValue /
            100
        ) *
        circumference;


    const colors = {

        blue:
            "#3b82f6",

        purple:
            "#8b5cf6",

        emerald:
            "#10b981",

        orange:
            "#f97316"

    };


    return (

        <div
            className="
                relative
                shrink-0
            "
            style={{
                width: size,
                height: size
            }}
        >

            <svg
                width={size}
                height={size}
                viewBox={`0 0 ${size} ${size}`}
                className="
                    -rotate-90
                "
            >

                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke="rgba(255,255,255,0.055)"
                    strokeWidth={stroke}
                />


                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="none"
                    stroke={
                        colors[tone] ||
                        colors.blue
                    }
                    strokeWidth={stroke}
                    strokeLinecap="round"
                    strokeDasharray={
                        circumference
                    }
                    strokeDashoffset={
                        offset
                    }
                    style={{
                        transition:
                            "stroke-dashoffset 1s ease"
                    }}
                />

            </svg>


            <div
                className="
                    absolute
                    inset-0
                    flex
                    flex-col
                    items-center
                    justify-center
                "
            >

                <span
                    className="
                        text-3xl
                        font-bold
                        tracking-tight
                    "
                >
                    {
                        Math.round(
                            safeValue
                        )
                    }%
                </span>


                <span
                    className="
                        text-xs
                        text-slate-600
                        mt-1
                    "
                >
                    {label}
                </span>

            </div>

        </div>

    );

}


// ============================================================
// PROGRESS BAR
// ============================================================

function ProgressBar({
    value,
    tone = "blue",
    height = "h-2"
}) {

    const safeValue =
        clamp(
            value
        );


    const backgrounds = {

        blue:
            "bg-blue-500",

        emerald:
            "bg-emerald-500",

        purple:
            "bg-purple-500",

        orange:
            "bg-orange-500"

    };


    return (

        <div
            className={`
                w-full
                ${height}
                rounded-full
                bg-white/[0.055]
                overflow-hidden
            `}
        >

            <div
                className={`
                    h-full
                    rounded-full
                    ${backgrounds[tone] || backgrounds.blue}
                    transition-all
                    duration-700
                    ease-out
                `}
                style={{
                    width:
                        `${safeValue}%`
                }}
            />

        </div>

    );

}


// ============================================================
// METRIC BOX
// ============================================================

function MetricBox({
    icon,
    label,
    value
}) {

    return (

        <div
            className="
                rounded-xl
                border
                border-white/[0.05]
                bg-white/[0.02]
                p-3
            "
        >

            {icon && (

                <div
                    className="
                        text-slate-600
                        mb-2
                    "
                >
                    {icon}
                </div>

            )}


            <div
                className="
                    text-lg
                    font-semibold
                "
            >
                {value}
            </div>


            <div
                className="
                    text-[11px]
                    text-slate-600
                    mt-0.5
                "
            >
                {label}
            </div>

        </div>

    );

}


// ============================================================
// SUBJECT ROW
// ============================================================

function SubjectRow({
    subject,
    data,
    selected,
    onClick
}) {

    const mastery =
        clamp(
            data?.mastery
        );


    const tone =
        getMasteryTone(
            mastery
        );


    return (

        <div>

            <button
                onClick={
                    onClick
                }
                className="
                    w-full
                    text-left
                    rounded-xl
                    border
                    border-white/[0.045]
                    bg-white/[0.018]
                    hover:bg-white/[0.035]
                    hover:border-white/[0.08]
                    p-4
                    transition
                "
            >

                <div
                    className="
                        flex
                        items-center
                        gap-4
                    "
                >

                    <div
                        className="
                            w-10
                            h-10
                            rounded-xl
                            bg-white/[0.04]
                            border
                            border-white/[0.05]
                            flex
                            items-center
                            justify-center
                            text-slate-500
                            shrink-0
                        "
                    >

                        <BookOpen
                            size={17}
                        />

                    </div>


                    <div
                        className="
                            flex-1
                            min-w-0
                        "
                    >

                        <div
                            className="
                                flex
                                items-center
                                justify-between
                                gap-4
                                mb-2
                            "
                        >

                            <span
                                className="
                                    text-sm
                                    font-medium
                                    truncate
                                "
                            >
                                {subject}
                            </span>


                            <span
                                className={`
                                    text-xs
                                    font-semibold
                                    shrink-0
                                    ${
                                        tone === "success"
                                            ? "text-emerald-400"
                                            : tone === "warning"
                                                ? "text-orange-400"
                                                : tone === "danger"
                                                    ? "text-red-400"
                                                    : "text-blue-400"
                                    }
                                `}
                            >
                                {
                                    formatPercent(
                                        mastery
                                    )
                                }
                            </span>

                        </div>


                        <ProgressBar
                            value={
                                mastery
                            }
                            tone={
                                tone === "success"
                                    ? "emerald"
                                    : tone === "warning"
                                        ? "orange"
                                        : "blue"
                            }
                        />

                    </div>


                    <ChevronRight
                        size={16}
                        className={`
                            text-slate-700
                            transition-transform
                            ${
                                selected
                                    ? "rotate-90"
                                    : ""
                            }
                        `}
                    />

                </div>


                {selected && (

                    <div
                        className="
                            grid
                            grid-cols-3
                            gap-2
                            mt-4
                            pt-4
                            border-t
                            border-white/[0.05]
                        "
                    >

                        <SubjectMetric
                            label="Topics"
                            value={
                                data?.topics_count ||
                                0
                            }
                        />


                        <SubjectMetric
                            label="Correct"
                            value={
                                data?.correct_answers ||
                                0
                            }
                        />


                        <SubjectMetric
                            label="Wrong"
                            value={
                                data?.wrong_answers ||
                                0
                            }
                        />

                    </div>

                )}

            </button>

        </div>

    );

}


// ============================================================
// SUBJECT METRIC
// ============================================================

function SubjectMetric({
    label,
    value
}) {

    return (

        <div
            className="
                text-center
                py-2
                rounded-lg
                bg-white/[0.02]
            "
        >

            <div
                className="
                    text-sm
                    font-semibold
                "
            >
                {
                    formatNumber(
                        value
                    )
                }
            </div>


            <div
                className="
                    text-[10px]
                    text-slate-700
                    mt-1
                "
            >
                {label}
            </div>

        </div>

    );

}


// ============================================================
// PERFORMANCE HIGHLIGHT
// ============================================================

function PerformanceHighlight({
    icon,
    title,
    name,
    value,
    tone
}) {

    const isPositive =
        tone === "emerald";


    return (

        <div
            className={`
                p-4
                rounded-2xl
                border
                ${
                    isPositive
                        ? "border-emerald-500/10 bg-emerald-500/[0.035]"
                        : "border-orange-500/10 bg-orange-500/[0.035]"
                }
            `}
        >

            <div
                className="
                    flex
                    items-center
                    gap-2
                    mb-3
                "
            >

                <div
                    className={`
                        ${
                            isPositive
                                ? "text-emerald-400"
                                : "text-orange-400"
                        }
                    `}
                >
                    {icon}
                </div>


                <span
                    className="
                        text-xs
                        text-slate-500
                    "
                >
                    {title}
                </span>

            </div>


            <div
                className="
                    flex
                    items-center
                    justify-between
                    gap-3
                "
            >

                <span
                    className="
                        font-medium
                        truncate
                    "
                    title={name}
                >
                    {name}
                </span>


                <span
                    className={`
                        text-sm
                        font-semibold
                        ${
                            isPositive
                                ? "text-emerald-400"
                                : "text-orange-400"
                        }
                    `}
                >
                    {
                        formatPercent(
                            value
                        )
                    }
                </span>

            </div>

        </div>

    );

}


// ============================================================
// INSIGHT CARD
// ============================================================

function InsightCard({
    icon,
    title,
    subtitle,
    items,
    tone,
    emptyText
}) {

    const positive =
        tone === "emerald";


    return (

        <div
            className="
                nova-card
            "
        >

            <SectionHeader
                icon={
                    icon
                }
                iconClass={
                    positive
                        ? "text-emerald-400"
                        : "text-orange-400"
                }
                title={
                    title
                }
                subtitle={
                    subtitle
                }
            />


            {items.length === 0 ? (

                <div
                    className="
                        rounded-xl
                        border
                        border-dashed
                        border-white/[0.06]
                        p-6
                        text-center
                    "
                >

                    <p
                        className="
                            text-xs
                            text-slate-600
                        "
                    >
                        {emptyText}
                    </p>

                </div>

            ) : (

                <div
                    className="
                        flex
                        flex-wrap
                        gap-2
                    "
                >

                    {items.map(
                        (
                            item,
                            index
                        ) => (

                            <span
                                key={
                                    `${item}-${index}`
                                }
                                className={`
                                    inline-flex
                                    items-center
                                    gap-2
                                    px-3
                                    py-2
                                    rounded-xl
                                    text-xs
                                    border
                                    ${
                                        positive
                                            ? "bg-emerald-500/[0.05] border-emerald-500/10 text-emerald-300"
                                            : "bg-orange-500/[0.05] border-orange-500/10 text-orange-300"
                                    }
                                `}
                            >

                                <span
                                    className="
                                        w-1.5
                                        h-1.5
                                        rounded-full
                                        bg-current
                                    "
                                />

                                {item}

                            </span>

                        )
                    )}

                </div>

            )}

        </div>

    );

}


// ============================================================
// DIFFICULTY ROW
// ============================================================

function DifficultyRow({
    label,
    value,
    percentage
}) {

    const tones = {

        Easy:
            "bg-emerald-500",

        Medium:
            "bg-orange-400",

        Hard:
            "bg-red-500"

    };


    return (

        <div>

            <div
                className="
                    flex
                    justify-between
                    items-center
                    mb-2
                "
            >

                <div
                    className="
                        flex
                        items-center
                        gap-2
                    "
                >

                    <span
                        className={`
                            w-2
                            h-2
                            rounded-full
                            ${
                                tones[label] ||
                                "bg-blue-500"
                            }
                        `}
                    />


                    <span
                        className="
                            text-sm
                            text-slate-300
                        "
                    >
                        {label}
                    </span>

                </div>


                <span
                    className="
                        text-xs
                        text-slate-500
                    "
                >
                    {
                        formatNumber(
                            value
                        )
                    }
                    {" "}
                    ·
                    {" "}
                    {
                        formatPercent(
                            percentage
                        )
                    }
                </span>

            </div>


            <div
                className="
                    h-2
                    rounded-full
                    bg-white/[0.05]
                    overflow-hidden
                "
            >

                <div
                    className={`
                        h-full
                        rounded-full
                        ${
                            tones[label] ||
                            "bg-blue-500"
                        }
                        transition-all
                        duration-700
                    `}
                    style={{
                        width:
                            `${clamp(
                                percentage
                            )}%`
                    }}
                />

            </div>

        </div>

    );

}


// ============================================================
// KNOWLEDGE ROW
// ============================================================

function KnowledgeRow({
    item
}) {

    const confidence =
        clamp(
            item.confidence
        );


    return (

        <div>

            <div
                className="
                    flex
                    items-center
                    justify-between
                    gap-3
                    mb-2
                "
            >

                <span
                    className="
                        text-sm
                        font-medium
                        truncate
                    "
                    title={
                        item.name
                    }
                >
                    {item.name}
                </span>


                <span
                    className="
                        text-xs
                        text-slate-600
                        shrink-0
                    "
                >
                    {
                        formatPercent(
                            confidence
                        )
                    }
                </span>

            </div>


            <ProgressBar
                value={
                    confidence
                }
                tone="blue"
            />


            <div
                className="
                    flex
                    items-center
                    gap-3
                    mt-1.5
                    text-[10px]
                    text-slate-700
                "
            >

                <span>
                    {formatNumber(item.topics)}
                    {" "}
                    topics
                </span>

                <span>
                    {formatNumber(item.attempts)}
                    {" "}
                    attempts
                </span>

            </div>

        </div>

    );

}


// ============================================================
// SESSION CARD
// ============================================================

function SessionCard({
    label,
    value,
    icon
}) {

    return (

        <div
            className="
                p-4
                rounded-xl
                border
                border-white/[0.05]
                bg-white/[0.02]
                min-w-0
            "
        >

            <div
                className="
                    flex
                    items-center
                    gap-2
                    text-slate-600
                    mb-3
                "
            >

                {icon}

                <span
                    className="
                        text-[11px]
                    "
                >
                    {label}
                </span>

            </div>


            <div
                className="
                    text-sm
                    font-medium
                    truncate
                "
                title={
                    String(
                        value
                    )
                }
            >
                {
                    safeString(
                        value,
                        "None"
                    )
                }
            </div>

        </div>

    );

}


// ============================================================
// CONVERSATION ROW
// ============================================================

function ConversationRow({
    conversation,
    onClick
}) {

    return (

        <button
            onClick={
                onClick
            }
            className="
                group
                w-full
                text-left
                p-4
                rounded-xl
                border
                border-white/[0.04]
                bg-white/[0.015]
                hover:bg-white/[0.035]
                hover:border-white/[0.08]
                transition
            "
        >

            <div
                className="
                    flex
                    items-center
                    gap-3
                "
            >

                <div
                    className="
                        w-10
                        h-10
                        rounded-xl
                        bg-purple-500/10
                        border
                        border-purple-500/10
                        flex
                        items-center
                        justify-center
                        text-purple-400
                        shrink-0
                    "
                >

                    <MessageSquare
                        size={17}
                    />

                </div>


                <div
                    className="
                        flex-1
                        min-w-0
                    "
                >

                    <div
                        className="
                            flex
                            items-center
                            justify-between
                            gap-4
                        "
                    >

                        <span
                            className="
                                text-sm
                                font-medium
                                truncate
                            "
                        >
                            {
                                conversation.title
                            }
                        </span>


                        <span
                            className="
                                hidden
                                sm:block
                                text-[10px]
                                text-slate-700
                                shrink-0
                            "
                        >
                            {
                                formatRelativeTime(
                                    conversation.updated_at
                                )
                            }
                        </span>

                    </div>


                    <div
                        className="
                            flex
                            items-center
                            justify-between
                            gap-4
                            mt-1
                        "
                    >

                        <p
                            className="
                                text-xs
                                text-slate-600
                                truncate
                            "
                        >
                            {
                                conversation.last_message
                            }
                        </p>


                        <span
                            className="
                                text-[10px]
                                text-slate-700
                                shrink-0
                            "
                        >
                            {
                                formatNumber(
                                    conversation.message_count
                                )
                            }
                            {" "}
                            msgs
                        </span>

                    </div>

                </div>


                <ChevronRight
                    size={16}
                    className="
                        text-slate-700
                        group-hover:text-slate-400
                        group-hover:translate-x-0.5
                        transition
                        shrink-0
                    "
                />

            </div>

        </button>

    );

}


// ============================================================
// FOOTER METRIC
// ============================================================

function FooterMetric({
    icon,
    label,
    value
}) {

    return (

        <div
            className="
                flex
                items-center
                gap-3
                p-4
                rounded-xl
                border
                border-white/[0.05]
                bg-white/[0.018]
            "
        >

            <div
                className="
                    w-9
                    h-9
                    rounded-lg
                    bg-white/[0.035]
                    flex
                    items-center
                    justify-center
                    text-slate-600
                    shrink-0
                "
            >
                {icon}
            </div>


            <div
                className="
                    min-w-0
                "
            >

                <div
                    className="
                        font-semibold
                        text-sm
                    "
                >
                    {value}
                </div>


                <div
                    className="
                        text-[10px]
                        text-slate-700
                        mt-0.5
                        truncate
                    "
                >
                    {label}
                </div>

            </div>

        </div>

    );

}


// ============================================================
// EMPTY STATE
// ============================================================

function EmptyState({
    icon,
    title,
    text,
    action
}) {

    return (

        <div
            className="
                py-8
                px-5
                text-center
                rounded-2xl
                border
                border-dashed
                border-white/[0.06]
                bg-white/[0.01]
            "
        >

            {icon && (

                <div
                    className="
                        w-11
                        h-11
                        mx-auto
                        rounded-xl
                        bg-white/[0.03]
                        border
                        border-white/[0.05]
                        flex
                        items-center
                        justify-center
                        text-slate-600
                    "
                >
                    {icon}
                </div>

            )}


            {title && (

                <h3
                    className="
                        mt-4
                        text-sm
                        font-medium
                        text-slate-400
                    "
                >
                    {title}
                </h3>

            )}


            {text && (

                <p
                    className="
                        mt-1.5
                        text-xs
                        text-slate-700
                        leading-5
                        max-w-sm
                        mx-auto
                    "
                >
                    {text}
                </p>

            )}


            {action && (

                <div
                    className="
                        mt-5
                    "
                >
                    {action}
                </div>

            )}

        </div>

    );

}
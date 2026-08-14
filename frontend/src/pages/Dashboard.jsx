import {
    useEffect,
    useState
} from "react";

import {
    useNavigate
} from "react-router-dom";

import {
    ArrowLeft,
    BookOpen,
    Brain,
    Target,
    TrendingUp,
    CheckCircle,
    XCircle,
    Clock,
    MessageSquare,
    Database,
    Award,
    AlertTriangle,
    BarChart3,
    RefreshCw
} from "lucide-react";


const API_URL =
    "http://127.0.0.1:8000";


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
        error,
        setError
    ] = useState(null);


    // =====================================================
    // LOAD DASHBOARD
    // =====================================================

    async function loadDashboard() {

        setLoading(true);

        setError(null);


        try {

            const user =
                JSON.parse(
                    localStorage.getItem(
                        "nova_user"
                    ) || "null"
                );


            if (!user?.email) {

                navigate(
                    "/login"
                );

                return;

            }


            const response =
                await fetch(
                    `${API_URL}/dashboard?email=${encodeURIComponent(
                        user.email
                    )}`
                );


            if (!response.ok) {

                throw new Error(
                    `Dashboard request failed: HTTP ${response.status}`
                );

            }


            const data =
                await response.json();


            setDashboard(
                data
            );

        } catch (err) {

            console.error(
                "Dashboard error:",
                err
            );


            setError(
                err.message
            );

        } finally {

            setLoading(false);

        }

    }


    // =====================================================
    // INITIAL LOAD
    // =====================================================

    useEffect(() => {

        loadDashboard();

    }, []);


    // =====================================================
    // LOADING
    // =====================================================

    if (loading) {

        return (

            <div
                className="
                    min-h-screen
                    bg-gray-950
                    text-white
                    flex
                    items-center
                    justify-center
                "
            >

                <div
                    className="
                        flex
                        flex-col
                        items-center
                        gap-4
                        text-gray-400
                    "
                >

                    <Brain
                        size={42}
                        className="
                            animate-pulse
                        "
                    />

                    <p>
                        Loading your learning dashboard...
                    </p>

                </div>

            </div>

        );

    }


    // =====================================================
    // ERROR
    // =====================================================

    if (error) {

        return (

            <div
                className="
                    min-h-screen
                    bg-gray-950
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
                        bg-gray-900
                        border
                        border-gray-800
                        rounded-2xl
                        p-8
                        text-center
                    "
                >

                    <AlertTriangle
                        size={42}
                        className="
                            mx-auto
                            mb-4
                            text-red-400
                        "
                    />

                    <h1
                        className="
                            text-xl
                            font-semibold
                            mb-2
                        "
                    >
                        Dashboard unavailable
                    </h1>


                    <p
                        className="
                            text-gray-500
                            text-sm
                            mb-6
                        "
                    >
                        {error}
                    </p>


                    <button
                        onClick={loadDashboard}
                        className="
                            bg-blue-600
                            hover:bg-blue-700
                            px-5
                            py-3
                            rounded-xl
                            font-medium
                            transition
                        "
                    >
                        Try again
                    </button>

                </div>

            </div>

        );

    }


    if (!dashboard) {
        return null;
    }


    const stats =
        dashboard.stats || {};


    const subjects =
        dashboard.subjects || {};


    const knowledgeSubjects =
        dashboard.knowledge_subjects || [];


    const strengths =
        dashboard.strengths || [];


    const weaknesses =
        dashboard.weaknesses || [];


    const difficulty =
        dashboard.difficulty || {};


    const session =
        dashboard.session || {};


    const recentConversations =
        dashboard.recent_conversations || [];


    const subjectEntries =
        Object.entries(
            subjects
        );


    const totalDifficulty =
        (
            difficulty.easy || 0
        ) +
        (
            difficulty.medium || 0
        ) +
        (
            difficulty.hard || 0
        );


    // =====================================================
    // HELPERS
    // =====================================================

    function formatNumber(
        value
    ) {

        if (
            typeof value !==
            "number"
        ) {

            return "0";

        }

        return value.toLocaleString();

    }


    function masteryLabel(
        value
    ) {

        if (value >= 90) {
            return "Excellent";
        }

        if (value >= 75) {
            return "Strong";
        }

        if (value >= 50) {
            return "Developing";
        }

        return "Needs work";

    }


    function masteryBar(
        value
    ) {

        const safeValue =
            Math.max(
                0,
                Math.min(
                    100,
                    Number(value) || 0
                )
            );


        return (

            <div
                className="
                    w-full
                    h-2
                    bg-gray-800
                    rounded-full
                    overflow-hidden
                "
            >

                <div
                    className="
                        h-full
                        bg-blue-500
                        rounded-full
                        transition-all
                    "
                    style={{
                        width:
                            `${safeValue}%`
                    }}
                />

            </div>

        );

    }


    // =====================================================
    // UI
    // =====================================================

    return (

        <div
            className="
                min-h-screen
                bg-gray-950
                text-white
            "
        >

            {/* =================================================
                HEADER
            ================================================= */}

            <header
                className="
                    h-16
                    border-b
                    border-gray-800
                    px-5
                    md:px-8
                    flex
                    items-center
                    justify-between
                    sticky
                    top-0
                    z-40
                    bg-gray-950/95
                    backdrop-blur
                "
            >

                <button
                    onClick={() =>
                        navigate("/")
                    }
                    className="
                        flex
                        items-center
                        gap-3
                        text-gray-400
                        hover:text-white
                        transition
                    "
                >

                    <ArrowLeft
                        size={19}
                    />

                    <span
                        className="
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

                    <Brain
                        size={22}
                        className="
                            text-blue-400
                        "
                    />

                    <div>

                        <h1
                            className="
                                font-semibold
                                leading-none
                            "
                        >
                            Nova Dashboard
                        </h1>

                        <p
                            className="
                                text-[11px]
                                text-gray-500
                                mt-1
                            "
                        >
                            Your learning overview
                        </p>

                    </div>

                </div>


                <button
                    onClick={loadDashboard}
                    disabled={loading}
                    className="
                        flex
                        items-center
                        gap-2
                        px-3
                        py-2
                        rounded-xl
                        bg-gray-900
                        border
                        border-gray-800
                        text-gray-400
                        hover:text-white
                        hover:border-gray-700
                        transition
                    "
                >

                    <RefreshCw
                        size={16}
                    />

                    <span
                        className="
                            hidden
                            md:block
                            text-sm
                        "
                    >
                        Refresh
                    </span>

                </button>

            </header>


            {/* =================================================
                CONTENT
            ================================================= */}

            <main
                className="
                    max-w-7xl
                    mx-auto
                    px-5
                    md:px-8
                    py-8
                "
            >

                {/* =================================================
                    TITLE
                ================================================= */}

                <section
                    className="
                        mb-8
                    "
                >

                    <p
                        className="
                            text-blue-400
                            text-sm
                            font-medium
                            mb-2
                        "
                    >
                        LEARNING OVERVIEW
                    </p>


                    <h2
                        className="
                            text-3xl
                            md:text-4xl
                            font-semibold
                            tracking-tight
                        "
                    >
                        Your progress
                    </h2>


                    <p
                        className="
                            mt-2
                            text-gray-500
                            max-w-2xl
                        "
                    >
                        Track what you have studied,
                        what you understand, and where
                        Nova thinks you can improve.
                    </p>

                </section>


                {/* =================================================
                    STAT CARDS
                ================================================= */}

                <section
                    className="
                        grid
                        grid-cols-2
                        lg:grid-cols-4
                        gap-4
                        mb-8
                    "
                >

                    <StatCard
                        icon={
                            <MessageSquare
                                size={20}
                            />
                        }
                        label="Questions"
                        value={
                            formatNumber(
                                stats.questions
                            )
                        }
                    />


                    <StatCard
                        icon={
                            <BookOpen
                                size={20}
                            />
                        }
                        label="Subjects"
                        value={
                            formatNumber(
                                stats.total_subjects
                            )
                        }
                    />


                    <StatCard
                        icon={
                            <Target
                                size={20}
                            />
                        }
                        label="Topics"
                        value={
                            formatNumber(
                                stats.total_topics
                            )
                        }
                    />


                    <StatCard
                        icon={
                            <TrendingUp
                                size={20}
                            />
                        }
                        label="Overall mastery"
                        value={
                            `${stats.overall_mastery || 0}%`
                        }
                    />

                </section>


                {/* =================================================
                    MAIN GRID
                ================================================= */}

                <section
                    className="
                        grid
                        lg:grid-cols-3
                        gap-6
                        mb-8
                    "
                >

                    {/* OVERALL MASTERY */}

                    <div
                        className="
                            lg:col-span-2
                            bg-gray-900
                            border
                            border-gray-800
                            rounded-2xl
                            p-6
                        "
                    >

                        <div
                            className="
                                flex
                                items-start
                                justify-between
                                mb-6
                            "
                        >

                            <div>

                                <div
                                    className="
                                        flex
                                        items-center
                                        gap-2
                                    "
                                >

                                    <Target
                                        size={19}
                                        className="
                                            text-blue-400
                                        "
                                    />

                                    <h3
                                        className="
                                            font-semibold
                                        "
                                    >
                                        Overall mastery
                                    </h3>

                                </div>


                                <p
                                    className="
                                        text-sm
                                        text-gray-500
                                        mt-1
                                    "
                                >
                                    Based on recorded answers
                                </p>

                            </div>


                            <div
                                className="
                                    text-right
                                "
                            >

                                <div
                                    className="
                                        text-3xl
                                        font-semibold
                                    "
                                >
                                    {
                                        stats.overall_mastery ||
                                        0
                                    }%
                                </div>


                                <div
                                    className="
                                        text-xs
                                        text-gray-500
                                    "
                                >
                                    {
                                        masteryLabel(
                                            stats.overall_mastery
                                        )
                                    }
                                </div>

                            </div>

                        </div>


                        <div
                            className="
                                h-4
                                bg-gray-800
                                rounded-full
                                overflow-hidden
                                mb-6
                            "
                        >

                            <div
                                className="
                                    h-full
                                    bg-blue-500
                                    rounded-full
                                    transition-all
                                "
                                style={{
                                    width:
                                        `${Math.min(
                                            100,
                                            Math.max(
                                                0,
                                                Number(
                                                    stats.overall_mastery
                                                ) || 0
                                            )
                                        )}%`
                                }}
                            />

                        </div>


                        <div
                            className="
                                grid
                                grid-cols-3
                                gap-4
                            "
                        >

                            <MiniStat
                                label="Correct"
                                value={
                                    formatNumber(
                                        stats.correct_answers
                                    )
                                }
                                icon={
                                    <CheckCircle
                                        size={16}
                                    />
                                }
                            />


                            <MiniStat
                                label="Wrong"
                                value={
                                    formatNumber(
                                        stats.wrong_answers
                                    )
                                }
                                icon={
                                    <XCircle
                                        size={16}
                                    />
                                }
                            />


                            <MiniStat
                                label="Attempts"
                                value={
                                    formatNumber(
                                        stats.study_attempts
                                    )
                                }
                                icon={
                                    <BarChart3
                                        size={16}
                                    />
                                }
                            />

                        </div>

                    </div>


                    {/* CONFIDENCE */}

                    <div
                        className="
                            bg-gray-900
                            border
                            border-gray-800
                            rounded-2xl
                            p-6
                        "
                    >

                        <div
                            className="
                                flex
                                items-center
                                gap-2
                                mb-2
                            "
                        >

                            <Brain
                                size={19}
                                className="
                                    text-purple-400
                                "
                            />

                            <h3
                                className="
                                    font-semibold
                                "
                            >
                                Understanding
                            </h3>

                        </div>


                        <p
                            className="
                                text-sm
                                text-gray-500
                                mb-6
                            "
                        >
                            Nova's current confidence estimate.
                        </p>


                        <div
                            className="
                                flex
                                items-center
                                justify-center
                                mb-5
                            "
                        >

                            <div
                                className="
                                    w-36
                                    h-36
                                    rounded-full
                                    border-[10px]
                                    border-gray-800
                                    flex
                                    items-center
                                    justify-center
                                    relative
                                "
                            >

                                <div
                                    className="
                                        absolute
                                        inset-[-10px]
                                        rounded-full
                                        border-[10px]
                                        border-transparent
                                    "
                                    style={{
                                        borderTopColor:
                                            "#8b5cf6",
                                        borderRightColor:
                                            (
                                                stats.average_confidence ||
                                                0
                                            ) >= 50
                                                ? "#8b5cf6"
                                                : "transparent"
                                    }}
                                />

                                <div
                                    className="
                                        text-center
                                    "
                                >

                                    <div
                                        className="
                                            text-3xl
                                            font-semibold
                                        "
                                    >
                                        {
                                            stats.average_confidence ||
                                            0
                                        }%
                                    </div>

                                    <div
                                        className="
                                            text-xs
                                            text-gray-500
                                        "
                                    >
                                        confidence
                                    </div>

                                </div>

                            </div>

                        </div>


                        <div
                            className="
                                text-center
                                text-sm
                                text-gray-500
                            "
                        >
                            {
                                stats.understanding_attempts ||
                                0
                            } understanding checks
                        </div>

                    </div>

                </section>


                {/* =================================================
                    SUBJECTS
                ================================================= */}

                <section
                    className="
                        bg-gray-900
                        border
                        border-gray-800
                        rounded-2xl
                        p-6
                        mb-8
                    "
                >

                    <div
                        className="
                            flex
                            items-center
                            justify-between
                            mb-6
                        "
                    >

                        <div>

                            <div
                                className="
                                    flex
                                    items-center
                                    gap-2
                                "
                            >

                                <BookOpen
                                    size={19}
                                    className="
                                        text-green-400
                                    "
                                />

                                <h3
                                    className="
                                        font-semibold
                                    "
                                >
                                    Subjects
                                </h3>

                            </div>


                            <p
                                className="
                                    text-sm
                                    text-gray-500
                                    mt-1
                                "
                            >
                                Your subject-by-subject progress.
                            </p>

                        </div>

                    </div>


                    {subjectEntries.length === 0 ? (

                        <EmptyState
                            text="
                                No subject data yet.
                                Start studying with Nova.
                            "
                        />

                    ) : (

                        <div
                            className="
                                grid
                                md:grid-cols-2
                                gap-4
                            "
                        >

                            {subjectEntries.map(
                                ([
                                    subject,
                                    data
                                ]) => (

                                    <div
                                        key={subject}
                                        className="
                                            bg-gray-950
                                            border
                                            border-gray-800
                                            rounded-xl
                                            p-5
                                        "
                                    >

                                        <div
                                            className="
                                                flex
                                                justify-between
                                                items-center
                                                mb-3
                                            "
                                        >

                                            <div
                                                className="
                                                    font-medium
                                                    truncate
                                                    pr-4
                                                "
                                            >
                                                {subject}
                                            </div>


                                            <div
                                                className="
                                                    text-sm
                                                    font-semibold
                                                    text-blue-400
                                                "
                                            >
                                                {
                                                    data.mastery ||
                                                    0
                                                }%
                                            </div>

                                        </div>


                                        {
                                            masteryBar(
                                                data.mastery
                                            )
                                        }


                                        <div
                                            className="
                                                grid
                                                grid-cols-3
                                                gap-2
                                                mt-4
                                            "
                                        >

                                            <SmallMetric
                                                label="Topics"
                                                value={
                                                    data.topics_count ||
                                                    0
                                                }
                                            />

                                            <SmallMetric
                                                label="Correct"
                                                value={
                                                    data.correct_answers ||
                                                    0
                                                }
                                            />

                                            <SmallMetric
                                                label="Wrong"
                                                value={
                                                    data.wrong_answers ||
                                                    0
                                                }
                                            />

                                        </div>

                                    </div>

                                )
                            )}

                        </div>

                    )}

                </section>


                {/* =================================================
                    STRENGTHS / WEAKNESSES
                ================================================= */}

                <section
                    className="
                        grid
                        md:grid-cols-2
                        gap-6
                        mb-8
                    "
                >

                    {/* STRENGTHS */}

                    <div
                        className="
                            bg-gray-900
                            border
                            border-gray-800
                            rounded-2xl
                            p-6
                        "
                    >

                        <div
                            className="
                                flex
                                items-center
                                gap-2
                                mb-5
                            "
                        >

                            <Award
                                size={19}
                                className="
                                    text-green-400
                                "
                            />

                            <h3
                                className="
                                    font-semibold
                                "
                            >
                                Strengths
                            </h3>

                        </div>


                        {strengths.length === 0 ? (

                            <p
                                className="
                                    text-sm
                                    text-gray-500
                                "
                            >
                                Nova hasn't identified
                                clear strengths yet.
                            </p>

                        ) : (

                            <div
                                className="
                                    flex
                                    flex-wrap
                                    gap-2
                                "
                            >

                                {strengths.map(
                                    (
                                        item,
                                        index
                                    ) => (

                                        <span
                                            key={
                                                `${item}-${index}`
                                            }
                                            className="
                                                px-3
                                                py-2
                                                rounded-xl
                                                bg-green-950
                                                border
                                                border-green-900
                                                text-green-300
                                                text-sm
                                            "
                                        >
                                            {item}
                                        </span>

                                    )
                                )}

                            </div>

                        )}

                    </div>


                    {/* WEAKNESSES */}

                    <div
                        className="
                            bg-gray-900
                            border
                            border-gray-800
                            rounded-2xl
                            p-6
                        "
                    >

                        <div
                            className="
                                flex
                                items-center
                                gap-2
                                mb-5
                            "
                        >

                            <AlertTriangle
                                size={19}
                                className="
                                    text-yellow-400
                                "
                            />

                            <h3
                                className="
                                    font-semibold
                                "
                            >
                                Needs attention
                            </h3>

                        </div>


                        {weaknesses.length === 0 ? (

                            <p
                                className="
                                    text-sm
                                    text-gray-500
                                "
                            >
                                Nova hasn't identified
                                clear weak areas yet.
                            </p>

                        ) : (

                            <div
                                className="
                                    flex
                                    flex-wrap
                                    gap-2
                                "
                            >

                                {weaknesses.map(
                                    (
                                        item,
                                        index
                                    ) => (

                                        <span
                                            key={
                                                `${item}-${index}`
                                            }
                                            className="
                                                px-3
                                                py-2
                                                rounded-xl
                                                bg-yellow-950
                                                border
                                                border-yellow-900
                                                text-yellow-300
                                                text-sm
                                            "
                                        >
                                            {item}
                                        </span>

                                    )
                                )}

                            </div>

                        )}

                    </div>

                </section>


                {/* =================================================
                    DIFFICULTY
                ================================================= */}

                <section
                    className="
                        grid
                        lg:grid-cols-2
                        gap-6
                        mb-8
                    "
                >

                    <div
                        className="
                            bg-gray-900
                            border
                            border-gray-800
                            rounded-2xl
                            p-6
                        "
                    >

                        <div
                            className="
                                flex
                                items-center
                                gap-2
                                mb-2
                            "
                        >

                            <BarChart3
                                size={19}
                                className="
                                    text-orange-400
                                "
                            />

                            <h3
                                className="
                                    font-semibold
                                "
                            >
                                Difficulty
                            </h3>

                        </div>


                        <p
                            className="
                                text-sm
                                text-gray-500
                                mb-6
                            "
                        >
                            How difficult your interactions
                            have been classified.
                        </p>


                        {totalDifficulty === 0 ? (

                            <EmptyState
                                text="
                                    No difficulty data yet.
                                "
                            />

                        ) : (

                            <div
                                className="
                                    space-y-5
                                "
                            >

                                <DifficultyBar
                                    label="Easy"
                                    value={
                                        difficulty.easy ||
                                        0
                                    }
                                    total={
                                        totalDifficulty
                                    }
                                />

                                <DifficultyBar
                                    label="Medium"
                                    value={
                                        difficulty.medium ||
                                        0
                                    }
                                    total={
                                        totalDifficulty
                                    }
                                />

                                <DifficultyBar
                                    label="Hard"
                                    value={
                                        difficulty.hard ||
                                        0
                                    }
                                    total={
                                        totalDifficulty
                                    }
                                />

                            </div>

                        )}

                    </div>


                    {/* KNOWLEDGE MAP */}

                    <div
                        className="
                            bg-gray-900
                            border
                            border-gray-800
                            rounded-2xl
                            p-6
                        "
                    >

                        <div
                            className="
                                flex
                                items-center
                                gap-2
                                mb-2
                            "
                        >

                            <Database
                                size={19}
                                className="
                                    text-cyan-400
                                "
                            />

                            <h3
                                className="
                                    font-semibold
                                "
                            >
                                Knowledge map
                            </h3>

                        </div>


                        <p
                            className="
                                text-sm
                                text-gray-500
                                mb-6
                            "
                        >
                            Nova's current view of your
                            subject knowledge.
                        </p>


                        {knowledgeSubjects.length === 0 ? (

                            <EmptyState
                                text="
                                    Your knowledge map is
                                    still being built.
                                "
                            />

                        ) : (

                            <div
                                className="
                                    space-y-4
                                    max-h-64
                                    overflow-y-auto
                                    nova-dashboard-scroll
                                "
                            >

                                {knowledgeSubjects.map(
                                    item => (

                                        <div
                                            key={
                                                item.name
                                            }
                                        >

                                            <div
                                                className="
                                                    flex
                                                    justify-between
                                                    mb-2
                                                    text-sm
                                                "
                                            >

                                                <span>
                                                    {
                                                        item.name
                                                    }
                                                </span>

                                                <span
                                                    className="
                                                        text-gray-500
                                                    "
                                                >
                                                    {
                                                        item.confidence
                                                    }%
                                                </span>

                                            </div>


                                            {
                                                masteryBar(
                                                    item.confidence
                                                )
                                            }


                                            <div
                                                className="
                                                    text-[11px]
                                                    text-gray-600
                                                    mt-1
                                                "
                                            >
                                                {
                                                    item.topics
                                                } topics •{" "}
                                                {
                                                    item.attempts
                                                } attempts
                                            </div>

                                        </div>

                                    )
                                )}

                            </div>

                        )}

                    </div>

                </section>


                {/* =================================================
                    CURRENT SESSION
                ================================================= */}

                <section
                    className="
                        bg-gray-900
                        border
                        border-gray-800
                        rounded-2xl
                        p-6
                        mb-8
                    "
                >

                    <div
                        className="
                            flex
                            items-center
                            gap-2
                            mb-6
                        "
                    >

                        <Clock
                            size={19}
                            className="
                                text-blue-400
                            "
                        />

                        <div>

                            <h3
                                className="
                                    font-semibold
                                "
                            >
                                Current learning session
                            </h3>

                            <p
                                className="
                                    text-sm
                                    text-gray-500
                                "
                            >
                                What Nova currently has in context.
                            </p>

                        </div>

                    </div>


                    <div
                        className="
                            grid
                            grid-cols-2
                            md:grid-cols-4
                            gap-4
                        "
                    >

                        <SessionItem
                            label="Subject"
                            value={
                                session.subject ||
                                "None"
                            }
                        />


                        <SessionItem
                            label="Topic"
                            value={
                                session.topic ||
                                "None"
                            }
                        />


                        <SessionItem
                            label="Mode"
                            value={
                                session.mode ||
                                "None"
                            }
                        />


                        <SessionItem
                            label="Score"
                            value={
                                session.score ??
                                0
                            }
                        />

                    </div>

                </section>


                {/* =================================================
                    ACTIVITY
                ================================================= */}

                <section
                    className="
                        bg-gray-900
                        border
                        border-gray-800
                        rounded-2xl
                        p-6
                        mb-8
                    "
                >

                    <div
                        className="
                            flex
                            items-center
                            gap-2
                            mb-6
                        "
                    >

                        <MessageSquare
                            size={19}
                            className="
                                text-purple-400
                            "
                        />

                        <h3
                            className="
                                font-semibold
                            "
                        >
                            Recent conversations
                        </h3>

                    </div>


                    {recentConversations.length === 0 ? (

                        <EmptyState
                            text="
                                No conversations available yet.
                            "
                        />

                    ) : (

                        <div
                            className="
                                space-y-2
                            "
                        >

                            {recentConversations.map(
                                conversation => (

                                    <button
                                        key={
                                            conversation.id
                                        }
                                        onClick={() => {

                                            localStorage.setItem(
                                                "nova_current_conversation",
                                                conversation.id
                                            );

                                            navigate(
                                                "/chat"
                                            );

                                        }}
                                        className="
                                            w-full
                                            text-left
                                            p-4
                                            rounded-xl
                                            bg-gray-950
                                            border
                                            border-gray-800
                                            hover:border-gray-700
                                            hover:bg-gray-900
                                            transition
                                        "
                                    >

                                        <div
                                            className="
                                                flex
                                                justify-between
                                                gap-4
                                            "
                                        >

                                            <span
                                                className="
                                                    font-medium
                                                    truncate
                                                "
                                            >
                                                {
                                                    conversation.title ||
                                                    "New Chat"
                                                }
                                            </span>


                                            <span
                                                className="
                                                    text-xs
                                                    text-gray-600
                                                    shrink-0
                                                "
                                            >
                                                {
                                                    conversation.message_count
                                                } messages
                                            </span>

                                        </div>


                                        <p
                                            className="
                                                text-sm
                                                text-gray-500
                                                truncate
                                                mt-1
                                            "
                                        >
                                            {
                                                conversation.last_message ||
                                                "No messages yet"
                                            }
                                        </p>

                                    </button>

                                )
                            )}

                        </div>

                    )}

                </section>


                {/* =================================================
                    FOOTER STATS
                ================================================= */}

                <section
                    className="
                        grid
                        grid-cols-2
                        md:grid-cols-4
                        gap-4
                        pb-10
                    "
                >

                    <FooterStat
                        icon={
                            <Database
                                size={18}
                            />
                        }
                        label="Memory"
                        value={
                            formatNumber(
                                stats.memory_count
                            )
                        }
                    />


                    <FooterStat
                        icon={
                            <MessageSquare
                                size={18}
                            />
                        }
                        label="Conversations"
                        value={
                            formatNumber(
                                stats.conversation_count
                            )
                        }
                    />


                    <FooterStat
                        icon={
                            <Brain
                                size={18}
                            />
                        }
                        label="Understanding checks"
                        value={
                            formatNumber(
                                stats.understanding_attempts
                            )
                        }
                    />


                    <FooterStat
                        icon={
                            <BookOpen
                                size={18}
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

            </main>


            {/* =================================================
                STYLES
            ================================================= */}

            <style>{`

                .nova-dashboard-scroll::-webkit-scrollbar {
                    width: 6px;
                }

                .nova-dashboard-scroll::-webkit-scrollbar-track {
                    background: transparent;
                }

                .nova-dashboard-scroll::-webkit-scrollbar-thumb {
                    background:
                        rgba(
                            75,
                            85,
                            99,
                            0.35
                        );

                    border-radius: 999px;
                }

                .nova-dashboard-scroll {
                    scrollbar-width: thin;
                    scrollbar-color:
                        rgba(
                            75,
                            85,
                            99,
                            0.35
                        )
                        transparent;
                }

            `}</style>

        </div>

    );

}


// ============================================================
// STAT CARD
// ============================================================

function StatCard({
    icon,
    label,
    value
}) {

    return (

        <div
            className="
                bg-gray-900
                border
                border-gray-800
                rounded-2xl
                p-5
            "
        >

            <div
                className="
                    w-10
                    h-10
                    rounded-xl
                    bg-gray-800
                    flex
                    items-center
                    justify-center
                    text-gray-300
                    mb-4
                "
            >
                {icon}
            </div>


            <div
                className="
                    text-2xl
                    font-semibold
                "
            >
                {value}
            </div>


            <div
                className="
                    text-sm
                    text-gray-500
                    mt-1
                "
            >
                {label}
            </div>

        </div>

    );

}


// ============================================================
// MINI STAT
// ============================================================

function MiniStat({
    label,
    value,
    icon
}) {

    return (

        <div
            className="
                bg-gray-950
                border
                border-gray-800
                rounded-xl
                p-3
            "
        >

            <div
                className="
                    flex
                    items-center
                    gap-2
                    text-gray-500
                    text-xs
                    mb-1
                "
            >
                {icon}
                {label}
            </div>


            <div
                className="
                    font-semibold
                "
            >
                {value}
            </div>

        </div>

    );

}


// ============================================================
// SMALL METRIC
// ============================================================

function SmallMetric({
    label,
    value
}) {

    return (

        <div
            className="
                text-center
            "
        >

            <div
                className="
                    text-sm
                    font-semibold
                "
            >
                {value}
            </div>


            <div
                className="
                    text-[11px]
                    text-gray-600
                "
            >
                {label}
            </div>

        </div>

    );

}


// ============================================================
// DIFFICULTY BAR
// ============================================================

function DifficultyBar({
    label,
    value,
    total
}) {

    const percentage =
        total > 0
            ? (
                value /
                total
            ) * 100
            : 0;


    return (

        <div>

            <div
                className="
                    flex
                    justify-between
                    text-sm
                    mb-2
                "
            >

                <span>
                    {label}
                </span>

                <span
                    className="
                        text-gray-500
                    "
                >
                    {value}
                </span>

            </div>


            <div
                className="
                    h-2
                    bg-gray-800
                    rounded-full
                    overflow-hidden
                "
            >

                <div
                    className="
                        h-full
                        bg-orange-500
                        rounded-full
                    "
                    style={{
                        width:
                            `${percentage}%`
                    }}
                />

            </div>

        </div>

    );

}


// ============================================================
// SESSION ITEM
// ============================================================

function SessionItem({
    label,
    value
}) {

    return (

        <div
            className="
                bg-gray-950
                border
                border-gray-800
                rounded-xl
                p-4
            "
        >

            <div
                className="
                    text-xs
                    text-gray-600
                    mb-1
                "
            >
                {label}
            </div>


            <div
                className="
                    text-sm
                    font-medium
                    truncate
                "
                title={
                    String(value)
                }
            >
                {value}
            </div>

        </div>

    );

}


// ============================================================
// FOOTER STAT
// ============================================================

function FooterStat({
    icon,
    label,
    value
}) {

    return (

        <div
            className="
                bg-gray-900
                border
                border-gray-800
                rounded-xl
                p-4
                flex
                items-center
                gap-3
            "
        >

            <div
                className="
                    text-gray-500
                "
            >
                {icon}
            </div>


            <div>

                <div
                    className="
                        font-semibold
                    "
                >
                    {value}
                </div>

                <div
                    className="
                        text-xs
                        text-gray-600
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
    text
}) {

    return (

        <div
            className="
                py-8
                text-center
                text-sm
                text-gray-600
                border
                border-dashed
                border-gray-800
                rounded-xl
            "
        >
            {text}
        </div>

    );

}

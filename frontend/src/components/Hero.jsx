import {
    ArrowRight,
    Sparkles,
    Bot,
    Play,
    BookOpen,
    Brain,
    ShieldCheck,
    Zap,
    ChevronDown
} from "lucide-react";

import {
    useCallback,
    useEffect,
    useMemo,
    useState
} from "react";

import {
    useLocation,
    useNavigate
} from "react-router-dom";


// ============================================================
// CONSTANTS
// ============================================================

const STORAGE_KEYS = {
    USER: "nova_user",
    LAST_ROUTE: "nova_last_route",
    LAST_PAGE: "nova_last_page",
    CURRENT_CONVERSATION:
        "nova_current_conversation"
};


// ============================================================
// SAFE STORAGE
// ============================================================

function getStoredUser() {

    try {

        const raw =
            localStorage.getItem(
                STORAGE_KEYS.USER
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


// ============================================================
// SAFE LAST ROUTE
// ============================================================

function getLastRoute() {

    try {

        const route =
            localStorage.getItem(
                STORAGE_KEYS.LAST_ROUTE
            );

        const page =
            localStorage.getItem(
                STORAGE_KEYS.LAST_PAGE
            );

        const candidate =
            route || page;

        if (
            !candidate ||
            typeof candidate !== "string"
        ) {
            return null;
        }

        if (
            !candidate.startsWith("/")
        ) {
            return null;
        }

        if (
            candidate === "/" ||
            candidate.startsWith("/login") ||
            candidate.startsWith("/register")
        ) {
            return null;
        }

        return candidate;

    } catch {

        return null;

    }

}


// ============================================================
// HERO
// ============================================================

export default function Hero() {

    const navigate =
        useNavigate();

    const location =
        useLocation();


    // ========================================================
    // STATE
    // ========================================================

    const [
        user,
        setUser
    ] = useState(
        getStoredUser
    );


    const [
        activeAction,
        setActiveAction
    ] = useState(null);


    const [
        showMore,
        setShowMore
    ] = useState(false);


    const [
        mousePosition,
        setMousePosition
    ] = useState({
        x: 0,
        y: 0
    });


    const [
        isVisible,
        setIsVisible
    ] = useState(false);


    // ========================================================
    // LOAD USER
    // ========================================================

    const refreshUser =
        useCallback(() => {

            setUser(
                getStoredUser()
            );

        }, []);


    useEffect(() => {

        refreshUser();

        window.addEventListener(
            "storage",
            refreshUser
        );


        /*
         * Same-tab authentication changes do not
         * automatically trigger the storage event.
         *
         * Nova can dispatch this custom event
         * whenever login/logout happens.
         */

        window.addEventListener(
            "nova-auth-change",
            refreshUser
        );


        return () => {

            window.removeEventListener(
                "storage",
                refreshUser
            );

            window.removeEventListener(
                "nova-auth-change",
                refreshUser
            );

        };

    }, [
        refreshUser
    ]);


    // ========================================================
    // HERO INTRO
    // ========================================================

    useEffect(() => {

        const timer =
            requestAnimationFrame(() => {

                setIsVisible(true);

            });


        return () => {

            cancelAnimationFrame(
                timer
            );

        };

    }, []);


    // ========================================================
    // MOUSE PARALLAX
    // ========================================================

    useEffect(() => {

        const mediaQuery =
            window.matchMedia(
                "(prefers-reduced-motion: reduce)"
            );


        if (mediaQuery.matches) {
            return undefined;
        }


        let frame = null;


        function handlePointerMove(event) {

            if (frame) {
                cancelAnimationFrame(frame);
            }


            frame =
                requestAnimationFrame(() => {

                    const x =
                        (
                            event.clientX /
                            window.innerWidth
                        ) - 0.5;


                    const y =
                        (
                            event.clientY /
                            window.innerHeight
                        ) - 0.5;


                    setMousePosition({
                        x,
                        y
                    });

                });

        }


        window.addEventListener(
            "pointermove",
            handlePointerMove,
            {
                passive: true
            }
        );


        return () => {

            window.removeEventListener(
                "pointermove",
                handlePointerMove
            );


            if (frame) {

                cancelAnimationFrame(
                    frame
                );

            }

        };

    }, []);


    // ========================================================
    // LAST ROUTE
    // ========================================================

    const lastRoute =
        useMemo(
            () => getLastRoute(),
            [
                user,
                location.pathname
            ]
        );


    // ========================================================
    // USER DISPLAY NAME
    // ========================================================

    const userLabel =
        useMemo(() => {

            if (!user) {
                return null;
            }


            if (
                user.name &&
                typeof user.name === "string"
            ) {

                return user.name;

            }


            if (
                user.username &&
                typeof user.username === "string"
            ) {

                return user.username;

            }


            if (
                user.email &&
                typeof user.email === "string"
            ) {

                return user.email
                    .split("@")[0];

            }


            return "Student";

        }, [
            user
        ]);


    // ========================================================
    // START LEARNING
    // ========================================================

    const startLearning =
        useCallback(() => {

            setActiveAction(
                "start"
            );

            navigate(
                "/login"
            );

        }, [
            navigate
        ]);


    // ========================================================
    // OPEN DEMO
    // ========================================================

    const openDemo =
        useCallback(() => {

            setActiveAction(
                "demo"
            );

            navigate(
                "/chat?demo=true"
            );

        }, [
            navigate
        ]);


    // ========================================================
    // CONTINUE LEARNING
    // ========================================================

    const continueLearning =
        useCallback(() => {

            setActiveAction(
                "continue"
            );


            if (lastRoute) {

                navigate(
                    lastRoute
                );

                return;

            }


            navigate(
                "/chat"
            );

        }, [
            lastRoute,
            navigate
        ]);


    // ========================================================
    // NEW LEARNING SESSION
    // ========================================================

    const startFresh =
        useCallback(() => {

            setActiveAction(
                "new"
            );


            /*
             * The current Chat implementation already
             * understands nova_current_conversation.
             *
             * Removing it guarantees that the next
             * Chat page starts a fresh conversation.
             */

            try {

                localStorage.removeItem(
                    STORAGE_KEYS.CURRENT_CONVERSATION
                );

            } catch {
                // Storage can fail in restricted browsers.
            }


            navigate(
                "/chat"
            );

        }, [
            navigate
        ]);


    // ========================================================
    // OPEN DASHBOARD
    // ========================================================

    const openDashboard =
        useCallback(() => {

            setActiveAction(
                "dashboard"
            );

            navigate(
                "/dashboard"
            );

        }, [
            navigate
        ]);


    // ========================================================
    // SCROLL TO FEATURES
    // ========================================================

    const scrollToFeatures =
        useCallback(() => {

            const element =
                document.getElementById(
                    "features"
                );


            if (!element) {
                return;
            }


            element.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        }, []);


    // ========================================================
    // KEYBOARD SHORTCUT
    // ========================================================

    useEffect(() => {

        function handleKeyDown(event) {

            if (
                event.key === "Escape"
            ) {

                setShowMore(false);

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
    // BUTTON COMPONENT
    // ========================================================

    function ActionButton({
        action,
        onClick,
        children,
        icon: Icon,
        primary = false
    }) {

        const loading =
            activeAction === action;


        return (

            <button
                type="button"
                onClick={onClick}
                disabled={Boolean(activeAction)}
                aria-label={
                    typeof children === "string"
                        ? children
                        : undefined
                }
                className={`
                    group
                    relative
                    inline-flex
                    items-center
                    justify-center
                    gap-3
                    overflow-hidden
                    rounded-2xl
                    px-7
                    py-4
                    font-semibold
                    transition-all
                    duration-300
                    disabled:cursor-wait
                    disabled:opacity-70
                    focus:outline-none
                    focus-visible:ring-2
                    focus-visible:ring-blue-400
                    focus-visible:ring-offset-2
                    focus-visible:ring-offset-slate-950

                    ${
                        primary
                            ? `
                                bg-blue-600
                                text-white
                                shadow-xl
                                shadow-blue-950/40
                                hover:bg-blue-500
                                hover:-translate-y-1
                                hover:shadow-blue-900/50
                            `
                            : `
                                border
                                border-slate-700/80
                                bg-slate-900/60
                                text-slate-200
                                backdrop-blur-xl
                                hover:bg-slate-800
                                hover:border-slate-600
                                hover:text-white
                                hover:-translate-y-1
                            `
                    }
                `}
            >

                {primary && (

                    <span
                        aria-hidden="true"
                        className="
                            absolute
                            inset-0
                            -translate-x-full
                            bg-gradient-to-r
                            from-transparent
                            via-white/10
                            to-transparent
                            transition-transform
                            duration-700
                            group-hover:translate-x-full
                        "
                    />

                )}


                <span
                    className="
                        relative
                        flex
                        items-center
                        gap-3
                    "
                >

                    {loading ? (

                        <span
                            className="
                                h-5
                                w-5
                                rounded-full
                                border-2
                                border-current
                                border-t-transparent
                                animate-spin
                            "
                        />

                    ) : (

                        <Icon
                            size={19}
                            strokeWidth={2}
                            className="
                                transition-transform
                                duration-300
                                group-hover:scale-110
                            "
                        />

                    )}


                    {children}

                    {!loading && primary && (

                        <ArrowRight
                            size={18}
                            className="
                                transition-transform
                                duration-300
                                group-hover:translate-x-1
                            "
                        />

                    )}

                </span>

            </button>

        );

    }


    // ========================================================
    // RENDER
    // ========================================================

    return (

        <section
            className={`
                relative
                isolate
                min-h-[680px]
                md:min-h-[760px]
                flex
                items-center
                justify-center
                overflow-hidden
                bg-slate-950
                text-white
                ${
                    isVisible
                        ? "nova-hero-visible"
                        : ""
                }
            `}
            aria-labelledby="nova-hero-title"
        >

            {/* ==================================================
                BACKGROUND
            ================================================== */}

            <div
                aria-hidden="true"
                className="
                    absolute
                    inset-0
                    pointer-events-none
                    overflow-hidden
                "
            >

                {/* Main glow */}

                <div
                    className="
                        absolute
                        left-1/2
                        top-[-180px]
                        h-[520px]
                        w-[760px]
                        -translate-x-1/2
                        rounded-full
                        bg-blue-600/10
                        blur-[130px]
                    "
                />


                {/* Secondary glow */}

                <div
                    className="
                        absolute
                        -left-32
                        top-1/3
                        h-72
                        w-72
                        rounded-full
                        bg-indigo-500/10
                        blur-[110px]
                        nova-float-left
                    "
                />


                <div
                    className="
                        absolute
                        -right-32
                        bottom-1/4
                        h-80
                        w-80
                        rounded-full
                        bg-cyan-500/5
                        blur-[120px]
                        nova-float-right
                    "
                />


                {/* Grid */}

                <div
                    className="
                        absolute
                        inset-0
                        opacity-[0.035]
                        nova-grid
                    "
                />


                {/* Top radial light */}

                <div
                    className="
                        absolute
                        inset-x-0
                        top-0
                        h-96
                        bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.08),transparent_65%)]
                    "
                />


                {/* Parallax orb */}

                <div
                    className="
                        absolute
                        left-1/2
                        top-1/2
                        h-64
                        w-64
                        rounded-full
                        border
                        border-blue-400/5
                        transition-transform
                        duration-700
                        ease-out
                    "
                    style={{
                        transform: `
                            translate(
                                ${mousePosition.x * 35}px,
                                ${mousePosition.y * 35}px
                            )
                        `
                    }}
                />


                <div
                    className="
                        absolute
                        left-1/2
                        top-1/2
                        h-96
                        w-96
                        rounded-full
                        border
                        border-blue-400/[0.025]
                        transition-transform
                        duration-1000
                        ease-out
                    "
                    style={{
                        transform: `
                            translate(
                                ${mousePosition.x * -20}px,
                                ${mousePosition.y * -20}px
                            )
                        `
                    }}
                />

            </div>


            {/* ==================================================
                CONTENT
            ================================================== */}

            <div
                className="
                    relative
                    z-10
                    mx-auto
                    w-full
                    max-w-6xl
                    px-6
                    py-24
                    md:py-32
                "
            >

                <div
                    className="
                        mx-auto
                        max-w-4xl
                        text-center
                    "
                >

                    {/* ==================================================
                        BADGE
                    ================================================== */}

                    <div
                        className="
                            nova-hero-item
                            nova-delay-1
                            inline-flex
                            items-center
                            gap-2
                            rounded-full
                            border
                            border-blue-400/15
                            bg-blue-500/[0.06]
                            px-4
                            py-2
                            text-sm
                            font-medium
                            text-blue-300
                            shadow-lg
                            shadow-blue-950/10
                            backdrop-blur-xl
                        "
                    >

                        <span
                            className="
                                relative
                                flex
                                h-2
                                w-2
                            "
                        >

                            <span
                                className="
                                    absolute
                                    inline-flex
                                    h-full
                                    w-full
                                    animate-ping
                                    rounded-full
                                    bg-blue-400
                                    opacity-60
                                "
                            />

                            <span
                                className="
                                    relative
                                    inline-flex
                                    h-2
                                    w-2
                                    rounded-full
                                    bg-blue-400
                                "
                            />

                        </span>


                        <Sparkles
                            size={15}
                        />

                        AI-powered learning

                    </div>


                    {/* ==================================================
                        LOGO
                    ================================================== */}

                    <div
                        className="
                            nova-hero-item
                            nova-delay-2
                            mt-8
                            flex
                            justify-center
                        "
                    >

                        <div
                            className="
                                relative
                                flex
                                h-24
                                w-24
                                items-center
                                justify-center
                            "
                        >

                            <div
                                className="
                                    absolute
                                    inset-0
                                    rounded-[30px]
                                    bg-blue-500/10
                                    blur-2xl
                                    nova-logo-glow
                                "
                            />

                            <div
                                className="
                                    relative
                                    flex
                                    h-20
                                    w-20
                                    items-center
                                    justify-center
                                    rounded-[26px]
                                    border
                                    border-blue-400/10
                                    bg-slate-900/70
                                    shadow-2xl
                                    shadow-blue-950/30
                                    backdrop-blur-xl
                                "
                            >

                                <Bot
                                    size={52}
                                    strokeWidth={1.35}
                                    className="
                                        text-blue-400
                                    "
                                />

                            </div>

                        </div>

                    </div>


                    {/* ==================================================
                        TITLE
                    ================================================== */}

                    <h1
                        id="nova-hero-title"
                        className="
                            nova-hero-item
                            nova-delay-3
                            mt-6
                            text-5xl
                            font-bold
                            leading-[1.02]
                            tracking-[-0.04em]
                            text-slate-100
                            sm:text-6xl
                            md:text-7xl
                            lg:text-8xl
                        "
                    >

                        Learn smarter.

                        <span
                            className="
                                mt-2
                                block
                                bg-gradient-to-r
                                from-blue-300
                                via-blue-500
                                to-indigo-400
                                bg-clip-text
                                text-transparent
                            "
                        >
                            With Nova AI.
                        </span>

                    </h1>


                    {/* ==================================================
                        DESCRIPTION
                    ================================================== */}

                    <p
                        className="
                            nova-hero-item
                            nova-delay-4
                            mx-auto
                            mt-8
                            max-w-2xl
                            text-base
                            leading-7
                            text-slate-400
                            sm:text-lg
                            sm:leading-8
                        "
                    >

                        Nova is an adaptive AI tutor designed
                        to explain difficult concepts, guide
                        your reasoning, and help you actually
                        understand what you're studying.

                    </p>


                    {/* ==================================================
                        ACTIONS
                    ================================================== */}

                    <div
                        className="
                            nova-hero-item
                            nova-delay-5
                            mt-10
                            flex
                            flex-col
                            items-stretch
                            justify-center
                            gap-3
                            sm:flex-row
                            sm:items-center
                        "
                    >

                        {!user ? (

                            <>

                                <ActionButton
                                    action="start"
                                    onClick={
                                        startLearning
                                    }
                                    icon={BookOpen}
                                    primary
                                >
                                    Start Learning
                                </ActionButton>


                                <ActionButton
                                    action="demo"
                                    onClick={
                                        openDemo
                                    }
                                    icon={Play}
                                >
                                    Try Nova Demo
                                </ActionButton>

                            </>

                        ) : (

                            <>

                                <ActionButton
                                    action="continue"
                                    onClick={
                                        continueLearning
                                    }
                                    icon={Zap}
                                    primary
                                >
                                    Continue Learning
                                </ActionButton>


                                <ActionButton
                                    action="new"
                                    onClick={
                                        startFresh
                                    }
                                    icon={Sparkles}
                                >
                                    Start Something New
                                </ActionButton>

                            </>

                        )}

                    </div>


                    {/* ==================================================
                        ACCOUNT STATUS
                    ================================================== */}

                    {user && (

                        <div
                            className="
                                nova-hero-item
                                nova-delay-6
                                mt-5
                                flex
                                flex-wrap
                                items-center
                                justify-center
                                gap-x-3
                                gap-y-2
                                text-xs
                                text-slate-500
                            "
                        >

                            <span>
                                Welcome back,{" "}
                                <span
                                    className="
                                        text-slate-300
                                    "
                                >
                                    {userLabel}
                                </span>
                            </span>


                            <span
                                className="
                                    hidden
                                    h-1
                                    w-1
                                    rounded-full
                                    bg-slate-700
                                    sm:block
                                "
                            />


                            <button
                                type="button"
                                onClick={
                                    openDashboard
                                }
                                className="
                                    text-blue-400
                                    transition
                                    hover:text-blue-300
                                "
                            >
                                Open dashboard
                            </button>

                        </div>

                    )}


                    {/* ==================================================
                        TRUST SIGNALS
                    ================================================== */}

                    <div
                        className="
                            nova-hero-item
                            nova-delay-7
                            mt-12
                            flex
                            flex-wrap
                            items-center
                            justify-center
                            gap-x-6
                            gap-y-3
                            text-xs
                            text-slate-500
                        "
                    >

                        <div
                            className="
                                flex
                                items-center
                                gap-2
                            "
                        >

                            <Brain
                                size={15}
                                className="
                                    text-slate-400
                                "
                            />

                            Adaptive explanations

                        </div>


                        <div
                            className="
                                hidden
                                h-3
                                w-px
                                bg-slate-800
                                sm:block
                            "
                        />


                        <div
                            className="
                                flex
                                items-center
                                gap-2
                            "
                        >

                            <ShieldCheck
                                size={15}
                                className="
                                    text-slate-400
                                "
                            />

                            Personalized learning

                        </div>


                        <div
                            className="
                                hidden
                                h-3
                                w-px
                                sm:block
                            "
                        />


                        <div
                            className="
                                flex
                                items-center
                                gap-2
                            "
                        >

                            <Zap
                                size={15}
                                className="
                                    text-slate-400
                                "
                            />

                            Built for students

                        </div>

                    </div>


                    {/* ==================================================
                        MORE INFO
                    ================================================== */}

                    <div
                        className="
                            nova-hero-item
                            nova-delay-8
                            mt-10
                        "
                    >

                        <button
                            type="button"
                            onClick={() =>
                                setShowMore(
                                    previous =>
                                        !previous
                                )
                            }
                            aria-expanded={
                                showMore
                            }
                            className="
                                inline-flex
                                items-center
                                gap-2
                                rounded-full
                                px-4
                                py-2
                                text-xs
                                text-slate-500
                                transition
                                hover:bg-slate-900
                                hover:text-slate-300
                                focus:outline-none
                                focus-visible:ring-2
                                focus-visible:ring-blue-400
                            "
                        >

                            Learn more about Nova

                            <ChevronDown
                                size={14}
                                className={`
                                    transition-transform
                                    duration-300
                                    ${
                                        showMore
                                            ? "rotate-180"
                                            : ""
                                    }
                                `}
                            />

                        </button>


                        {showMore && (

                            <div
                                className="
                                    mx-auto
                                    mt-4
                                    max-w-2xl
                                    rounded-2xl
                                    border
                                    border-slate-800
                                    bg-slate-900/60
                                    p-5
                                    text-left
                                    text-sm
                                    leading-6
                                    text-slate-400
                                    shadow-2xl
                                    shadow-black/20
                                    backdrop-blur-xl
                                    nova-more-panel
                                "
                            >

                                <div
                                    className="
                                        grid
                                        gap-4
                                        sm:grid-cols-3
                                    "
                                >

                                    <div>

                                        <Brain
                                            size={18}
                                            className="
                                                mb-2
                                                text-blue-400
                                            "
                                        />

                                        <div
                                            className="
                                                font-medium
                                                text-slate-200
                                            "
                                        >
                                            Understand
                                        </div>

                                        <p
                                            className="
                                                mt-1
                                                text-xs
                                                text-slate-500
                                            "
                                        >
                                            Explanations can
                                            adapt to what you
                                            already know.
                                        </p>

                                    </div>


                                    <div>

                                        <Zap
                                            size={18}
                                            className="
                                                mb-2
                                                text-blue-400
                                            "
                                        />

                                        <div
                                            className="
                                                font-medium
                                                text-slate-200
                                            "
                                        >
                                            Practice
                                        </div>

                                        <p
                                            className="
                                                mt-1
                                                text-xs
                                                text-slate-500
                                            "
                                        >
                                            Work through
                                            problems instead of
                                            only reading answers.
                                        </p>

                                    </div>


                                    <div>

                                        <ShieldCheck
                                            size={18}
                                            className="
                                                mb-2
                                                text-blue-400
                                            "
                                        />

                                        <div
                                            className="
                                                font-medium
                                                text-slate-200
                                            "
                                        >
                                            Improve
                                        </div>

                                        <p
                                            className="
                                                mt-1
                                                text-xs
                                                text-slate-500
                                            "
                                        >
                                            Keep your learning
                                            experience organized
                                            across sessions.
                                        </p>

                                    </div>

                                </div>

                            </div>

                        )}

                    </div>

                </div>


                {/* ==================================================
                    SCROLL INDICATOR
                ================================================== */}

                <button
                    type="button"
                    onClick={
                        scrollToFeatures
                    }
                    aria-label="Explore Nova features"
                    className="
                        nova-scroll-indicator
                        absolute
                        bottom-8
                        left-1/2
                        hidden
                        -translate-x-1/2
                        flex-col
                        items-center
                        gap-2
                        text-slate-600
                        transition
                        hover:text-slate-400
                        md:flex
                    "
                >

                    <span
                        className="
                            text-[10px]
                            uppercase
                            tracking-[0.2em]
                        "
                    >
                        Explore
                    </span>

                    <span
                        className="
                            flex
                            h-8
                            w-5
                            items-start
                            justify-center
                            rounded-full
                            border
                            border-slate-700
                            p-1
                        "
                    >

                        <span
                            className="
                                h-1.5
                                w-1
                                rounded-full
                                bg-slate-500
                                nova-scroll-dot
                            "
                        />

                    </span>

                </button>

            </div>


            {/* ==================================================
                BOTTOM FADE
            ================================================== */}

            <div
                aria-hidden="true"
                className="
                    absolute
                    bottom-0
                    left-0
                    right-0
                    h-32
                    bg-gradient-to-t
                    from-slate-950
                    to-transparent
                    pointer-events-none
                "
            />


            {/* ==================================================
                STYLES
            ================================================== */}

            <style>{`

                /* ================================================
                   HERO ENTRY
                ================================================= */

                .nova-hero-item {

                    opacity: 0;

                    transform:
                        translateY(28px)
                        scale(0.985);

                    transition:
                        opacity 0.85s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        ),
                        transform 0.85s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        );

                }


                .nova-hero-visible
                .nova-hero-item {

                    opacity: 1;

                    transform:
                        translateY(0)
                        scale(1);

                }


                .nova-delay-1 {
                    transition-delay: 0.05s;
                }


                .nova-delay-2 {
                    transition-delay: 0.11s;
                }


                .nova-delay-3 {
                    transition-delay: 0.17s;
                }


                .nova-delay-4 {
                    transition-delay: 0.25s;
                }


                .nova-delay-5 {
                    transition-delay: 0.33s;
                }


                .nova-delay-6 {
                    transition-delay: 0.42s;
                }


                .nova-delay-7 {
                    transition-delay: 0.5s;
                }


                .nova-delay-8 {
                    transition-delay: 0.58s;
                }


                /* ================================================
                   GRID
                ================================================= */

                .nova-grid {

                    background-image:
                        linear-gradient(
                            rgba(
                                148,
                                163,
                                184,
                                0.4
                            )
                            1px,
                            transparent 1px
                        ),
                        linear-gradient(
                            90deg,
                            rgba(
                                148,
                                163,
                                184,
                                0.4
                            )
                            1px,
                            transparent 1px
                        );

                    background-size:
                        64px 64px;

                    mask-image:
                        radial-gradient(
                            ellipse at center,
                            black 0%,
                            transparent 72%
                        );

                }


                /* ================================================
                   BACKGROUND FLOAT
                ================================================= */

                .nova-float-left {

                    animation:
                        novaFloatLeft
                        9s
                        ease-in-out
                        infinite;

                }


                @keyframes novaFloatLeft {

                    0%,
                    100% {

                        transform:
                            translate3d(
                                0,
                                0,
                                0
                            );

                    }

                    50% {

                        transform:
                            translate3d(
                                35px,
                                -28px,
                                0
                            );

                    }

                }


                .nova-float-right {

                    animation:
                        novaFloatRight
                        11s
                        ease-in-out
                        infinite;

                }


                @keyframes novaFloatRight {

                    0%,
                    100% {

                        transform:
                            translate3d(
                                0,
                                0,
                                0
                            );

                    }

                    50% {

                        transform:
                            translate3d(
                                -30px,
                                32px,
                                0
                            );

                    }

                }


                /* ================================================
                   LOGO
                ================================================= */

                .nova-logo-glow {

                    animation:
                        novaLogoPulse
                        4s
                        ease-in-out
                        infinite;

                }


                @keyframes novaLogoPulse {

                    0%,
                    100% {

                        opacity: 0.45;

                        transform:
                            scale(0.9);

                    }

                    50% {

                        opacity: 0.8;

                        transform:
                            scale(1.08);

                    }

                }


                /* ================================================
                   MORE PANEL
                ================================================= */

                .nova-more-panel {

                    animation:
                        novaMorePanel
                        0.35s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        );

                    transform-origin:
                        top center;

                }


                @keyframes novaMorePanel {

                    from {

                        opacity: 0;

                        transform:
                            translateY(-8px)
                            scale(0.98);

                    }

                    to {

                        opacity: 1;

                        transform:
                            translateY(0)
                            scale(1);

                    }

                }


                /* ================================================
                   SCROLL DOT
                ================================================= */

                .nova-scroll-dot {

                    animation:
                        novaScrollDot
                        1.8s
                        ease-in-out
                        infinite;

                }


                @keyframes novaScrollDot {

                    0% {

                        opacity: 0.4;

                        transform:
                            translateY(0);

                    }

                    50% {

                        opacity: 1;

                        transform:
                            translateY(10px);

                    }

                    100% {

                        opacity: 0.4;

                        transform:
                            translateY(0);

                    }

                }


                /* ================================================
                   REDUCED MOTION
                ================================================= */

                @media (
                    prefers-reduced-motion: reduce
                ) {

                    .nova-hero-item {

                        opacity: 1;

                        transform:
                            none;

                        transition:
                            none;

                    }


                    .nova-float-left,
                    .nova-float-right,
                    .nova-logo-glow,
                    .nova-scroll-dot {

                        animation: none;

                    }

                }


                /* ================================================
                   MOBILE
                ================================================= */

                @media (
                    max-width: 640px
                ) {

                    .nova-grid {

                        background-size:
                            44px 44px;

                    }

                }

            `}</style>

        </section>

    );

}
import React, {
    Suspense,
    lazy,
    useCallback,
    useEffect,
    useRef,
    useState
} from "react";

import {
    BrowserRouter,
    Routes,
    Route,
    useLocation,
    useNavigate,
    useNavigationType
} from "react-router-dom";

import {
    AlertTriangle,
    LoaderCircle,
    RefreshCw,
    Wifi,
    WifiOff
} from "lucide-react";


// ============================================================
// LAZY PAGE LOADING
// ============================================================
//
// Loading pages lazily keeps the initial frontend bundle smaller.
//
// ============================================================

const Home = lazy(
    () => import("./pages/Home")
);

const Chat = lazy(
    () => import("./pages/Chat")
);

const Dashboard = lazy(
    () => import("./pages/Dashboard")
);

const Login = lazy(
    () => import("./pages/Login")
);

const Register = lazy(
    () => import("./pages/Register")
);

const Settings = lazy(
    () => import("./pages/Settings")
);

const NotFound = lazy(
    () => import("./pages/NotFound")
);


// ============================================================
// CONSTANTS
// ============================================================

const APP_NAME = "Nova AI";

const STORAGE_KEYS = {
    LAST_ROUTE: "nova_last_route",
    THEME: "nova_theme",
    SIDEBAR: "nova_sidebar_state"
};

const LEARNING_ROUTES = [
    "/chat",
    "/dashboard"
];

const PAGE_TITLES = {
    "/": "Nova AI",
    "/chat": "Chat",
    "/dashboard": "Dashboard",
    "/settings": "Settings",
    "/login": "Login",
    "/register": "Create Account"
};


// ============================================================
// SAFE STORAGE
// ============================================================

function safeStorageGet(key) {
    try {
        return localStorage.getItem(key);
    } catch {
        return null;
    }
}


function safeStorageSet(key, value) {
    try {
        localStorage.setItem(
            key,
            value
        );

        return true;
    } catch {
        return false;
    }
}


// ============================================================
// ERROR BOUNDARY
// ============================================================

class NovaErrorBoundary extends React.Component {

    constructor(props) {

        super(props);

        this.state = {
            hasError: false,
            error: null
        };
    }


    static getDerivedStateFromError(error) {

        return {
            hasError: true,
            error
        };
    }


    componentDidCatch(error, errorInfo) {

        console.error(
            "Nova frontend error:",
            error
        );

        console.error(
            "Nova component stack:",
            errorInfo
        );
    }


    handleReload = () => {

        window.location.reload();
    };


    handleReset = () => {

        this.setState({
            hasError: false,
            error: null
        });
    };


    render() {

        if (!this.state.hasError) {

            return this.props.children;
        }


        return (

            <div
                className="
                    min-h-screen
                    bg-slate-950
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
                        max-w-lg
                        rounded-3xl
                        border
                        border-white/10
                        bg-white/[0.04]
                        p-8
                        shadow-2xl
                    "
                >

                    <div
                        className="
                            flex
                            h-14
                            w-14
                            items-center
                            justify-center
                            rounded-2xl
                            bg-red-500/10
                            text-red-400
                        "
                    >

                        <AlertTriangle
                            size={26}
                        />

                    </div>


                    <h1
                        className="
                            mt-6
                            text-2xl
                            font-semibold
                        "
                    >

                        Nova encountered an error.

                    </h1>


                    <p
                        className="
                            mt-3
                            text-sm
                            leading-6
                            text-slate-400
                        "
                    >

                        Something went wrong while rendering
                        this part of the application.

                    </p>


                    <div
                        className="
                            mt-6
                            flex
                            gap-3
                            flex-wrap
                        "
                    >

                        <button
                            type="button"
                            onClick={this.handleReset}
                            className="
                                inline-flex
                                items-center
                                gap-2
                                rounded-xl
                                bg-white
                                px-4
                                py-2.5
                                text-sm
                                font-medium
                                text-slate-950
                                transition
                                hover:bg-slate-200
                            "
                        >

                            <RefreshCw
                                size={16}
                            />

                            Try again

                        </button>


                        <button
                            type="button"
                            onClick={this.handleReload}
                            className="
                                inline-flex
                                items-center
                                gap-2
                                rounded-xl
                                border
                                border-white/10
                                bg-white/5
                                px-4
                                py-2.5
                                text-sm
                                font-medium
                                text-white
                                transition
                                hover:bg-white/10
                            "
                        >

                            Reload

                        </button>

                    </div>

                </div>

            </div>
        );
    }
}


// ============================================================
// PAGE LOADER
// ============================================================

function PageLoader() {

    return (

        <div
            className="
                min-h-screen
                bg-slate-950
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
                "
            >

                <div
                    className="
                        flex
                        h-14
                        w-14
                        items-center
                        justify-center
                        rounded-2xl
                        bg-white/5
                        border
                        border-white/10
                    "
                >

                    <LoaderCircle
                        size={25}
                        className="animate-spin"
                    />

                </div>


                <div
                    className="
                        text-sm
                        text-slate-400
                    "
                >

                    Loading Nova...

                </div>

            </div>

        </div>
    );
}


// ============================================================
// OFFLINE INDICATOR
// ============================================================

function NetworkStatus() {

    const [
        online,
        setOnline
    ] = useState(
        navigator.onLine
    );

    const [
        visible,
        setVisible
    ] = useState(false);


    useEffect(() => {

        let timer = null;


        const handleOnline = () => {

            setOnline(true);

            setVisible(true);

            timer = setTimeout(
                () => setVisible(false),
                2500
            );
        };


        const handleOffline = () => {

            setOnline(false);

            setVisible(true);
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

            if (timer) {
                clearTimeout(timer);
            }
        };

    }, []);


    if (!visible) {

        return null;
    }


    return (

        <div
            className="
                fixed
                bottom-5
                left-1/2
                z-[9999]
                -translate-x-1/2
            "
        >

            <div
                className={`
                    flex
                    items-center
                    gap-2
                    rounded-full
                    border
                    px-4
                    py-2.5
                    text-sm
                    shadow-xl
                    backdrop-blur-xl

                    ${
                        online
                            ? "border-emerald-400/20 bg-emerald-500/10 text-emerald-300"
                            : "border-red-400/20 bg-red-500/10 text-red-300"
                    }
                `}
            >

                {
                    online
                        ? <Wifi size={15} />
                        : <WifiOff size={15} />
                }

                {
                    online
                        ? "Connection restored"
                        : "You're offline"
                }

            </div>

        </div>
    );
}


// ============================================================
// ROUTE MEMORY
// ============================================================

function RouteMemory() {

    const location =
        useLocation();


    useEffect(() => {

        const pathname =
            location.pathname;

        const currentRoute =
            pathname +
            location.search;


        const shouldRemember =
            LEARNING_ROUTES.some(
                route =>
                    pathname === route
            );


        if (shouldRemember) {

            safeStorageSet(
                STORAGE_KEYS.LAST_ROUTE,
                currentRoute
            );
        }

    }, [
        location.pathname,
        location.search
    ]);


    return null;
}


// ============================================================
// SCROLL RESTORATION
// ============================================================

function ScrollRestoration() {

    const location =
        useLocation();


    useEffect(() => {

        window.scrollTo({
            top: 0,
            left: 0,
            behavior: "instant"
        });

    }, [
        location.pathname
    ]);


    return null;
}


// ============================================================
// DOCUMENT TITLE
// ============================================================

function DocumentManager() {

    const location =
        useLocation();


    useEffect(() => {

        const pathname =
            location.pathname;


        const title =
            PAGE_TITLES[pathname] ||
            "Nova AI";


        document.title =
            title === "Nova AI"
                ? APP_NAME
                : `${title} | ${APP_NAME}`;


        const description =
            document.querySelector(
                'meta[name="description"]'
            );


        if (description) {

            description.setAttribute(
                "content",
                "Nova AI, an adaptive educational tutor."
            );
        }

    }, [
        location.pathname
    ]);


    return null;
}


// ============================================================
// PAGE TRANSITION
// ============================================================

function PageTransition({
    children
}) {

    const location =
        useLocation();

    const navigationType =
        useNavigationType();


    const previousPath =
        useRef(
            location.pathname
        );


    const [
        animate,
        setAnimate
    ] = useState(false);


    const [
        direction,
        setDirection
    ] = useState(
        "forward"
    );


    const firstRender =
        useRef(true);


    useEffect(() => {

        if (firstRender.current) {

            firstRender.current =
                false;

            previousPath.current =
                location.pathname;

            return;
        }


        const oldPath =
            previousPath.current;


        const newPath =
            location.pathname;


        if (
            navigationType === "POP" ||
            (
                newPath === "/" &&
                oldPath !== "/"
            )
        ) {

            setDirection(
                "back"
            );

        } else {

            setDirection(
                "forward"
            );
        }


        previousPath.current =
            newPath;


        setAnimate(true);


        const timer =
            setTimeout(
                () => {
                    setAnimate(false);
                },
                620
            );


        return () => {

            clearTimeout(
                timer
            );
        };

    }, [
        location.pathname,
        location.search,
        navigationType
    ]);


    return (

        <div
            className={`
                nova-page

                ${
                    animate
                        ? direction === "back"
                            ? "nova-transition-back"
                            : "nova-transition-forward"
                        : ""
                }
            `}
        >

            {children}

        </div>
    );
}


// ============================================================
// GLOBAL KEYBOARD SHORTCUTS
// ============================================================

function KeyboardShortcuts() {

    const navigate =
        useNavigate();


    const location =
        useLocation();


    const handleKeyDown =
        useCallback(
            event => {

                const target =
                    event.target;


                const isTyping =
                    target instanceof
                        HTMLInputElement ||
                    target instanceof
                        HTMLTextAreaElement ||
                    target instanceof
                        HTMLSelectElement ||
                    target?.isContentEditable;


                if (isTyping) {

                    return;
                }


                const modifier =
                    event.ctrlKey ||
                    event.metaKey;


                // Ctrl/Cmd + K
                // Focus chat.

                if (
                    modifier &&
                    event.key.toLowerCase() === "k"
                ) {

                    event.preventDefault();

                    navigate(
                        "/chat"
                    );

                    return;
                }


                // Alt + Left

                if (
                    event.altKey &&
                    event.key === "ArrowLeft"
                ) {

                    event.preventDefault();

                    window.history.back();

                    return;
                }


                // Alt + Right

                if (
                    event.altKey &&
                    event.key === "ArrowRight"
                ) {

                    event.preventDefault();

                    window.history.forward();

                    return;
                }


                // Escape

                if (
                    event.key === "Escape"
                ) {

                    if (
                        location.pathname !== "/"
                    ) {

                        // Deliberately do not navigate.
                        // Escape is reserved for page-level
                        // overlays and modals.
                    }
                }

            },
            [
                navigate,
                location.pathname
            ]
        );


    useEffect(() => {

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
        handleKeyDown
    ]);


    return null;
}


// ============================================================
// APP STATUS
// ============================================================

function AppStatus() {

    const [
        status,
        setStatus
    ] = useState(
        "ready"
    );


    useEffect(() => {

        let mounted = true;


        const checkBackend =
            async () => {

                try {

                    const response =
                        await fetch(
                            "http://127.0.0.1:8000/",
                            {
                                method: "GET",
                                signal:
                                    AbortSignal.timeout(
                                        2500
                                    )
                            }
                        );


                    if (!mounted) {

                        return;
                    }


                    if (response.ok) {

                        setStatus(
                            "online"
                        );

                    } else {

                        setStatus(
                            "degraded"
                        );
                    }

                } catch {

                    if (mounted) {

                        setStatus(
                            "offline"
                        );
                    }
                }
            };


        checkBackend();


        return () => {

            mounted = false;
        };

    }, []);


    // Status is currently used only to track
    // backend availability internally.

    void status;

    return null;
}


// ============================================================
// ROUTE HELPERS
// ============================================================

function RouteLoadingFallback() {

    return (
        <PageLoader />
    );
}


// ============================================================
// APP CONTENT
// ============================================================

function AppContent() {

    return (

        <>

            <RouteMemory />

            <ScrollRestoration />

            <DocumentManager />

            <KeyboardShortcuts />

            <AppStatus />

            <NetworkStatus />


            <PageTransition>

                <Suspense
                    fallback={
                        <RouteLoadingFallback />
                    }
                >

                    <Routes>

                        {/* ================================== */}
                        {/* HOME */}
                        {/* ================================== */}

                        <Route
                            path="/"
                            element={
                                <Home />
                            }
                        />


                        {/* ================================== */}
                        {/* CHAT */}
                        {/* ================================== */}

                        <Route
                            path="/chat"
                            element={
                                <Chat />
                            }
                        />


                        {/* ================================== */}
                        {/* DASHBOARD */}
                        {/* ================================== */}

                        <Route
                            path="/dashboard"
                            element={
                                <Dashboard />
                            }
                        />


                        {/* ================================== */}
                        {/* SETTINGS */}
                        {/* ================================== */}

                        <Route
                            path="/settings"
                            element={
                                <Settings />
                            }
                        />


                        {/* ================================== */}
                        {/* AUTH */}
                        {/* ================================== */}

                        <Route
                            path="/login"
                            element={
                                <Login />
                            }
                        />

                        <Route
                            path="/register"
                            element={
                                <Register />
                            }
                        />


                        {/* ================================== */}
                        {/* 404 */}
                        {/* ================================== */}

                        <Route
                            path="*"
                            element={
                                <NotFound />
                            }
                        />

                    </Routes>

                </Suspense>

            </PageTransition>


            <style>{`

                html {
                    background:
                        #020617;

                    color-scheme:
                        dark;

                    scroll-behavior:
                        smooth;
                }


                body {
                    margin: 0;

                    min-width:
                        320px;

                    min-height:
                        100vh;

                    background:
                        #020617;

                    color:
                        white;

                    overflow-x:
                        hidden;

                    text-rendering:
                        optimizeLegibility;

                    -webkit-font-smoothing:
                        antialiased;
                }


                #root {
                    min-height:
                        100vh;

                    width:
                        100%;

                    background:
                        #020617;

                    overflow-x:
                        hidden;
                }


                button,
                input,
                textarea,
                select {
                    font:
                        inherit;
                }


                button {
                    -webkit-tap-highlight-color:
                        transparent;
                }


                ::selection {
                    background:
                        rgba(
                            255,
                            255,
                            255,
                            0.16
                        );
                }


                ::-webkit-scrollbar {
                    width:
                        8px;

                    height:
                        8px;
                }


                ::-webkit-scrollbar-track {
                    background:
                        #020617;
                }


                ::-webkit-scrollbar-thumb {
                    background:
                        rgba(
                            148,
                            163,
                            184,
                            0.25
                        );

                    border-radius:
                        999px;
                }


                ::-webkit-scrollbar-thumb:hover {
                    background:
                        rgba(
                            148,
                            163,
                            184,
                            0.4
                        );
                }


                .nova-page {
                    position:
                        relative;

                    min-height:
                        100vh;

                    width:
                        100%;

                    background:
                        #020617;

                    isolation:
                        isolate;
                }


                .nova-transition-forward {
                    animation:
                        novaRevealRight
                        0.62s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        );

                    transform-origin:
                        center center;

                    will-change:
                        transform,
                        filter,
                        clip-path;
                }


                @keyframes novaRevealRight {

                    0% {

                        clip-path:
                            inset(
                                0 0 0 18%
                            );

                        transform:
                            scale(0.975)
                            translateX(18px);

                        filter:
                            blur(5px);
                    }


                    35% {

                        clip-path:
                            inset(
                                0 0 0 7%
                            );

                        transform:
                            scale(0.99)
                            translateX(5px);

                        filter:
                            blur(2px);
                    }


                    70% {

                        clip-path:
                            inset(
                                0 0 0 1%
                            );

                        transform:
                            scale(1.002)
                            translateX(0);

                        filter:
                            blur(0);
                    }


                    100% {

                        clip-path:
                            inset(
                                0 0 0 0
                            );

                        transform:
                            scale(1)
                            translateX(0);

                        filter:
                            blur(0);
                    }
                }


                .nova-transition-back {

                    animation:
                        novaRevealLeft
                        0.62s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        );

                    transform-origin:
                        center center;

                    will-change:
                        transform,
                        filter,
                        clip-path;
                }


                @keyframes novaRevealLeft {

                    0% {

                        clip-path:
                            inset(
                                0 18% 0 0
                            );

                        transform:
                            scale(0.975)
                            translateX(-18px);

                        filter:
                            blur(5px);
                    }


                    35% {

                        clip-path:
                            inset(
                                0 7% 0 0
                            );

                        transform:
                            scale(0.99)
                            translateX(-5px);

                        filter:
                            blur(2px);
                    }


                    70% {

                        clip-path:
                            inset(
                                0 1% 0 0
                            );

                        transform:
                            scale(1.002)
                            translateX(0);

                        filter:
                            blur(0);
                    }


                    100% {

                        clip-path:
                            inset(
                                0 0 0 0
                            );

                        transform:
                            scale(1)
                            translateX(0);

                        filter:
                            blur(0);
                    }
                }


                @media (
                    prefers-reduced-motion: reduce
                ) {

                    html {
                        scroll-behavior:
                            auto;
                    }


                    .nova-transition-forward,
                    .nova-transition-back {

                        animation:
                            none !important;
                    }
                }


                @media (
                    max-width: 640px
                ) {

                    .nova-page {
                        min-height:
                            100svh;
                    }
                }

            `}</style>

        </>
    );
}


// ============================================================
// APP
// ============================================================

function App() {

    return (

        <NovaErrorBoundary>

            <BrowserRouter>

                <AppContent />

            </BrowserRouter>

        </NovaErrorBoundary>
    );
}


export default App;
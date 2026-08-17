import React, {
    Suspense,
    lazy,
    useCallback,
    useEffect,
    useMemo,
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
    CheckCircle2,
    CircleDot,
    LoaderCircle,
    RefreshCw,
    Server,
    Wifi,
    WifiOff,
    X
} from "lucide-react";


// ============================================================
// NOVA FRONTEND CONFIGURATION
// ============================================================

const NOVA_CONFIG = {

    name:
        "Nova AI",

    version:
        "1.0.0",

    apiUrl:
        (
            import.meta.env.VITE_API_URL ||
            "http://127.0.0.1:8000"
        ).replace(/\/+$/, ""),

    requestTimeout:
        60000,

    transitionDuration:
        620,

    storage: {

        lastRoute:
            "nova_last_route",

        theme:
            "nova_theme",

        sidebar:
            "nova_sidebar_state",

        session:
            "nova_session",

        user:
            "nova_user",

        backendStatus:
            "nova_backend_status",

        initialized:
            "nova_initialized",

        lastError:
            "nova_last_error"
    },

    routes: {

        home:
            "/",

        chat:
            "/chat",

        dashboard:
            "/dashboard",

        settings:
            "/settings",

        login:
            "/login",

        register:
            "/register"
    }

};


// ============================================================
// LAZY PAGE LOADING
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
// PAGE METADATA
// ============================================================

const PAGE_METADATA = {

    "/": {
        title:
            "Nova AI",
        description:
            "Nova AI, an adaptive educational tutor."
    },

    "/chat": {
        title:
            "Chat",
        description:
            "Learn with Nova AI through adaptive tutoring."
    },

    "/dashboard": {
        title:
            "Dashboard",
        description:
            "Track your learning progress with Nova AI."
    },

    "/settings": {
        title:
            "Settings",
        description:
            "Customize your Nova AI learning experience."
    },

    "/login": {
        title:
            "Login",
        description:
            "Sign in to your Nova AI account."
    },

    "/register": {
        title:
            "Create Account",
        description:
            "Create your Nova AI learning account."
    }

};


// ============================================================
// LEARNING ROUTES
// ============================================================

const LEARNING_ROUTES = [

    "/chat",

    "/dashboard"

];


// ============================================================
// SAFE STORAGE
// ============================================================

function storageGet(key) {

    try {

        return localStorage.getItem(
            key
        );

    } catch (error) {

        console.warn(
            "[Nova] Unable to read localStorage:",
            error
        );

        return null;
    }
}


function storageSet(
    key,
    value
) {

    try {

        localStorage.setItem(
            key,
            value
        );

        return true;

    } catch (error) {

        console.warn(
            "[Nova] Unable to write localStorage:",
            error
        );

        return false;
    }
}


function storageRemove(key) {

    try {

        localStorage.removeItem(
            key
        );

        return true;

    } catch {

        return false;
    }
}


// ============================================================
// API HELPERS
// ============================================================

function buildApiUrl(path) {

    if (!path) {

        return NOVA_CONFIG.apiUrl;
    }


    if (
        path.startsWith("http://") ||
        path.startsWith("https://")
    ) {

        return path;
    }


    return (
        `${NOVA_CONFIG.apiUrl}/` +
        path.replace(/^\/+/, "")
    );
}


async function fetchWithTimeout(
    url,
    options = {},
    timeout = NOVA_CONFIG.requestTimeout
) {

    const controller =
        new AbortController();


    const timeoutId =
        setTimeout(
            () => controller.abort(),
            timeout
        );


    try {

        return await fetch(
            url,
            {
                ...options,
                signal:
                    controller.signal
            }
        );

    } finally {

        clearTimeout(
            timeoutId
        );
    }
}


// ============================================================
// GLOBAL ERROR BOUNDARY
// ============================================================

class NovaErrorBoundary
    extends React.Component {

    constructor(props) {

        super(props);

        this.state = {

            hasError:
                false,

            error:
                null,

            errorInfo:
                null
        };
    }


    static getDerivedStateFromError(
        error
    ) {

        return {

            hasError:
                true,

            error
        };
    }


    componentDidCatch(
        error,
        errorInfo
    ) {

        console.error(
            "[Nova] React rendering error:",
            error
        );


        console.error(
            "[Nova] Component information:",
            errorInfo
        );


        try {

            storageSet(

                NOVA_CONFIG.storage.lastError,

                JSON.stringify({

                    message:
                        error?.message ||
                        "Unknown error",

                    stack:
                        error?.stack ||
                        "",

                    timestamp:
                        new Date().toISOString(),

                    pathname:
                        window.location.pathname
                })

            );

        } catch {

            // Nothing else to do.
        }


        this.setState({

            errorInfo

        });
    }


    handleRetry = () => {

        this.setState({

            hasError:
                false,

            error:
                null,

            errorInfo:
                null
        });
    };


    handleReload = () => {

        window.location.reload();
    };


    handleReset = () => {

        storageRemove(
            NOVA_CONFIG.storage.lastRoute
        );

        window.location.href =
            "/";
    };


    render() {

        if (
            !this.state.hasError
        ) {

            return this.props.children;
        }


        const message =
            this.state.error?.message ||
            "Unknown frontend error.";


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
                    py-12
                "
                role="alert"
            >

                <div
                    className="
                        w-full
                        max-w-xl
                        rounded-3xl
                        border
                        border-white/10
                        bg-white/[0.04]
                        p-8
                        shadow-2xl
                        backdrop-blur-xl
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
                            size={27}
                        />

                    </div>


                    <h1
                        className="
                            mt-6
                            text-2xl
                            font-semibold
                            tracking-tight
                        "
                    >
                        Nova encountered a problem.
                    </h1>


                    <p
                        className="
                            mt-3
                            text-sm
                            leading-6
                            text-slate-400
                        "
                    >
                        Something went wrong while Nova
                        was rendering the application.
                    </p>


                    <details
                        className="
                            mt-6
                            rounded-2xl
                            border
                            border-white/10
                            bg-black/20
                            p-4
                        "
                    >

                        <summary
                            className="
                                cursor-pointer
                                text-sm
                                font-medium
                                text-slate-300
                            "
                        >
                            Technical details
                        </summary>


                        <pre
                            className="
                                mt-4
                                max-h-48
                                overflow-auto
                                whitespace-pre-wrap
                                break-words
                                text-xs
                                leading-5
                                text-red-300
                            "
                        >
                            {message}
                        </pre>

                    </details>


                    <div
                        className="
                            mt-6
                            flex
                            flex-wrap
                            gap-3
                        "
                    >

                        <button
                            type="button"
                            onClick={
                                this.handleRetry
                            }
                            className="
                                inline-flex
                                items-center
                                gap-2
                                rounded-xl
                                bg-white
                                px-4
                                py-2.5
                                text-sm
                                font-semibold
                                text-slate-950
                                transition
                                hover:bg-slate-200
                                active:scale-[0.98]
                            "
                        >

                            <RefreshCw
                                size={16}
                            />

                            Try again

                        </button>


                        <button
                            type="button"
                            onClick={
                                this.handleReload
                            }
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


                        <button
                            type="button"
                            onClick={
                                this.handleReset
                            }
                            className="
                                inline-flex
                                items-center
                                gap-2
                                rounded-xl
                                border
                                border-white/10
                                px-4
                                py-2.5
                                text-sm
                                text-slate-400
                                transition
                                hover:bg-white/5
                                hover:text-white
                            "
                        >

                            Return home

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
            role="status"
            aria-live="polite"
            aria-label="Loading Nova"
        >

            <div
                className="
                    flex
                    flex-col
                    items-center
                    gap-5
                "
            >

                <div
                    className="
                        relative
                        flex
                        h-16
                        w-16
                        items-center
                        justify-center
                        rounded-2xl
                        border
                        border-white/10
                        bg-white/[0.04]
                        shadow-xl
                    "
                >

                    <div
                        className="
                            absolute
                            inset-0
                            rounded-2xl
                            border
                            border-white/5
                        "
                    />

                    <LoaderCircle
                        size={26}
                        className="
                            animate-spin
                            text-slate-300
                        "
                    />

                </div>


                <div
                    className="
                        text-sm
                        font-medium
                        text-slate-300
                    "
                >
                    Loading Nova...
                </div>


                <div
                    className="
                        text-xs
                        text-slate-500
                    "
                >
                    Preparing your learning environment.
                </div>

            </div>

        </div>
    );
}


// ============================================================
// CHUNK LOAD ERROR RECOVERY
// ============================================================

function ChunkRecoveryBoundary({
    children
}) {

    const [
        failed,
        setFailed
    ] = useState(false);


    useEffect(() => {

        const handleError =
            event => {

                const message =
                    event?.message ||
                    event?.error?.message ||
                    "";


                const chunkFailure =
                    message.includes(
                        "Failed to fetch dynamically imported module"
                    ) ||
                    message.includes(
                        "Importing a module script failed"
                    );


                if (
                    chunkFailure
                ) {

                    setFailed(
                        true
                    );
                }
            };


        window.addEventListener(
            "error",
            handleError
        );


        return () => {

            window.removeEventListener(
                "error",
                handleError
            );
        };

    }, []);


    if (!failed) {

        return children;
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
                    max-w-md
                    rounded-3xl
                    border
                    border-white/10
                    bg-white/[0.04]
                    p-8
                    text-center
                "
            >

                <AlertTriangle
                    className="
                        mx-auto
                        text-amber-400
                    "
                    size={30}
                />


                <h1
                    className="
                        mt-5
                        text-xl
                        font-semibold
                    "
                >
                    Nova needs to refresh.
                </h1>


                <p
                    className="
                        mt-3
                        text-sm
                        leading-6
                        text-slate-400
                    "
                >
                    The browser loaded an outdated
                    frontend bundle.
                </p>


                <button
                    type="button"
                    onClick={() =>
                        window.location.reload()
                    }
                    className="
                        mt-6
                        rounded-xl
                        bg-white
                        px-5
                        py-2.5
                        text-sm
                        font-semibold
                        text-slate-950
                    "
                >
                    Refresh Nova
                </button>

            </div>

        </div>
    );
}


// ============================================================
// NETWORK STATUS
// ============================================================

function NetworkStatus() {

    const [
        online,
        setOnline
    ] = useState(
        typeof navigator !== "undefined"
            ? navigator.onLine
            : true
    );


    const [
        visible,
        setVisible
    ] = useState(false);


    const timerRef =
        useRef(null);


    useEffect(() => {

        const showTemporarily =
            () => {

                setVisible(true);


                if (
                    timerRef.current
                ) {

                    clearTimeout(
                        timerRef.current
                    );
                }


                timerRef.current =
                    setTimeout(
                        () => {
                            setVisible(false);
                        },
                        2800
                    );
            };


        const handleOnline =
            () => {

                setOnline(
                    true
                );

                showTemporarily();
            };


        const handleOffline =
            () => {

                setOnline(
                    false
                );

                setVisible(
                    true
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


            if (
                timerRef.current
            ) {

                clearTimeout(
                    timerRef.current
                );
            }
        };

    }, []);


    if (
        !visible
    ) {

        return null;
    }


    return (

        <div
            className="
                fixed
                bottom-5
                left-1/2
                z-[10000]
                -translate-x-1/2
            "
            role="status"
            aria-live="polite"
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
                    shadow-2xl
                    backdrop-blur-xl

                    ${
                        online
                            ? `
                                border-emerald-400/20
                                bg-emerald-500/10
                                text-emerald-300
                              `
                            : `
                                border-red-400/20
                                bg-red-500/10
                                text-red-300
                              `
                    }

                `}
            >

                {
                    online

                        ? (
                            <Wifi
                                size={15}
                            />
                        )

                        : (
                            <WifiOff
                                size={15}
                            />
                        )
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
// BACKEND STATUS
// ============================================================

function BackendStatus() {

    const [
        status,
        setStatus
    ] = useState(
        "checking"
    );


    const [
        visible,
        setVisible
    ] = useState(false);


    const [
        lastChecked,
        setLastChecked
    ] = useState(null);


    const checkBackend =
        useCallback(
            async () => {

                setStatus(
                    "checking"
                );


                try {

                    const response =
    await fetch(
        buildApiUrl("/health"),
        {
            method: "GET",
            headers: {
                Accept: "application/json"
            },
            cache: "no-store"
        }
    );

                    if (
                        response.ok
                    ) {

                        setStatus(
                            "online"
                        );

                    } else {

                        setStatus(
                            "degraded"
                        );
                    }


                    setLastChecked(
                        Date.now()
                    );


                    storageSet(
                        NOVA_CONFIG.storage.backendStatus,
                        response.ok
                            ? "online"
                            : "degraded"
                    );


                } catch {

                    setStatus(
                        "offline"
                    );

                    setLastChecked(
                        Date.now()
                    );


                    storageSet(
                        NOVA_CONFIG.storage.backendStatus,
                        "offline"
                    );
                }

            },
            []
        );


    useEffect(() => {

        checkBackend();


        const interval =
            setInterval(
                checkBackend,
                30000
            );


        return () => {

            clearInterval(
                interval
            );
        };

    }, [
        checkBackend
    ]);


    useEffect(() => {

        if (
            status === "online"
        ) {

            setVisible(false);

            return;
        }


        setVisible(true);

    }, [
        status
    ]);


    if (
        !visible
    ) {

        return null;
    }


    const statusText = {

        checking:
            "Connecting to Nova...",

        online:
            "Nova backend online",

        degraded:
            "Nova backend is responding slowly",

        offline:
            "Nova backend unavailable"

    }[status];


    const statusIcon = {

        checking:
            <LoaderCircle
                size={14}
                className="animate-spin"
            />,

        online:
            <CheckCircle2
                size={14}
            />,

        degraded:
            <CircleDot
                size={14}
            />,

        offline:
            <Server
                size={14}
            />

    }[status];


    return (

        <div
            className="
                fixed
                right-4
                top-4
                z-[9999]
            "
        >

            <div
                className="
                    flex
                    max-w-[calc(100vw-2rem)]
                    items-center
                    gap-2
                    rounded-xl
                    border
                    border-white/10
                    bg-slate-900/90
                    px-3
                    py-2
                    text-xs
                    text-slate-300
                    shadow-2xl
                    backdrop-blur-xl
                "
            >

                {statusIcon}

                <span>
                    {statusText}
                </span>


                {
                    lastChecked &&

                    <button
                        type="button"
                        onClick={
                            checkBackend
                        }
                        className="
                            ml-1
                            rounded-md
                            p-1
                            text-slate-500
                            transition
                            hover:bg-white/10
                            hover:text-white
                        "
                        aria-label="Check Nova backend again"
                        title="Check backend"
                    >

                        <RefreshCw
                            size={13}
                        />

                    </button>
                }


                <button
                    type="button"
                    onClick={() =>
                        setVisible(false)
                    }
                    className="
                        rounded-md
                        p-1
                        text-slate-500
                        transition
                        hover:bg-white/10
                        hover:text-white
                    "
                    aria-label="Dismiss backend status"
                >

                    <X
                        size={13}
                    />

                </button>

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


        const route =
            pathname +
            location.search;


        const shouldRemember =
            LEARNING_ROUTES.some(
                routeName =>
                    pathname === routeName ||
                    pathname.startsWith(
                        `${routeName}/`
                    )
            );


        if (
            shouldRemember
        ) {

            storageSet(
                NOVA_CONFIG.storage.lastRoute,
                route
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

function ScrollRestorationManager() {

    const location =
        useLocation();


    useEffect(() => {

        const timer =
            requestAnimationFrame(
                () => {

                    window.scrollTo({

                        top:
                            0,

                        left:
                            0,

                        behavior:
                            "auto"
                    });
                }
            );


        return () => {

            cancelAnimationFrame(
                timer
            );
        };

    }, [
        location.pathname
    ]);


    return null;
}


// ============================================================
// DOCUMENT MANAGER
// ============================================================

function DocumentManager() {

    const location =
        useLocation();


    useEffect(() => {

        const pathname =
            location.pathname;


        const metadata =
            PAGE_METADATA[pathname] ||
            {
                title:
                    "Nova AI",

                description:
                    "Nova AI, an adaptive educational tutor."
            };


        document.title =
            metadata.title === "Nova AI"

                ? "Nova AI"

                : `${metadata.title} | Nova AI`;


        let description =
            document.querySelector(
                'meta[name="description"]'
            );


        if (
            !description
        ) {

            description =
                document.createElement(
                    "meta"
                );

            description.name =
                "description";

            document.head.appendChild(
                description
            );
        }


        description.setAttribute(
            "content",
            metadata.description
        );


        let themeColor =
            document.querySelector(
                'meta[name="theme-color"]'
            );


        if (
            !themeColor
        ) {

            themeColor =
                document.createElement(
                    "meta"
                );

            themeColor.name =
                "theme-color";

            document.head.appendChild(
                themeColor
            );
        }


        themeColor.setAttribute(
            "content",
            "#020617"
        );

    }, [
        location.pathname
    ]);


    return null;
}


// ============================================================
// PAGE TRANSITIONS
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


    const firstRender =
        useRef(true);


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


    useEffect(() => {

        if (
            firstRender.current
        ) {

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


        const goingBack =
            navigationType === "POP" ||
            (
                newPath === "/" &&
                oldPath !== "/"
            );


        setDirection(
            goingBack
                ? "back"
                : "forward"
        );


        previousPath.current =
            newPath;


        setAnimate(
            true
        );


        const timer =
            setTimeout(
                () => {

                    setAnimate(
                        false
                    );

                },
                NOVA_CONFIG.transitionDuration
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
// KEYBOARD SHORTCUTS
// ============================================================

function KeyboardShortcuts() {

    const navigate =
        useNavigate();


    const location =
        useLocation();


    useEffect(() => {

        const handleKeyDown =
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


                const modifier =
                    event.ctrlKey ||
                    event.metaKey;


                // ------------------------------------------------
                // Ctrl/Cmd + K
                // ------------------------------------------------

                if (
                    modifier &&
                    event.key.toLowerCase() === "k"
                ) {

                    event.preventDefault();


                    if (
                        location.pathname !==
                        NOVA_CONFIG.routes.chat
                    ) {

                        navigate(
                            NOVA_CONFIG.routes.chat
                        );
                    }


                    return;
                }


                // ------------------------------------------------
                // Escape
                // ------------------------------------------------

                if (
                    event.key === "Escape"
                ) {

                    window.dispatchEvent(
                        new CustomEvent(
                            "nova:escape"
                        )
                    );


                    return;
                }


                if (
                    isTyping
                ) {

                    return;
                }


                // ------------------------------------------------
                // Alt + Left
                // ------------------------------------------------

                if (
                    event.altKey &&
                    event.key === "ArrowLeft"
                ) {

                    event.preventDefault();

                    window.history.back();

                    return;
                }


                // ------------------------------------------------
                // Alt + Right
                // ------------------------------------------------

                if (
                    event.altKey &&
                    event.key === "ArrowRight"
                ) {

                    event.preventDefault();

                    window.history.forward();
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
        navigate,
        location.pathname
    ]);


    return null;
}


// ============================================================
// VISIBILITY / FOCUS TRACKING
// ============================================================

function BrowserLifecycle() {

    useEffect(() => {

        const handleVisibility =
            () => {

                window.dispatchEvent(
                    new CustomEvent(
                        "nova:visibility",
                        {
                            detail: {
                                visible:
                                    !document.hidden
                            }
                        }
                    )
                );
            };


        document.addEventListener(
            "visibilitychange",
            handleVisibility
        );


        const handleFocus =
            () => {

                window.dispatchEvent(
                    new CustomEvent(
                        "nova:focus",
                        {
                            detail: {
                                focused:
                                    true
                            }
                        }
                    )
                );
            };


        const handleBlur =
            () => {

                window.dispatchEvent(
                    new CustomEvent(
                        "nova:focus",
                        {
                            detail: {
                                focused:
                                    false
                            }
                        }
                    )
                );
            };


        window.addEventListener(
            "focus",
            handleFocus
        );

        window.addEventListener(
            "blur",
            handleBlur
        );


        return () => {

            document.removeEventListener(
                "visibilitychange",
                handleVisibility
            );

            window.removeEventListener(
                "focus",
                handleFocus
            );

            window.removeEventListener(
                "blur",
                handleBlur
            );
        };

    }, []);


    return null;
}


// ============================================================
// FRONTEND INITIALIZATION
// ============================================================

function FrontendInitialization() {

    useEffect(() => {

        document.documentElement.dataset.novaVersion =
            NOVA_CONFIG.version;


        document.documentElement.dataset.novaReady =
            "true";


        document.body.classList.add(
            "nova-app"
        );


        storageSet(
            NOVA_CONFIG.storage.initialized,
            "true"
        );


        // ----------------------------------------------------
        // Viewport
        // ----------------------------------------------------

        let viewport =
            document.querySelector(
                'meta[name="viewport"]'
            );


        if (
            !viewport
        ) {

            viewport =
                document.createElement(
                    "meta"
                );

            viewport.name =
                "viewport";

            document.head.appendChild(
                viewport
            );
        }


        viewport.content =
            "width=device-width, initial-scale=1.0, viewport-fit=cover";


        // ----------------------------------------------------
        // Color scheme
        // ----------------------------------------------------

        let colorScheme =
            document.querySelector(
                'meta[name="color-scheme"]'
            );


        if (
            !colorScheme
        ) {

            colorScheme =
                document.createElement(
                    "meta"
                );

            colorScheme.name =
                "color-scheme";

            document.head.appendChild(
                colorScheme
            );
        }


        colorScheme.content =
            "dark";


        // ----------------------------------------------------
        // Development diagnostics
        // ----------------------------------------------------

        if (
            import.meta.env.DEV
        ) {

            console.info(
                `[Nova] ${NOVA_CONFIG.name} v${NOVA_CONFIG.version}`
            );

            console.info(
                `[Nova] API: ${NOVA_CONFIG.apiUrl}`
            );

            console.info(
                "[Nova] Development mode enabled."
            );
        }

    }, []);


    return null;
}


// ============================================================
// GLOBAL BROWSER ERROR HANDLERS
// ============================================================

function GlobalErrorHandlers() {

    useEffect(() => {

        const handleError =
            event => {

                console.error(
                    "[Nova] Browser error:",
                    event.error ||
                    event.message
                );
            };


        const handleRejection =
            event => {

                console.error(
                    "[Nova] Unhandled promise rejection:",
                    event.reason
                );
            };


        window.addEventListener(
            "error",
            handleError
        );

        window.addEventListener(
            "unhandledrejection",
            handleRejection
        );


        return () => {

            window.removeEventListener(
                "error",
                handleError
            );

            window.removeEventListener(
                "unhandledrejection",
                handleRejection
            );
        };

    }, []);


    return null;
}


// ============================================================
// ROUTE LOADING FALLBACK
// ============================================================

function RouteLoadingFallback() {

    return (
        <PageLoader />
    );
}


// ============================================================
// APPLICATION ROUTES
// ============================================================

function ApplicationRoutes() {

    return (

        <Suspense
            fallback={
                <RouteLoadingFallback />
            }
        >

            <Routes>

                <Route
                    path="/"
                    element={
                        <Home />
                    }
                />


                <Route
                    path="/chat"
                    element={
                        <Chat />
                    }
                />


                <Route
                    path="/dashboard"
                    element={
                        <Dashboard />
                    }
                />


                <Route
                    path="/settings"
                    element={
                        <Settings />
                    }
                />


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


                <Route
                    path="*"
                    element={
                        <NotFound />
                    }
                />

            </Routes>

        </Suspense>
    );
}


// ============================================================
// APP CONTENT
// ============================================================

function AppContent() {

    const apiConfiguration =
        useMemo(
            () => ({

                baseUrl:
                    NOVA_CONFIG.apiUrl,

                version:
                    NOVA_CONFIG.version

            }),
            []
        );


    useEffect(() => {

        /*
         * Do not mutate window.Nova here.
         *
         * home.jsx may expose window.Nova as a frozen
         * runtime object. Mutating it would therefore
         * cause a runtime error.
         *
         * Instead, expose App's configuration separately.
         */

        window.NovaAppConfig =
            apiConfiguration;


        return () => {

            try {

                delete window.NovaAppConfig;

            } catch {

                // Ignore cleanup failures.
            }

        };

    }, [
        apiConfiguration
    ]);


    return (

        <>

            <FrontendInitialization />

            <GlobalErrorHandlers />

            <BrowserLifecycle />

            <RouteMemory />

            <ScrollRestorationManager />

            <DocumentManager />

            <KeyboardShortcuts />

            <BackendStatus />

            <NetworkStatus />


            <PageTransition>

                <ChunkRecoveryBoundary>

                    <ApplicationRoutes />

                </ChunkRecoveryBoundary>

            </PageTransition>


            <style>{`

                /* =================================================
                   NOVA GLOBAL FOUNDATION
                   ================================================= */

                :root {

                    color-scheme:
                        dark;

                    background:
                        #020617;

                    --nova-background:
                        #020617;

                    --nova-surface:
                        rgba(
                            255,
                            255,
                            255,
                            0.04
                        );

                    --nova-border:
                        rgba(
                            255,
                            255,
                            255,
                            0.10
                        );

                    --nova-text:
                        #ffffff;

                    --nova-muted:
                        #94a3b8;
                }


                html {

                    background:
                        var(
                            --nova-background
                        );

                    color-scheme:
                        dark;

                    scroll-behavior:
                        smooth;

                    min-width:
                        320px;
                }


                body {

                    margin:
                        0;

                    min-width:
                        320px;

                    min-height:
                        100vh;

                    background:
                        var(
                            --nova-background
                        );

                    color:
                        var(
                            --nova-text
                        );

                    overflow-x:
                        hidden;

                    text-rendering:
                        optimizeLegibility;

                    -webkit-font-smoothing:
                        antialiased;

                    -moz-osx-font-smoothing:
                        grayscale;
                }


                body.nova-app {

                    overscroll-behavior-x:
                        none;
                }


                #root {

                    min-height:
                        100vh;

                    width:
                        100%;

                    background:
                        var(
                            --nova-background
                        );

                    overflow-x:
                        hidden;
                }


                *,
                *::before,
                *::after {

                    box-sizing:
                        border-box;
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


                img,
                svg {

                    max-width:
                        100%;
                }


                a {

                    color:
                        inherit;
                }


                ::selection {

                    background:
                        rgba(
                            255,
                            255,
                            255,
                            0.16
                        );

                    color:
                        white;
                }


                /* =================================================
                   SCROLLBAR
                   ================================================= */

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

                    border:
                        2px solid
                        transparent;

                    background-clip:
                        padding-box;
                }


                ::-webkit-scrollbar-thumb:hover {

                    background:
                        rgba(
                            148,
                            163,
                            184,
                            0.40
                        );

                    background-clip:
                        padding-box;
                }


                /* =================================================
                   PAGE SYSTEM
                   ================================================= */

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


                /* =================================================
                   FORWARD TRANSITION
                   ================================================= */

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


                /* =================================================
                   BACK TRANSITION
                   ================================================= */

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


                /* =================================================
                   MOBILE
                   ================================================= */

                @media (
                    max-width: 640px
                ) {

                    html {

                        scroll-behavior:
                            auto;
                    }


                    .nova-page {

                        min-height:
                            100svh;
                    }
                }


                /* =================================================
                   REDUCED MOTION
                   ================================================= */

                @media (
                    prefers-reduced-motion: reduce
                ) {

                    html {

                        scroll-behavior:
                            auto;
                    }


                    *,
                    *::before,
                    *::after {

                        animation-duration:
                            0.01ms !important;

                        animation-iteration-count:
                            1 !important;

                        transition-duration:
                            0.01ms !important;

                        scroll-behavior:
                            auto !important;
                    }


                    .nova-transition-forward,
                    .nova-transition-back {

                        animation:
                            none !important;
                    }
                }


                /* =================================================
                   SAFE AREA SUPPORT
                   ================================================= */

                @supports (
                    padding: env(safe-area-inset-top)
                ) {

                    body {

                        padding-top:
                            env(
                                safe-area-inset-top
                            );

                        padding-bottom:
                            env(
                                safe-area-inset-bottom
                            );
                    }
                }


                /* =================================================
                   FOCUS ACCESSIBILITY
                   ================================================= */

                :focus-visible {

                    outline:
                        2px solid
                        rgba(
                            255,
                            255,
                            255,
                            0.70
                        );

                    outline-offset:
                        3px;
                }

            `}</style>

        </>
    );
}


// ============================================================
// ROOT APP
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
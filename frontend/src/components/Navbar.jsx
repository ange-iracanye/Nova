import {
    Link,
    useLocation,
    useNavigate
} from "react-router-dom";

import {
    Bot,
    Settings,
    LogOut,
    ChevronDown,
    Menu,
    X,
    MessageSquare,
    LayoutDashboard,
    Home,
    UserRound,
    Sparkles,
    ShieldCheck
} from "lucide-react";

import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState
} from "react";


// ============================================================
// CONSTANTS
// ============================================================

const STORAGE_KEYS = {
    USER: "nova_user",
    CURRENT_CONVERSATION:
        "nova_current_conversation"
};


// ============================================================
// NAVIGATION
// ============================================================

const NAV_ITEMS = [
    {
        label: "Home",
        path: "/",
        icon: Home
    },
    {
        label: "Chat",
        path: "/chat",
        icon: MessageSquare
    },
    {
        label: "Dashboard",
        path: "/dashboard",
        icon: LayoutDashboard
    },
    {
        label: "Settings",
        path: "/settings",
        icon: Settings
    }
];


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
// USER HELPERS
// ============================================================

function getUserEmail(user) {

    if (
        user &&
        typeof user.email === "string" &&
        user.email.trim()
    ) {

        return user.email.trim();
    }

    return "";
}


function getUserInitial(user) {

    const email =
        getUserEmail(user);

    if (!email) {
        return "N";
    }

    return email
        .charAt(0)
        .toUpperCase();
}


// ============================================================
// NAVBAR
// ============================================================

export default function Navbar() {

    const navigate =
        useNavigate();

    const location =
        useLocation();


    // ========================================================
    // STATE
    // ========================================================

    const [
        accountOpen,
        setAccountOpen
    ] = useState(false);


    const [
        mobileOpen,
        setMobileOpen
    ] = useState(false);


    const [
        user,
        setUser
    ] = useState(() =>
        getStoredUser()
    );


    const [
        scrolled,
        setScrolled
    ] = useState(false);


    const [
        loggingOut,
        setLoggingOut
    ] = useState(false);


    // ========================================================
    // REFS
    // ========================================================

    const accountRef =
        useRef(null);

    const mobileRef =
        useRef(null);

    const mobileButtonRef =
        useRef(null);


    // ========================================================
    // DERIVED USER DATA
    // ========================================================

    const userEmail =
        useMemo(
            () => getUserEmail(user),
            [user]
        );


    const userInitial =
        useMemo(
            () => getUserInitial(user),
            [user]
        );


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

        const handleStorage =
            event => {

                if (
                    event.key ===
                    STORAGE_KEYS.USER
                ) {

                    refreshUser();

                }

            };


        window.addEventListener(
            "storage",
            handleStorage
        );


        return () => {

            window.removeEventListener(
                "storage",
                handleStorage
            );

        };

    }, [
        refreshUser
    ]);


    // ========================================================
    // SAME-TAB STORAGE SYNC
    // ========================================================
    //
    // The browser's "storage" event does not fire in the
    // same tab that changed localStorage.
    //
    // A small custom event lets Nova update immediately.
    //
    // ========================================================

    useEffect(() => {

        const handleNovaUserChange =
            () => {

                refreshUser();

            };


        window.addEventListener(
            "nova:user-changed",
            handleNovaUserChange
        );


        return () => {

            window.removeEventListener(
                "nova:user-changed",
                handleNovaUserChange
            );

        };

    }, [
        refreshUser
    ]);


    // ========================================================
    // SCROLL DETECTION
    // ========================================================

    useEffect(() => {

        let ticking = false;


        const handleScroll =
            () => {

                if (ticking) {
                    return;
                }

                ticking = true;


                window.requestAnimationFrame(
                    () => {

                        setScrolled(
                            window.scrollY > 8
                        );

                        ticking = false;

                    }
                );

            };


        handleScroll();


        window.addEventListener(
            "scroll",
            handleScroll,
            {
                passive: true
            }
        );


        return () => {

            window.removeEventListener(
                "scroll",
                handleScroll
            );

        };

    }, []);


    // ========================================================
    // ACTIVE ROUTE
    // ========================================================

    const isActive =
        useCallback(
            path => {

                if (path === "/") {

                    return (
                        location.pathname ===
                        "/"
                    );

                }

                return (
                    location.pathname ===
                        path ||
                    location.pathname.startsWith(
                        `${path}/`
                    )
                );

            },
            [
                location.pathname
            ]
        );


    // ========================================================
    // CLOSE MENUS
    // ========================================================

    const closeAccount =
        useCallback(() => {

            setAccountOpen(false);

        }, []);


    const closeMobile =
        useCallback(() => {

            setMobileOpen(false);

        }, []);


    const closeMenus =
        useCallback(() => {

            setAccountOpen(false);
            setMobileOpen(false);

        }, []);


    // ========================================================
    // ROUTE CHANGE
    // ========================================================

    useEffect(() => {

        closeMenus();

    }, [
        location.pathname,
        location.search,
        closeMenus
    ]);


    // ========================================================
    // OUTSIDE CLICK
    // ========================================================

    useEffect(() => {

        function handlePointerDown(event) {

            const target =
                event.target;


            if (
                accountRef.current &&
                !accountRef.current.contains(
                    target
                )
            ) {

                closeAccount();

            }


            if (
                mobileRef.current &&
                mobileButtonRef.current &&
                !mobileRef.current.contains(
                    target
                ) &&
                !mobileButtonRef.current.contains(
                    target
                )
            ) {

                closeMobile();

            }

        }


        document.addEventListener(
            "mousedown",
            handlePointerDown
        );


        return () => {

            document.removeEventListener(
                "mousedown",
                handlePointerDown
            );

        };

    }, [
        closeAccount,
        closeMobile
    ]);


    // ========================================================
    // ESCAPE KEY
    // ========================================================

    useEffect(() => {

        function handleKeyDown(event) {

            if (
                event.key !== "Escape"
            ) {
                return;
            }


            if (accountOpen) {

                setAccountOpen(false);

                return;

            }


            if (mobileOpen) {

                setMobileOpen(false);

            }

        }


        document.addEventListener(
            "keydown",
            handleKeyDown
        );


        return () => {

            document.removeEventListener(
                "keydown",
                handleKeyDown
            );

        };

    }, [
        accountOpen,
        mobileOpen
    ]);


    // ========================================================
    // BODY SCROLL LOCK
    // ========================================================

    useEffect(() => {

        if (!mobileOpen) {
            return;
        }


        const previousOverflow =
            document.body.style.overflow;


        document.body.style.overflow =
            "hidden";


        return () => {

            document.body.style.overflow =
                previousOverflow;

        };

    }, [
        mobileOpen
    ]);


    // ========================================================
    // PERSONALIZE
    // ========================================================

    function personalize() {

        closeMenus();

        navigate(
            "/settings"
        );

    }


    // ========================================================
    // LOG OUT
    // ========================================================

    function logout() {

        if (loggingOut) {
            return;
        }


        setLoggingOut(true);


        try {

            localStorage.removeItem(
                STORAGE_KEYS.USER
            );

            localStorage.removeItem(
                STORAGE_KEYS.CURRENT_CONVERSATION
            );


            setUser(null);

            closeMenus();


            window.dispatchEvent(
                new Event(
                    "nova:user-changed"
                )
            );


            navigate(
                "/"
            );

        } catch (error) {

            console.error(
                "Nova logout error:",
                error
            );

        } finally {

            setLoggingOut(false);

        }

    }


    // ========================================================
    // MOBILE NAVIGATION
    // ========================================================

    function handleMobileNavigation(
        path
    ) {

        closeMenus();

        navigate(path);

    }


    // ========================================================
    // ACCOUNT TOGGLE
    // ========================================================

    function toggleAccount() {

        setAccountOpen(
            previous =>
                !previous
        );

        setMobileOpen(false);

    }


    // ========================================================
    // MOBILE TOGGLE
    // ========================================================

    function toggleMobile() {

        setMobileOpen(
            previous =>
                !previous
        );

        setAccountOpen(false);

    }


    // ========================================================
    // UI
    // ========================================================

    return (

        <>

            {/* =================================================
                NAVBAR
            ================================================= */}

            <nav
                className={`
                    sticky
                    top-0
                    z-[100]
                    w-full
                    border-b
                    transition-all
                    duration-300

                    ${
                        scrolled
                            ? `
                                border-slate-800/80
                                bg-slate-950/90
                                shadow-xl
                                shadow-black/10
                            `
                            : `
                                border-slate-800/50
                                bg-slate-950/70
                            `
                    }

                    backdrop-blur-2xl
                `}
            >

                <div
                    className="
                        max-w-7xl
                        mx-auto
                        px-4
                        sm:px-6
                        lg:px-8
                    "
                >

                    <div
                        className="
                            h-16
                            sm:h-[72px]
                            flex
                            items-center
                            justify-between
                            gap-4
                        "
                    >

                        {/* =====================================
                            LOGO
                        ===================================== */}

                        <Link
                            to="/"
                            onClick={closeMenus}
                            aria-label="Nova AI home"
                            className="
                                group
                                flex
                                items-center
                                gap-3
                                shrink-0
                                rounded-xl
                                outline-none
                                focus-visible:ring-2
                                focus-visible:ring-blue-500/70
                                focus-visible:ring-offset-2
                                focus-visible:ring-offset-slate-950
                            "
                        >

                            <div
                                className="
                                    relative
                                    flex
                                    h-10
                                    w-10
                                    items-center
                                    justify-center
                                    rounded-xl
                                    border
                                    border-blue-400/20
                                    bg-blue-500/10
                                    text-blue-400
                                    shadow-lg
                                    shadow-blue-950/20
                                    transition-all
                                    duration-300
                                    group-hover:border-blue-400/40
                                    group-hover:bg-blue-500/15
                                    group-hover:scale-105
                                "
                            >

                                <div
                                    className="
                                        absolute
                                        inset-0
                                        rounded-xl
                                        bg-blue-500/10
                                        blur-xl
                                        opacity-0
                                        transition-opacity
                                        duration-300
                                        group-hover:opacity-100
                                    "
                                />

                                <Bot
                                    size={22}
                                    strokeWidth={1.8}
                                    className="
                                        relative
                                        z-10
                                    "
                                />

                            </div>


                            <div
                                className="
                                    flex
                                    flex-col
                                    leading-none
                                "
                            >

                                <span
                                    className="
                                        text-xl
                                        sm:text-2xl
                                        font-bold
                                        tracking-tight
                                        text-white
                                    "
                                >
                                    Nova
                                </span>

                                <span
                                    className="
                                        hidden
                                        sm:block
                                        mt-1
                                        text-[9px]
                                        font-medium
                                        uppercase
                                        tracking-[0.22em]
                                        text-slate-500
                                    "
                                >
                                    AI Learning
                                </span>

                            </div>

                        </Link>


                        {/* =====================================
                            DESKTOP NAVIGATION
                        ===================================== */}

                        <div
                            className="
                                hidden
                                lg:flex
                                items-center
                                gap-1
                                rounded-2xl
                                border
                                border-slate-800/60
                                bg-slate-900/30
                                p-1
                            "
                        >

                            {NAV_ITEMS.map(
                                item => {

                                    const Icon =
                                        item.icon;

                                    const active =
                                        isActive(
                                            item.path
                                        );


                                    return (

                                        <Link
                                            key={
                                                item.path
                                            }
                                            to={
                                                item.path
                                            }
                                            aria-current={
                                                active
                                                    ? "page"
                                                    : undefined
                                            }
                                            className={`
                                                group
                                                relative
                                                flex
                                                items-center
                                                gap-2
                                                rounded-xl
                                                px-3.5
                                                py-2
                                                text-sm
                                                font-medium
                                                transition-all
                                                duration-200
                                                outline-none
                                                focus-visible:ring-2
                                                focus-visible:ring-blue-500/70

                                                ${
                                                    active
                                                        ? `
                                                            bg-white/[0.07]
                                                            text-white
                                                            shadow-sm
                                                        `
                                                        : `
                                                            text-slate-400
                                                            hover:bg-white/[0.04]
                                                            hover:text-slate-100
                                                        `
                                                }
                                            `}
                                        >

                                            <Icon
                                                size={16}
                                                strokeWidth={
                                                    active
                                                        ? 2
                                                        : 1.8
                                                }
                                                className={`
                                                    transition-colors

                                                    ${
                                                        active
                                                            ? "text-blue-400"
                                                            : "text-slate-500 group-hover:text-slate-300"
                                                    }
                                                `}
                                            />

                                            {item.label}

                                            {active && (

                                                <span
                                                    className="
                                                        absolute
                                                        bottom-0.5
                                                        left-1/2
                                                        h-0.5
                                                        w-5
                                                        -translate-x-1/2
                                                        rounded-full
                                                        bg-blue-400
                                                    "
                                                />

                                            )}

                                        </Link>

                                    );

                                }
                            )}

                        </div>


                        {/* =====================================
                            RIGHT SIDE
                        ===================================== */}

                        <div
                            className="
                                flex
                                items-center
                                gap-2
                            "
                        >

                            {/* Status indicator */}

                            <div
                                className="
                                    hidden
                                    xl:flex
                                    items-center
                                    gap-2
                                    rounded-full
                                    border
                                    border-emerald-400/10
                                    bg-emerald-400/[0.04]
                                    px-3
                                    py-1.5
                                "
                                title="Nova is ready"
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
                                            bg-emerald-400
                                            opacity-40
                                        "
                                    />

                                    <span
                                        className="
                                            relative
                                            inline-flex
                                            h-2
                                            w-2
                                            rounded-full
                                            bg-emerald-400
                                        "
                                    />

                                </span>

                                <span
                                    className="
                                        text-[11px]
                                        font-medium
                                        text-emerald-300
                                    "
                                >
                                    Ready
                                </span>

                            </div>


                            {/* =================================
                                ACCOUNT
                            ================================= */}

                            {!user ? (

                                <Link
                                    to="/login"
                                    className="
                                        hidden
                                        sm:inline-flex
                                        items-center
                                        gap-2
                                        rounded-xl
                                        bg-blue-600
                                        px-4
                                        py-2.5
                                        text-sm
                                        font-semibold
                                        text-white
                                        shadow-lg
                                        shadow-blue-950/30
                                        transition-all
                                        duration-200
                                        hover:bg-blue-500
                                        hover:-translate-y-0.5
                                        hover:shadow-blue-900/40
                                        active:translate-y-0
                                        outline-none
                                        focus-visible:ring-2
                                        focus-visible:ring-blue-400
                                        focus-visible:ring-offset-2
                                        focus-visible:ring-offset-slate-950
                                    "
                                >

                                    <UserRound
                                        size={16}
                                    />

                                    Login

                                </Link>

                            ) : (

                                <div
                                    ref={accountRef}
                                    className="
                                        relative
                                        hidden
                                        sm:block
                                    "
                                >

                                    <button
                                        type="button"
                                        onClick={
                                            toggleAccount
                                        }
                                        aria-expanded={
                                            accountOpen
                                        }
                                        aria-haspopup="menu"
                                        className="
                                            group
                                            flex
                                            items-center
                                            gap-2.5
                                            rounded-xl
                                            border
                                            border-transparent
                                            px-2
                                            py-1.5
                                            transition-all
                                            duration-200
                                            hover:border-slate-800
                                            hover:bg-slate-900/80
                                            outline-none
                                            focus-visible:ring-2
                                            focus-visible:ring-blue-500/70
                                        "
                                    >

                                        <div
                                            className="
                                                relative
                                                flex
                                                h-9
                                                w-9
                                                items-center
                                                justify-center
                                                overflow-hidden
                                                rounded-full
                                                border
                                                border-blue-400/20
                                                bg-gradient-to-br
                                                from-blue-500/20
                                                to-slate-800
                                            "
                                        >

                                            <span
                                                className="
                                                    text-sm
                                                    font-bold
                                                    text-blue-300
                                                "
                                            >
                                                {
                                                    userInitial
                                                }
                                            </span>

                                        </div>


                                        <div
                                            className="
                                                hidden
                                                md:block
                                                max-w-36
                                                text-left
                                            "
                                        >

                                            <div
                                                className="
                                                    truncate
                                                    text-sm
                                                    font-medium
                                                    text-slate-100
                                                "
                                            >
                                                {
                                                    userEmail ||
                                                    "Nova User"
                                                }
                                            </div>

                                            <div
                                                className="
                                                    mt-0.5
                                                    flex
                                                    items-center
                                                    gap-1
                                                    text-[10px]
                                                    text-slate-500
                                                "
                                            >

                                                <ShieldCheck
                                                    size={11}
                                                />

                                                Account

                                            </div>

                                        </div>


                                        <ChevronDown
                                            size={15}
                                            className={`
                                                text-slate-500
                                                transition-transform
                                                duration-200
                                                ${
                                                    accountOpen
                                                        ? "rotate-180"
                                                        : ""
                                                }
                                            `}
                                        />

                                    </button>


                                    {/* ACCOUNT DROPDOWN */}

                                    {accountOpen && (

                                        <div
                                            role="menu"
                                            className="
                                                absolute
                                                right-0
                                                top-full
                                                mt-2
                                                w-64
                                                overflow-hidden
                                                rounded-2xl
                                                border
                                                border-slate-800
                                                bg-slate-950/95
                                                shadow-2xl
                                                shadow-black/50
                                                backdrop-blur-2xl
                                                animate-account-menu
                                            "
                                        >

                                            <div
                                                className="
                                                    border-b
                                                    border-slate-800
                                                    px-4
                                                    py-3
                                                "
                                            >

                                                <div
                                                    className="
                                                        text-[10px]
                                                        font-semibold
                                                        uppercase
                                                        tracking-[0.18em]
                                                        text-slate-600
                                                    "
                                                >
                                                    Signed in as
                                                </div>

                                                <div
                                                    className="
                                                        mt-1
                                                        truncate
                                                        text-sm
                                                        text-slate-300
                                                    "
                                                >
                                                    {
                                                        userEmail ||
                                                        "Nova User"
                                                    }
                                                </div>

                                            </div>


                                            <button
                                                type="button"
                                                role="menuitem"
                                                onClick={
                                                    personalize
                                                }
                                                className="
                                                    flex
                                                    w-full
                                                    items-center
                                                    gap-3
                                                    px-4
                                                    py-3.5
                                                    text-left
                                                    text-sm
                                                    text-slate-300
                                                    transition-colors
                                                    hover:bg-slate-900
                                                    hover:text-white
                                                    focus:bg-slate-900
                                                    focus:outline-none
                                                "
                                            >

                                                <span
                                                    className="
                                                        flex
                                                        h-8
                                                        w-8
                                                        items-center
                                                        justify-center
                                                        rounded-lg
                                                        bg-slate-800
                                                        text-slate-400
                                                    "
                                                >

                                                    <Settings
                                                        size={16}
                                                    />

                                                </span>

                                                <span
                                                    className="
                                                        flex-1
                                                    "
                                                >
                                                    Personalize account
                                                </span>

                                            </button>


                                            <div
                                                className="
                                                    mx-3
                                                    h-px
                                                    bg-slate-800
                                                "
                                            />


                                            <button
                                                type="button"
                                                role="menuitem"
                                                onClick={
                                                    logout
                                                }
                                                disabled={
                                                    loggingOut
                                                }
                                                className="
                                                    flex
                                                    w-full
                                                    items-center
                                                    gap-3
                                                    px-4
                                                    py-3.5
                                                    text-left
                                                    text-sm
                                                    text-slate-400
                                                    transition-colors
                                                    hover:bg-red-950/40
                                                    hover:text-red-300
                                                    disabled:cursor-not-allowed
                                                    disabled:opacity-50
                                                    focus:bg-red-950/40
                                                    focus:outline-none
                                                "
                                            >

                                                <span
                                                    className="
                                                        flex
                                                        h-8
                                                        w-8
                                                        items-center
                                                        justify-center
                                                        rounded-lg
                                                        bg-red-500/5
                                                    "
                                                >

                                                    <LogOut
                                                        size={16}
                                                    />

                                                </span>

                                                <span>
                                                    {
                                                        loggingOut
                                                            ? "Logging out..."
                                                            : "Log out"
                                                    }
                                                </span>

                                            </button>

                                        </div>

                                    )}

                                </div>

                            )}


                            {/* =================================
                                MOBILE BUTTON
                            ================================= */}

                            <button
                                ref={
                                    mobileButtonRef
                                }
                                type="button"
                                onClick={
                                    toggleMobile
                                }
                                aria-label={
                                    mobileOpen
                                        ? "Close navigation menu"
                                        : "Open navigation menu"
                                }
                                aria-expanded={
                                    mobileOpen
                                }
                                className="
                                    flex
                                    h-10
                                    w-10
                                    items-center
                                    justify-center
                                    rounded-xl
                                    border
                                    border-slate-800
                                    bg-slate-900/60
                                    text-slate-300
                                    transition-all
                                    duration-200
                                    hover:bg-slate-800
                                    hover:text-white
                                    lg:hidden
                                    outline-none
                                    focus-visible:ring-2
                                    focus-visible:ring-blue-500/70
                                "
                            >

                                {mobileOpen ? (

                                    <X
                                        size={20}
                                    />

                                ) : (

                                    <Menu
                                        size={20}
                                    />

                                )}

                            </button>

                        </div>

                    </div>

                </div>


                {/* =================================================
                    MOBILE MENU
                ================================================= */}

                {mobileOpen && (

                    <div
                        ref={mobileRef}
                        className="
                            border-t
                            border-slate-800/70
                            bg-slate-950/95
                            backdrop-blur-2xl
                            lg:hidden
                            animate-mobile-menu
                        "
                    >

                        <div
                            className="
                                mx-auto
                                max-w-7xl
                                px-4
                                py-4
                                sm:px-6
                            "
                        >

                            <div
                                className="
                                    rounded-2xl
                                    border
                                    border-slate-800/70
                                    bg-slate-900/30
                                    p-2
                                "
                            >

                                {NAV_ITEMS.map(
                                    item => {

                                        const Icon =
                                            item.icon;

                                        const active =
                                            isActive(
                                                item.path
                                            );


                                        return (

                                            <button
                                                key={
                                                    item.path
                                                }
                                                type="button"
                                                onClick={() =>
                                                    handleMobileNavigation(
                                                        item.path
                                                    )
                                                }
                                                className={`
                                                    flex
                                                    w-full
                                                    items-center
                                                    gap-3
                                                    rounded-xl
                                                    px-3
                                                    py-3
                                                    text-left
                                                    text-sm
                                                    font-medium
                                                    transition-all

                                                    ${
                                                        active
                                                            ? `
                                                                bg-blue-500/10
                                                                text-white
                                                            `
                                                            : `
                                                                text-slate-400
                                                                hover:bg-slate-800/70
                                                                hover:text-white
                                                            `
                                                    }
                                                `}
                                            >

                                                <span
                                                    className={`
                                                        flex
                                                        h-9
                                                        w-9
                                                        items-center
                                                        justify-center
                                                        rounded-lg

                                                        ${
                                                            active
                                                                ? `
                                                                    bg-blue-500/15
                                                                    text-blue-400
                                                                `
                                                                : `
                                                                    bg-slate-800/60
                                                                    text-slate-500
                                                                `
                                                        }
                                                    `}
                                                >

                                                    <Icon
                                                        size={17}
                                                    />

                                                </span>

                                                <span
                                                    className="
                                                        flex-1
                                                    "
                                                >
                                                    {
                                                        item.label
                                                    }
                                                </span>


                                                {active && (

                                                    <span
                                                        className="
                                                            h-1.5
                                                            w-1.5
                                                            rounded-full
                                                            bg-blue-400
                                                        "
                                                    />

                                                )}

                                            </button>

                                        );

                                    }
                                )}

                            </div>


                            {/* MOBILE ACCOUNT */}

                            {user ? (

                                <div
                                    className="
                                        mt-3
                                        rounded-2xl
                                        border
                                        border-slate-800/70
                                        bg-slate-900/30
                                        p-3
                                    "
                                >

                                    <div
                                        className="
                                            flex
                                            items-center
                                            gap-3
                                            px-2
                                            py-2
                                        "
                                    >

                                        <div
                                            className="
                                                flex
                                                h-10
                                                w-10
                                                shrink-0
                                                items-center
                                                justify-center
                                                rounded-full
                                                border
                                                border-blue-400/20
                                                bg-blue-500/10
                                                text-sm
                                                font-bold
                                                text-blue-300
                                            "
                                        >
                                            {
                                                userInitial
                                            }
                                        </div>


                                        <div
                                            className="
                                                min-w-0
                                                flex-1
                                            "
                                        >

                                            <div
                                                className="
                                                    truncate
                                                    text-sm
                                                    font-medium
                                                    text-white
                                                "
                                            >
                                                {
                                                    userEmail ||
                                                    "Nova User"
                                                }
                                            </div>

                                            <div
                                                className="
                                                    text-xs
                                                    text-slate-500
                                                "
                                            >
                                                Nova account
                                            </div>

                                        </div>

                                    </div>


                                    <div
                                        className="
                                            my-2
                                            h-px
                                            bg-slate-800
                                        "
                                    />


                                    <button
                                        type="button"
                                        onClick={
                                            personalize
                                        }
                                        className="
                                            flex
                                            w-full
                                            items-center
                                            gap-3
                                            rounded-xl
                                            px-3
                                            py-3
                                            text-left
                                            text-sm
                                            text-slate-300
                                            transition
                                            hover:bg-slate-800
                                            hover:text-white
                                        "
                                    >

                                        <Settings
                                            size={17}
                                        />

                                        Personalize account

                                    </button>


                                    <button
                                        type="button"
                                        onClick={
                                            logout
                                        }
                                        disabled={
                                            loggingOut
                                        }
                                        className="
                                            mt-1
                                            flex
                                            w-full
                                            items-center
                                            gap-3
                                            rounded-xl
                                            px-3
                                            py-3
                                            text-left
                                            text-sm
                                            text-slate-400
                                            transition
                                            hover:bg-red-950/40
                                            hover:text-red-300
                                            disabled:opacity-50
                                        "
                                    >

                                        <LogOut
                                            size={17}
                                        />

                                        {
                                            loggingOut
                                                ? "Logging out..."
                                                : "Log out"
                                        }

                                    </button>

                                </div>

                            ) : (

                                <Link
                                    to="/login"
                                    onClick={
                                        closeMenus
                                    }
                                    className="
                                        mt-3
                                        flex
                                        w-full
                                        items-center
                                        justify-center
                                        gap-2
                                        rounded-xl
                                        bg-blue-600
                                        px-4
                                        py-3
                                        text-sm
                                        font-semibold
                                        text-white
                                        shadow-lg
                                        shadow-blue-950/30
                                        transition
                                        hover:bg-blue-500
                                    "
                                >

                                    <UserRound
                                        size={17}
                                    />

                                    Login

                                </Link>

                            )}


                            {/* MOBILE BRAND FOOTER */}

                            <div
                                className="
                                    mt-4
                                    flex
                                    items-center
                                    justify-center
                                    gap-2
                                    text-[10px]
                                    uppercase
                                    tracking-[0.2em]
                                    text-slate-700
                                "
                            >

                                <Sparkles
                                    size={11}
                                />

                                Adaptive learning

                            </div>

                        </div>

                    </div>

                )}

            </nav>


            {/* =================================================
                ANIMATIONS
            ================================================= */}

            <style>{`

                @keyframes accountMenu {

                    from {
                        opacity: 0;
                        transform:
                            translateY(-7px)
                            scale(0.97);
                    }

                    to {
                        opacity: 1;
                        transform:
                            translateY(0)
                            scale(1);
                    }

                }


                .animate-account-menu {

                    animation:
                        accountMenu
                        180ms
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        )
                        both;

                    transform-origin:
                        top right;

                }


                @keyframes mobileMenu {

                    from {
                        opacity: 0;
                        transform:
                            translateY(-8px);
                    }

                    to {
                        opacity: 1;
                        transform:
                            translateY(0);
                    }

                }


                .animate-mobile-menu {

                    animation:
                        mobileMenu
                        220ms
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        )
                        both;

                }


                @media (
                    prefers-reduced-motion: reduce
                ) {

                    .animate-account-menu,
                    .animate-mobile-menu {

                        animation:
                            none;

                    }

                }

            `}</style>

        </>

    );

}
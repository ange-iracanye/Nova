import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState
} from "react";

import {
    Link,
    useNavigate
} from "react-router-dom";

import {
    AlertCircle,
    ArrowRight,
    CheckCircle2,
    Eye,
    EyeOff,
    KeyRound,
    LoaderCircle,
    LogIn,
    Mail,
    ShieldCheck,
    Sparkles,
    UserRound,
    Wifi,
    WifiOff
} from "lucide-react";


// ============================================================
// NOVA LOGIN CONFIGURATION
// ============================================================

const API_URL = (
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const STORAGE_KEYS = {

    user:
        "nova_user",

    session:
        "nova_session",

    initialized:
        "nova_initialized",

    lastRoute:
        "nova_last_route",

    backendStatus:
        "nova_backend_status",

    lastError:
        "nova_last_error"

};


// ============================================================
// SAFE STORAGE HELPERS
// ============================================================

function readStorage(key) {

    try {

        return localStorage.getItem(key);

    } catch (error) {

        console.warn(
            "[Nova Login] Unable to read localStorage:",
            error
        );

        return null;
    }
}


function writeStorage(
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
            "[Nova Login] Unable to write localStorage:",
            error
        );

        return false;
    }
}


function removeStorage(key) {

    try {

        localStorage.removeItem(key);

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

        return API_URL;
    }


    if (
        path.startsWith("http://") ||
        path.startsWith("https://")
    ) {

        return path;
    }


    return (
        `${API_URL}/` +
        path.replace(/^\/+/, "")
    );
}


async function fetchWithTimeout(
    url,
    options = {},
    timeout = 10000
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
// RESPONSE PARSER
// ============================================================

async function parseApiResponse(response) {

    const contentType =
        response.headers.get(
            "content-type"
        ) || "";


    if (
        contentType.includes(
            "application/json"
        )
    ) {

        try {

            return await response.json();

        } catch {

            throw new Error(
                "The server returned invalid JSON."
            );
        }
    }


    const text =
        await response.text();


    if (!text) {

        return {};
    }


    return {
        message:
            text
    };
}


// ============================================================
// USER NORMALIZATION
// ============================================================

function normalizeUser(
    data,
    email
) {

    /*
     * We preserve the fields returned by the backend
     * when they exist.
     *
     * We do NOT invent a fake user ID or fake token.
     */

    const backendUser =
        data?.user &&
        typeof data.user === "object"

            ? data.user

            : {};


    const normalizedEmail =
        (
            backendUser.email ||
            data?.email ||
            email
        )
            .trim()
            .toLowerCase();


    const user = {

        ...backendUser,

        email:
            normalizedEmail

    };


    if (
        data?.user_id !== undefined &&
        data?.user_id !== null
    ) {

        user.id =
            data.user_id;
    }


    if (
        data?.id !== undefined &&
        data?.id !== null &&
        user.id === undefined
    ) {

        user.id =
            data.id;
    }


    if (
        data?.username
    ) {

        user.username =
            data.username;
    }


    if (
        data?.name
    ) {

        user.name =
            data.name;
    }


    if (
        data?.display_name
    ) {

        user.displayName =
            data.display_name;
    }


    return user;
}


// ============================================================
// SESSION EXTRACTION
// ============================================================

function extractSession(data) {

    /*
     * Only store a session/token when the backend actually
     * gives us one.
     */

    const token =
        data?.token ||
        data?.access_token ||
        data?.session_token ||
        data?.session;


    if (
        typeof token === "string" &&
        token.trim()
    ) {

        return {

            token:
                token.trim(),

            type:
                data?.token_type ||
                "Bearer"

        };
    }


    return null;
}


// ============================================================
// EXISTING SESSION CHECK
// ============================================================

function getExistingUser() {

    const raw =
        readStorage(
            STORAGE_KEYS.user
        );


    if (!raw) {

        return null;
    }


    try {

        const parsed =
            JSON.parse(raw);


        if (
            !parsed ||
            typeof parsed !== "object"
        ) {

            return null;
        }


        if (
            !parsed.email
        ) {

            return null;
        }


        return parsed;

    } catch {

        return null;
    }
}


// ============================================================
// EMAIL VALIDATION
// ============================================================

function validateEmail(email) {

    const value =
        email
            .trim()
            .toLowerCase();


    if (!value) {

        return "Please enter your email address.";
    }


    if (!value.includes("@")) {

        return "Please enter a valid email address.";
    }


    if (
        value.startsWith("@") ||
        value.endsWith("@")
    ) {

        return "Please enter a valid email address.";
    }


    return "";
}


// ============================================================
// PASSWORD VALIDATION
// ============================================================

function validatePassword(password) {

    if (!password) {

        return "Please enter your password.";
    }


    return "";
}


// ============================================================
// LOGIN PAGE
// ============================================================

export default function Login() {

    const navigate =
        useNavigate();


    const emailRef =
        useRef(null);


    const [
        email,
        setEmail
    ] = useState("");


    const [
        password,
        setPassword
    ] = useState("");


    const [
        showPassword,
        setShowPassword
    ] = useState(false);


    const [
        loading,
        setLoading
    ] = useState(false);


    const [
        error,
        setError
    ] = useState("");


    const [
        success,
        setSuccess
    ] = useState("");


    const [
        backendStatus,
        setBackendStatus
    ] = useState(
        "checking"
    );


    const [
        rememberMe,
        setRememberMe
    ] = useState(true);


    const [
        touched,
        setTouched
    ] = useState({

        email:
            false,

        password:
            false

    });


    // ========================================================
    // MEMOIZED VALIDATION
    // ========================================================

    const emailError =
        useMemo(
            () =>
                touched.email
                    ? validateEmail(email)
                    : "",
            [
                email,
                touched.email
            ]
        );


    const passwordError =
        useMemo(
            () =>
                touched.password
                    ? validatePassword(password)
                    : "",
            [
                password,
                touched.password
            ]
        );


    const formValid =
        !validateEmail(email) &&
        !validatePassword(password);


    // ========================================================
    // BACKEND HEALTH CHECK
    // ========================================================

    const checkBackend =
        useCallback(
            async () => {

                setBackendStatus(
                    "checking"
                );


                try {

                    const response =
                        await fetchWithTimeout(
                            buildApiUrl("/health"),
                            {
                                method:
                                    "GET",

                                headers: {
                                    Accept:
                                        "application/json"
                                }
                            },
                            10000
                        );


                    if (
                        response.ok
                    ) {

                        setBackendStatus(
                            "online"
                        );


                        writeStorage(
                            STORAGE_KEYS.backendStatus,
                            "online"
                        );

                    } else {

                        setBackendStatus(
                            "degraded"
                        );


                        writeStorage(
                            STORAGE_KEYS.backendStatus,
                            "degraded"
                        );
                    }

                } catch {

                    setBackendStatus(
                        "offline"
                    );


                    writeStorage(
                        STORAGE_KEYS.backendStatus,
                        "offline"
                    );
                }

            },
            []
        );


    // ========================================================
    // INITIALIZATION
    // ========================================================

    useEffect(() => {

        document.title =
            "Login | Nova AI";


        writeStorage(
            STORAGE_KEYS.initialized,
            "true"
        );


        /*
         * If an account is already stored, pre-fill the email.
         *
         * We do not automatically redirect here because that
         * could create confusing navigation loops.
         */

        const existingUser =
            getExistingUser();


        if (
            existingUser?.email
        ) {

            setEmail(
                existingUser.email
            );
        }


        emailRef.current?.focus();


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


    // ========================================================
    // FIELD HANDLERS
    // ========================================================

    function handleEmailChange(event) {

        const value =
            event.target.value;


        setEmail(value);


        if (
            error
        ) {

            setError("");
        }


        if (
            success
        ) {

            setSuccess("");
        }
    }


    function handlePasswordChange(event) {

        const value =
            event.target.value;


        setPassword(value);


        if (
            error
        ) {

            setError("");
        }


        if (
            success
        ) {

            setSuccess("");
        }
    }


    function handleEmailBlur() {

        setTouched(
            previous => ({

                ...previous,

                email:
                    true

            })
        );
    }


    function handlePasswordBlur() {

        setTouched(
            previous => ({

                ...previous,

                password:
                    true

            })
        );
    }


    // ========================================================
    // LOGIN
    // ========================================================

    async function handleLogin(event) {

        event.preventDefault();


        setError("");
        setSuccess("");


        setTouched({

            email:
                true,

            password:
                true

        });


        const cleanEmail =
            email
                .trim()
                .toLowerCase();


        const emailValidation =
            validateEmail(
                cleanEmail
            );


        const passwordValidation =
            validatePassword(
                password
            );


        if (
            emailValidation
        ) {

            setError(
                emailValidation
            );

            emailRef.current?.focus();

            return;
        }


        if (
            passwordValidation
        ) {

            setError(
                passwordValidation
            );

            return;
        }


        if (
            loading
        ) {

            return;
        }


        setLoading(true);


        try {

            const response =
                await fetchWithTimeout(
                    buildApiUrl("/login"),
                    {

                        method:
                            "POST",

                        headers: {

                            "Content-Type":
                                "application/json",

                            Accept:
                                "application/json"

                        },

                        body:
                            JSON.stringify({

                                email:
                                    cleanEmail,

                                password:
                                    password

                            })

                    },
                    10000
                );


            const data =
                await parseApiResponse(
                    response
                );


            if (
                !response.ok
            ) {

                throw new Error(
                    data?.detail ||
                    data?.message ||
                    "Incorrect email or password."
                );
            }


            if (
                data?.success === false
            ) {

                setError(
                    data?.message ||
                    data?.detail ||
                    "Incorrect email or password."
                );

                return;
            }


            /*
             * Create the canonical Nova user object.
             *
             * This is the critical connection between login
             * and the rest of the frontend.
             */

            const user =
                normalizeUser(
                    data,
                    cleanEmail
                );


            const stored =
                writeStorage(

                    STORAGE_KEYS.user,

                    JSON.stringify(
                        user
                    )

                );


            if (!stored) {

                throw new Error(
                    "Login succeeded, but Nova could not save the account session locally."
                );
            }


            /*
             * If the backend provides a real session/token,
             * preserve it.
             *
             * If it does not, we do not manufacture one.
             */

            const session =
                extractSession(
                    data
                );


            if (
                session
            ) {

                writeStorage(

                    STORAGE_KEYS.session,

                    JSON.stringify(
                        session
                    )

                );

            } else {

                /*
                 * Remove an old session so another account's
                 * stale token cannot remain attached to this
                 * login.
                 */

                removeStorage(
                    STORAGE_KEYS.session
                );
            }


            writeStorage(
                STORAGE_KEYS.lastRoute,
                "/dashboard"
            );


            setSuccess(
                "Welcome back. Opening your Nova dashboard..."
            );


            /*
             * Small delay allows the success state to render
             * before navigation.
             */

            window.setTimeout(
                () => {

                    navigate(
                        "/dashboard",
                        {
                            replace:
                                true
                        }
                    );

                },
                450
            );

        } catch (loginError) {

            console.error(
                "[Nova Login] Login error:",
                loginError
            );


            let message =
                "Unable to connect to Nova.";


            if (
                loginError?.name ===
                "AbortError"
            ) {

                message =
                    "The Nova backend took too long to respond. Please try again.";

            } else if (
                loginError?.message
            ) {

                message =
                    loginError.message;
            }


            setError(
                message
            );


            writeStorage(

                STORAGE_KEYS.lastError,

                JSON.stringify({

                    message:
                        message,

                    timestamp:
                        new Date().toISOString(),

                    pathname:
                        window.location.pathname

                })

            );

        } finally {

            setLoading(false);
        }
    }


    // ========================================================
    // KEYBOARD SHORTCUT
    // ========================================================

    function handleFormKeyDown(event) {

        if (
            event.key === "Enter" &&
            loading
        ) {

            event.preventDefault();
        }
    }


    // ========================================================
    // BACKEND STATUS UI
    // ========================================================

    const backendStatusUI = {

        checking: {

            icon:
                <LoaderCircle
                    size={14}
                    className="animate-spin"
                />,

            text:
                "Checking Nova backend",

            className:
                "text-slate-400"

        },

        online: {

            icon:
                <Wifi
                    size={14}
                />,

            text:
                "Nova backend online",

            className:
                "text-emerald-300"

        },

        degraded: {

            icon:
                <AlertCircle
                    size={14}
                />,

            text:
                "Nova backend responding slowly",

            className:
                "text-amber-300"

        },

        offline: {

            icon:
                <WifiOff
                    size={14}
                />,

            text:
                "Nova backend unavailable",

            className:
                "text-red-300"

        }

    }[backendStatus];


    // ========================================================
    // RENDER
    // ========================================================

    return (

        <main
            className="
                min-h-screen
                bg-[#020617]
                text-white
                flex
                items-center
                justify-center
                overflow-hidden
                relative
                px-4
                py-10
                sm:px-6
            "
        >

            {/* =================================================
                BACKGROUND
                ================================================= */}

            <div
                className="
                    pointer-events-none
                    absolute
                    inset-0
                    overflow-hidden
                "
                aria-hidden="true"
            >

                <div
                    className="
                        absolute
                        -left-32
                        -top-32
                        h-96
                        w-96
                        rounded-full
                        bg-blue-600/10
                        blur-3xl
                    "
                />

                <div
                    className="
                        absolute
                        -right-32
                        top-1/3
                        h-96
                        w-96
                        rounded-full
                        bg-indigo-600/10
                        blur-3xl
                    "
                />

                <div
                    className="
                        absolute
                        bottom-[-12rem]
                        left-1/3
                        h-96
                        w-96
                        rounded-full
                        bg-cyan-500/5
                        blur-3xl
                    "
                />

            </div>


            {/* =================================================
                MAIN CARD
                ================================================= */}

            <section
                className="
                    relative
                    z-10
                    w-full
                    max-w-5xl
                    overflow-hidden
                    rounded-[2rem]
                    border
                    border-white/10
                    bg-white/[0.035]
                    shadow-2xl
                    backdrop-blur-2xl
                "
            >

                <div
                    className="
                        grid
                        lg:grid-cols-[0.9fr_1.1fr]
                    "
                >

                    {/* =========================================
                        BRAND PANEL
                        ========================================= */}

                    <div
                        className="
                            relative
                            hidden
                            lg:flex
                            flex-col
                            justify-between
                            border-r
                            border-white/10
                            bg-white/[0.025]
                            p-10
                            xl:p-12
                        "
                    >

                        <div>

                            <div
                                className="
                                    inline-flex
                                    h-14
                                    w-14
                                    items-center
                                    justify-center
                                    rounded-2xl
                                    border
                                    border-blue-400/20
                                    bg-blue-500/10
                                    text-blue-300
                                    shadow-lg
                                "
                            >

                                <Sparkles
                                    size={27}
                                />

                            </div>


                            <h2
                                className="
                                    mt-8
                                    text-3xl
                                    font-semibold
                                    tracking-tight
                                "
                            >
                                Welcome back to Nova.
                            </h2>


                            <p
                                className="
                                    mt-4
                                    max-w-sm
                                    text-sm
                                    leading-7
                                    text-slate-400
                                "
                            >
                                Continue your learning journey,
                                keep your progress synchronized,
                                and pick up exactly where you left off.
                            </p>

                        </div>


                        <div
                            className="
                                space-y-4
                            "
                        >

                            <div
                                className="
                                    flex
                                    items-center
                                    gap-3
                                    rounded-2xl
                                    border
                                    border-white/10
                                    bg-black/10
                                    p-4
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
                                        rounded-xl
                                        bg-emerald-500/10
                                        text-emerald-300
                                    "
                                >

                                    <ShieldCheck
                                        size={19}
                                    />

                                </div>


                                <div>

                                    <p
                                        className="
                                            text-sm
                                            font-medium
                                            text-white
                                        "
                                    >
                                        Your account
                                    </p>

                                    <p
                                        className="
                                            mt-0.5
                                            text-xs
                                            text-slate-500
                                        "
                                    >
                                        Your Nova profile stays connected
                                        across the application.
                                    </p>

                                </div>

                            </div>


                            <div
                                className="
                                    flex
                                    items-center
                                    gap-3
                                    rounded-2xl
                                    border
                                    border-white/10
                                    bg-black/10
                                    p-4
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
                                        rounded-xl
                                        bg-blue-500/10
                                        text-blue-300
                                    "
                                >

                                    <CheckCircle2
                                        size={19}
                                    />

                                </div>


                                <div>

                                    <p
                                        className="
                                            text-sm
                                            font-medium
                                            text-white
                                        "
                                    >
                                        Ready to learn
                                    </p>

                                    <p
                                        className="
                                            mt-0.5
                                            text-xs
                                            text-slate-500
                                        "
                                    >
                                        Dashboard, chat and learning
                                        features are ready after login.
                                    </p>

                                </div>

                            </div>

                        </div>

                    </div>


                    {/* =========================================
                        LOGIN PANEL
                        ========================================= */}

                    <div
                        className="
                            p-6
                            sm:p-8
                            lg:p-10
                            xl:p-12
                        "
                    >

                        {/* Mobile brand */}

                        <div
                            className="
                                mb-8
                                flex
                                items-center
                                gap-3
                                lg:hidden
                            "
                        >

                            <div
                                className="
                                    flex
                                    h-11
                                    w-11
                                    items-center
                                    justify-center
                                    rounded-xl
                                    bg-blue-600
                                    shadow-lg
                                "
                            >

                                <Sparkles
                                    size={21}
                                />

                            </div>


                            <div>

                                <div
                                    className="
                                        font-semibold
                                    "
                                >
                                    Nova AI
                                </div>

                                <div
                                    className="
                                        text-xs
                                        text-slate-500
                                    "
                                >
                                    Adaptive learning
                                </div>

                            </div>

                        </div>


                        {/* Header */}

                        <div
                            className="
                                mb-8
                            "
                        >

                            <div
                                className="
                                    mb-5
                                    inline-flex
                                    h-14
                                    w-14
                                    items-center
                                    justify-center
                                    rounded-2xl
                                    bg-blue-600
                                    text-white
                                    shadow-lg
                                    shadow-blue-600/20
                                    lg:hidden
                                "
                            >

                                <LogIn
                                    size={26}
                                />

                            </div>


                            <h1
                                className="
                                    text-3xl
                                    font-bold
                                    tracking-tight
                                    sm:text-4xl
                                "
                            >
                                Welcome back
                            </h1>


                            <p
                                className="
                                    mt-2
                                    text-sm
                                    leading-6
                                    text-slate-400
                                "
                            >
                                Sign in to continue learning with Nova.
                            </p>

                        </div>


                        {/* Backend status */}

                        <div
                            className="
                                mb-6
                                flex
                                items-center
                                justify-between
                                gap-3
                                rounded-xl
                                border
                                border-white/10
                                bg-black/10
                                px-3
                                py-2.5
                            "
                        >

                            <div
                                className={`
                                    flex
                                    items-center
                                    gap-2
                                    text-xs
                                    ${backendStatusUI.className}
                                `}
                            >

                                {backendStatusUI.icon}

                                <span>
                                    {backendStatusUI.text}
                                </span>

                            </div>


                            <button
                                type="button"
                                onClick={
                                    checkBackend
                                }
                                className="
                                    text-xs
                                    text-slate-500
                                    transition
                                    hover:text-white
                                "
                            >
                                Check
                            </button>

                        </div>


                        {/* Form */}

                        <form
                            onSubmit={
                                handleLogin
                            }
                            onKeyDown={
                                handleFormKeyDown
                            }
                            noValidate
                            className="
                                space-y-5
                            "
                        >

                            {/* Email */}

                            <div>

                                <label
                                    htmlFor="nova-login-email"
                                    className="
                                        mb-2
                                        block
                                        text-sm
                                        font-medium
                                        text-slate-300
                                    "
                                >
                                    Email
                                </label>


                                <div
                                    className="
                                        relative
                                    "
                                >

                                    <Mail
                                        size={17}
                                        className="
                                            pointer-events-none
                                            absolute
                                            left-4
                                            top-1/2
                                            -translate-y-1/2
                                            text-slate-500
                                        "
                                    />


                                    <input
                                        ref={emailRef}
                                        id="nova-login-email"
                                        type="email"
                                        value={email}
                                        onChange={
                                            handleEmailChange
                                        }
                                        onBlur={
                                            handleEmailBlur
                                        }
                                        placeholder="you@example.com"
                                        autoComplete="email"
                                        autoCapitalize="none"
                                        spellCheck="false"
                                        disabled={loading}
                                        aria-invalid={
                                            Boolean(
                                                emailError
                                            )
                                        }
                                        aria-describedby={
                                            emailError
                                                ? "login-email-error"
                                                : undefined
                                        }
                                        className={`
                                            w-full
                                            rounded-xl
                                            border
                                            bg-slate-950/80
                                            py-3.5
                                            pl-11
                                            pr-4
                                            text-sm
                                            text-white
                                            outline-none
                                            transition
                                            placeholder:text-slate-600
                                            disabled:cursor-not-allowed
                                            disabled:opacity-50

                                            ${
                                                emailError

                                                    ? `
                                                        border-red-500/50
                                                        focus:border-red-400
                                                      `

                                                    : `
                                                        border-white/10
                                                        focus:border-blue-500
                                                        focus:ring-4
                                                        focus:ring-blue-500/10
                                                      `
                                            }
                                        `}
                                    />

                                </div>


                                {emailError && (

                                    <p
                                        id="login-email-error"
                                        className="
                                            mt-2
                                            flex
                                            items-center
                                            gap-1.5
                                            text-xs
                                            text-red-300
                                        "
                                    >

                                        <AlertCircle
                                            size={13}
                                        />

                                        {emailError}

                                    </p>

                                )}

                            </div>


                            {/* Password */}

                            <div>

                                <div
                                    className="
                                        mb-2
                                        flex
                                        items-center
                                        justify-between
                                    "
                                >

                                    <label
                                        htmlFor="nova-login-password"
                                        className="
                                            text-sm
                                            font-medium
                                            text-slate-300
                                        "
                                    >
                                        Password
                                    </label>

                                </div>


                                <div
                                    className="
                                        relative
                                    "
                                >

                                    <KeyRound
                                        size={17}
                                        className="
                                            pointer-events-none
                                            absolute
                                            left-4
                                            top-1/2
                                            -translate-y-1/2
                                            text-slate-500
                                        "
                                    />


                                    <input
                                        id="nova-login-password"
                                        type={
                                            showPassword
                                                ? "text"
                                                : "password"
                                        }
                                        value={password}
                                        onChange={
                                            handlePasswordChange
                                        }
                                        onBlur={
                                            handlePasswordBlur
                                        }
                                        placeholder="Your password"
                                        autoComplete="current-password"
                                        disabled={loading}
                                        aria-invalid={
                                            Boolean(
                                                passwordError
                                            )
                                        }
                                        className={`
                                            w-full
                                            rounded-xl
                                            border
                                            bg-slate-950/80
                                            py-3.5
                                            pl-11
                                            pr-12
                                            text-sm
                                            text-white
                                            outline-none
                                            transition
                                            placeholder:text-slate-600
                                            disabled:cursor-not-allowed
                                            disabled:opacity-50

                                            ${
                                                passwordError

                                                    ? `
                                                        border-red-500/50
                                                        focus:border-red-400
                                                      `

                                                    : `
                                                        border-white/10
                                                        focus:border-blue-500
                                                        focus:ring-4
                                                        focus:ring-blue-500/10
                                                      `
                                            }
                                        `}
                                    />


                                    <button
                                        type="button"
                                        onClick={() =>
                                            setShowPassword(
                                                value =>
                                                    !value
                                            )
                                        }
                                        disabled={
                                            loading ||
                                            !password
                                        }
                                        className="
                                            absolute
                                            right-3
                                            top-1/2
                                            -translate-y-1/2
                                            rounded-lg
                                            p-2
                                            text-slate-500
                                            transition
                                            hover:bg-white/5
                                            hover:text-white
                                            disabled:cursor-not-allowed
                                            disabled:opacity-40
                                        "
                                        aria-label={
                                            showPassword
                                                ? "Hide password"
                                                : "Show password"
                                        }
                                    >

                                        {
                                            showPassword

                                                ? (
                                                    <EyeOff
                                                        size={17}
                                                    />
                                                )

                                                : (
                                                    <Eye
                                                        size={17}
                                                    />
                                                )
                                        }

                                    </button>

                                </div>


                                {passwordError && (

                                    <p
                                        className="
                                            mt-2
                                            flex
                                            items-center
                                            gap-1.5
                                            text-xs
                                            text-red-300
                                        "
                                    >

                                        <AlertCircle
                                            size={13}
                                        />

                                        {passwordError}

                                    </p>

                                )}

                            </div>


                            {/* Remember */}

                            <div
                                className="
                                    flex
                                    items-center
                                    justify-between
                                    gap-4
                                "
                            >

                                <label
                                    className="
                                        flex
                                        cursor-pointer
                                        items-center
                                        gap-2.5
                                        text-sm
                                        text-slate-400
                                    "
                                >

                                    <input
                                        type="checkbox"
                                        checked={
                                            rememberMe
                                        }
                                        onChange={event =>
                                            setRememberMe(
                                                event.target.checked
                                            )
                                        }
                                        className="
                                            h-4
                                            w-4
                                            rounded
                                            border-white/20
                                            bg-slate-950
                                            accent-blue-600
                                        "
                                    />

                                    Remember me

                                </label>


                                <span
                                    className="
                                        text-xs
                                        text-slate-600
                                    "
                                >
                                    Secure session
                                </span>

                            </div>


                            {/* Error */}

                            {error && (

                                <div
                                    className="
                                        flex
                                        items-start
                                        gap-3
                                        rounded-xl
                                        border
                                        border-red-500/20
                                        bg-red-500/10
                                        p-4
                                        text-sm
                                        text-red-300
                                    "
                                    role="alert"
                                >

                                    <AlertCircle
                                        size={18}
                                        className="
                                            mt-0.5
                                            shrink-0
                                        "
                                    />

                                    <span>
                                        {error}
                                    </span>

                                </div>

                            )}


                            {/* Success */}

                            {success && (

                                <div
                                    className="
                                        flex
                                        items-start
                                        gap-3
                                        rounded-xl
                                        border
                                        border-emerald-500/20
                                        bg-emerald-500/10
                                        p-4
                                        text-sm
                                        text-emerald-300
                                    "
                                    role="status"
                                >

                                    <CheckCircle2
                                        size={18}
                                        className="
                                            mt-0.5
                                            shrink-0
                                        "
                                    />

                                    <span>
                                        {success}
                                    </span>

                                </div>

                            )}


                            {/* Submit */}

                            <button
                                type="submit"
                                disabled={
                                    loading ||
                                    !formValid
                                }
                                className="
                                    group
                                    flex
                                    w-full
                                    items-center
                                    justify-center
                                    gap-2
                                    rounded-xl
                                    bg-blue-600
                                    px-4
                                    py-3.5
                                    text-sm
                                    font-semibold
                                    text-white
                                    shadow-lg
                                    shadow-blue-600/20
                                    transition
                                    hover:bg-blue-500
                                    hover:shadow-blue-500/25
                                    active:scale-[0.99]
                                    disabled:cursor-not-allowed
                                    disabled:bg-slate-800
                                    disabled:text-slate-500
                                    disabled:shadow-none
                                "
                            >

                                {loading ? (

                                    <>
                                        <LoaderCircle
                                            size={18}
                                            className="animate-spin"
                                        />

                                        Signing in...

                                    </>

                                ) : (

                                    <>
                                        <LogIn
                                            size={18}
                                        />

                                        Sign in

                                        <ArrowRight
                                            size={17}
                                            className="
                                                transition
                                                group-hover:translate-x-0.5
                                            "
                                        />

                                    </>

                                )}

                            </button>


                            {/* Register */}

                            <p
                                className="
                                    pt-2
                                    text-center
                                    text-sm
                                    text-slate-500
                                "
                            >

                                Don't have an account?{" "}

                                <Link
                                    to="/register"
                                    className="
                                        font-medium
                                        text-blue-400
                                        transition
                                        hover:text-blue-300
                                    "
                                >
                                    Create one
                                </Link>

                            </p>

                        </form>


                        {/* Footer */}

                        <div
                            className="
                                mt-8
                                flex
                                items-center
                                justify-center
                                gap-2
                                text-xs
                                text-slate-600
                            "
                        >

                            <UserRound
                                size={13}
                            />

                            Your Nova account connects
                            your learning experience.

                        </div>

                    </div>

                </div>

            </section>

        </main>
    );
}
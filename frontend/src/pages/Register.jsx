import {
    useCallback,
    useEffect,
    useRef,
    useState
} from "react";

import {
    Link,
    useNavigate
} from "react-router-dom";

import {
    AlertCircle,
    Check,
    CheckCircle2,
    Eye,
    EyeOff,
    LoaderCircle,
    LockKeyhole,
    Mail,
    RefreshCw,
    ShieldCheck,
    UserPlus,
    WifiOff
} from "lucide-react";


// ============================================================
// NOVA REGISTER CONFIGURATION
// ============================================================

const API_URL = (
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const REGISTER_ENDPOINT =
    `${API_URL}/register`;

const LOGIN_ROUTE =
    "/login";

const CHAT_ROUTE =
    "/chat";

const USER_STORAGE_KEY =
    "nova_user";

const REGISTER_TIMEOUT =
    10000;

const MIN_PASSWORD_LENGTH =
    6;


// ============================================================
// SAFE STORAGE
// ============================================================

function getStoredUser() {

    try {

        const value =
            localStorage.getItem(
                USER_STORAGE_KEY
            );

        if (!value) {

            return null;
        }

        const user =
            JSON.parse(value);

        if (
            !user ||
            typeof user !== "object"
        ) {

            return null;
        }

        return user;

    } catch (error) {

        console.warn(
            "[Nova] Unable to read stored user:",
            error
        );

        return null;
    }
}


function setStoredUser(user) {

    try {

        localStorage.setItem(
            USER_STORAGE_KEY,
            JSON.stringify(user)
        );

        return true;

    } catch (error) {

        console.error(
            "[Nova] Unable to save authenticated user:",
            error
        );

        return false;
    }
}


function removeStoredUser() {

    try {

        localStorage.removeItem(
            USER_STORAGE_KEY
        );

    } catch (error) {

        console.warn(
            "[Nova] Unable to clear stored user:",
            error
        );
    }
}


// ============================================================
// USER NORMALIZATION
// ============================================================

function normalizeUser(data, fallbackEmail) {

    const source =
        data?.user ||
        data?.account ||
        data?.profile ||
        data ||
        {};


    const email = String(
        source.email ||
        fallbackEmail ||
        ""
    )
        .trim()
        .toLowerCase();


    if (!email) {

        return null;
    }


    return {

        email,

        name:
            source.name ||
            source.username ||
            source.display_name ||
            source.displayName ||
            "",

        username:
            source.username ||
            "",

        id:
            source.id ||
            source.user_id ||
            source.userId ||
            null

    };
}


// ============================================================
// EMAIL VALIDATION
// ============================================================

function isValidEmail(email) {

    const value =
        email.trim().toLowerCase();


    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        .test(value);
}


// ============================================================
// PASSWORD VALIDATION
// ============================================================

function validatePassword(password) {

    const errors = [];


    if (
        password.length <
        MIN_PASSWORD_LENGTH
    ) {

        errors.push(
            `Password must be at least ${MIN_PASSWORD_LENGTH} characters.`
        );
    }


    return errors;
}


// ============================================================
// PASSWORD STRENGTH
// ============================================================

function getPasswordStrength(password) {

    if (!password) {

        return {
            score: 0,
            label: "",
            valid: false
        };
    }


    let score = 0;


    if (
        password.length >= 6
    ) {

        score++;
    }


    if (
        password.length >= 10
    ) {

        score++;
    }


    if (
        /[A-Z]/.test(password)
    ) {

        score++;
    }


    if (
        /[0-9]/.test(password)
    ) {

        score++;
    }


    if (
        /[^A-Za-z0-9]/.test(password)
    ) {

        score++;
    }


    const labels = [

        "",

        "Very weak",

        "Weak",

        "Fair",

        "Good",

        "Strong"

    ];


    return {

        score,

        label:
            labels[score],

        valid:
            password.length >=
            MIN_PASSWORD_LENGTH

    };
}


// ============================================================
// API REQUEST
// ============================================================

async function registerRequest(
    email,
    password,
    signal
) {

    const response =
        await fetch(
            REGISTER_ENDPOINT,
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

                        email,

                        password

                    }),

                signal

            }
        );


    let data = null;


    try {

        data =
            await response.json();

    } catch {

        if (
            !response.ok
        ) {

            throw new Error(
                `Registration failed (${response.status}).`
            );
        }


        throw new Error(
            "The server returned an invalid response."
        );
    }


    if (
        !response.ok
    ) {

        const message =
            data?.detail ||
            data?.message ||
            data?.error ||
            `Registration failed (${response.status}).`;


        throw new Error(
            typeof message === "string"
                ? message
                : "Registration failed."
        );
    }


    return data;
}


// ============================================================
// AUTH EVENT
// ============================================================

function dispatchAuthEvent(
    user
) {

    try {

        window.dispatchEvent(
            new CustomEvent(
                "nova:auth",
                {
                    detail: {
                        type:
                            "login",

                        user
                    }
                }
            )
        );

    } catch (error) {

        console.warn(
            "[Nova] Unable to dispatch auth event:",
            error
        );
    }
}


// ============================================================
// REGISTER PAGE
// ============================================================

export default function Register() {

    const navigate =
        useNavigate();


    const [
        email,
        setEmail
    ] = useState("");


    const [
        password,
        setPassword
    ] = useState("");


    const [
        confirmPassword,
        setConfirmPassword
    ] = useState("");


    const [
        showPassword,
        setShowPassword
    ] = useState(false);


    const [
        showConfirmPassword,
        setShowConfirmPassword
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
        touched,
        setTouched
    ] = useState({

        email:
            false,

        password:
            false,

        confirmPassword:
            false

    });


    const abortRef =
        useRef(null);


    const mountedRef =
        useRef(true);


    const redirectTimerRef =
        useRef(null);


    // ========================================================
    // CLEANUP
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


            if (
                redirectTimerRef.current
            ) {

                clearTimeout(
                    redirectTimerRef.current
                );
            }

        };

    }, []);


    // ========================================================
    // FORM VALUES
    // ========================================================

    const cleanEmail =
        email.trim().toLowerCase();


    const passwordStrength =
        getPasswordStrength(
            password
        );


    const emailError =
        touched.email &&
        cleanEmail &&
        !isValidEmail(cleanEmail)

            ? "Please enter a valid email address."

            : "";


    const passwordErrors =
        validatePassword(
            password
        );


    const passwordError =
        touched.password &&
        passwordErrors.length > 0

            ? passwordErrors[0]

            : "";


    const confirmPasswordError =
        touched.confirmPassword &&
        confirmPassword &&
        confirmPassword !== password

            ? "Passwords do not match."

            : "";


    // ========================================================
    // FORM VALIDATION
    // ========================================================

    const validateForm =
        useCallback(() => {

            if (
                !cleanEmail
            ) {

                return "Please enter your email address.";
            }


            if (
                !isValidEmail(cleanEmail)
            ) {

                return "Please enter a valid email address.";
            }


            if (
                password.length <
                MIN_PASSWORD_LENGTH
            ) {

                return (
                    `Password must be at least ` +
                    `${MIN_PASSWORD_LENGTH} characters.`
                );
            }


            if (
                password !==
                confirmPassword
            ) {

                return "Passwords do not match.";
            }


            return "";

        }, [
            cleanEmail,
            password,
            confirmPassword
        ]);


    // ========================================================
    // HANDLE REGISTER
    // ========================================================

    const handleRegister =
        useCallback(
            async event => {

                event.preventDefault();


                if (
                    loading
                ) {

                    return;
                }


                setError("");
                setSuccess("");


                setTouched({

                    email:
                        true,

                    password:
                        true,

                    confirmPassword:
                        true

                });


                const validationError =
                    validateForm();


                if (
                    validationError
                ) {

                    setError(
                        validationError
                    );

                    return;
                }


                // ------------------------------------------------
                // Cancel previous request
                // ------------------------------------------------

                if (
                    abortRef.current
                ) {

                    abortRef.current.abort();
                }


                const controller =
                    new AbortController();


                abortRef.current =
                    controller;


                const timeoutId =
                    setTimeout(
                        () => {

                            controller.abort();

                        },
                        REGISTER_TIMEOUT
                    );


                setLoading(
                    true
                );


                try {

                    const data =
                        await registerRequest(
                            cleanEmail,
                            password,
                            controller.signal
                        );


                    if (
                        !mountedRef.current
                    ) {

                        return;
                    }


                    // ------------------------------------------------
                    // Backend success validation
                    // ------------------------------------------------

                    if (
                        data?.success === false
                    ) {

                        throw new Error(
                            data.message ||
                            "An account with this email may already exist."
                        );
                    }


                    // ------------------------------------------------
                    // Build the user object that the rest of Nova
                    // already expects.
                    // ------------------------------------------------

                    const user =
                        normalizeUser(
                            data,
                            cleanEmail
                        );


                    if (!user) {

                        throw new Error(
                            "The account was created, but Nova could not determine the account email."
                        );
                    }


                    // ------------------------------------------------
                    // IMPORTANT:
                    //
                    // Chat.jsx expects:
                    //
                    // localStorage["nova_user"]
                    //
                    // and specifically expects an email.
                    // ------------------------------------------------

                    const stored =
                        setStoredUser(
                            user
                        );


                    if (!stored) {

                        throw new Error(
                            "Your account was created, but Nova could not save the local account session."
                        );
                    }


                    // ------------------------------------------------
                    // Verify immediately that the account can actually
                    // be read back.
                    // ------------------------------------------------

                    const savedUser =
                        getStoredUser();


                    if (
                        !savedUser?.email ||
                        savedUser.email !==
                            cleanEmail
                    ) {

                        throw new Error(
                            "Your account was created, but Nova could not verify the local account session."
                        );
                    }


                    // ------------------------------------------------
                    // Tell the rest of the frontend that authentication
                    // has changed.
                    // ------------------------------------------------

                    dispatchAuthEvent(
                        savedUser
                    );


                    setSuccess(
                        "Account created successfully!"
                    );


                    // ------------------------------------------------
                    // Enter Nova after a short confirmation.
                    // ------------------------------------------------

                    redirectTimerRef.current =
                        setTimeout(
                            () => {

                                if (
                                    mountedRef.current
                                ) {

                                    navigate(
                                        CHAT_ROUTE,
                                        {
                                            replace:
                                                true
                                        }
                                    );
                                }

                            },
                            500
                        );

                } catch (requestError) {

                    if (
                        !mountedRef.current
                    ) {

                        return;
                    }


                    // ------------------------------------------------
                    // Abort / timeout
                    // ------------------------------------------------

                    if (
                        requestError?.name ===
                        "AbortError"
                    ) {

                        setError(
                            "Nova took too long to respond. Please check that the backend is running and try again."
                        );

                        return;
                    }


                    // ------------------------------------------------
                    // Network error
                    // ------------------------------------------------

                    if (
                        requestError instanceof
                        TypeError
                    ) {

                        setError(
                            "Unable to connect to Nova. Please make sure the backend is running."
                        );

                        return;
                    }


                    // ------------------------------------------------
                    // Backend error
                    // ------------------------------------------------

                    setError(
                        requestError?.message ||
                        "Unable to create your account."
                    );


                } finally {

                    clearTimeout(
                        timeoutId
                    );


                    if (
                        mountedRef.current
                    ) {

                        setLoading(
                            false
                        );
                    }

                }

            },
            [
                loading,
                cleanEmail,
                password,
                validateForm,
                navigate
            ]
        );


    // ========================================================
    // INPUT HANDLERS
    // ========================================================

    const handleEmailChange =
        event => {

            setEmail(
                event.target.value
            );


            if (
                error
            ) {

                setError("");
            }
        };


    const handlePasswordChange =
        event => {

            setPassword(
                event.target.value
            );


            if (
                error
            ) {

                setError("");
            }
        };


    const handleConfirmPasswordChange =
        event => {

            setConfirmPassword(
                event.target.value
            );


            if (
                error
            ) {

                setError("");
            }
        };


    // ========================================================
    // ALREADY LOGGED IN
    // ========================================================

    const existingUser =
        getStoredUser();


    // ========================================================
    // RENDER
    // ========================================================

    return (

        <main
            className="
                min-h-screen
                bg-gray-950
                text-white
                flex
                items-center
                justify-center
                px-5
                py-10
            "
        >

            <div
                className="
                    w-full
                    max-w-md
                "
            >

                {/* =================================================
                    HEADER
                   ================================================= */}

                <div
                    className="
                        text-center
                        mb-8
                    "
                >

                    <div
                        className="
                            inline-flex
                            items-center
                            justify-center
                            w-16
                            h-16
                            rounded-2xl
                            bg-blue-600
                            shadow-lg
                            shadow-blue-600/20
                        "
                    >

                        <UserPlus
                            size={28}
                        />

                    </div>


                    <h1
                        className="
                            mt-5
                            text-3xl
                            sm:text-4xl
                            font-bold
                            tracking-tight
                        "
                    >
                        Create your account
                    </h1>


                    <p
                        className="
                            text-gray-400
                            mt-3
                            text-sm
                            leading-6
                        "
                    >
                        Start learning with Nova.
                    </p>

                </div>


                {/* =================================================
                    EXISTING SESSION NOTICE
                   ================================================= */}

                {
                    existingUser?.email &&

                    <div
                        className="
                            mb-5
                            rounded-2xl
                            border
                            border-blue-500/20
                            bg-blue-500/10
                            p-4
                            text-sm
                            text-blue-200
                        "
                    >

                        <div
                            className="
                                flex
                                items-start
                                gap-3
                            "
                        >

                            <ShieldCheck
                                size={19}
                                className="
                                    mt-0.5
                                    shrink-0
                                "
                            />


                            <div>

                                <p
                                    className="
                                        font-medium
                                    "
                                >
                                    You're already signed in.
                                </p>


                                <p
                                    className="
                                        mt-1
                                        text-blue-300/80
                                    "
                                >
                                    {existingUser.email}
                                </p>


                                <Link
                                    to={CHAT_ROUTE}
                                    className="
                                        mt-3
                                        inline-block
                                        font-medium
                                        text-blue-300
                                        hover:text-blue-200
                                    "
                                >
                                    Continue to Nova →
                                </Link>

                            </div>

                        </div>

                    </div>
                }


                {/* =================================================
                    FORM
                   ================================================= */}

                <form
                    onSubmit={
                        handleRegister
                    }
                    noValidate
                    className="
                        bg-gray-900
                        border
                        border-gray-800
                        rounded-3xl
                        p-6
                        sm:p-7
                        space-y-5
                        shadow-2xl
                    "
                >

                    {/* =================================================
                        EMAIL
                       ================================================= */}

                    <div>

                        <label
                            htmlFor="register-email"
                            className="
                                block
                                text-sm
                                font-medium
                                text-gray-300
                                mb-2
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
                                size={18}
                                className="
                                    absolute
                                    left-4
                                    top-1/2
                                    -translate-y-1/2
                                    text-gray-500
                                    pointer-events-none
                                "
                            />


                            <input
                                id="register-email"
                                type="email"
                                value={email}
                                onChange={
                                    handleEmailChange
                                }
                                onBlur={() =>
                                    setTouched(
                                        previous => ({
                                            ...previous,
                                            email:
                                                true
                                        })
                                    )
                                }
                                placeholder="you@example.com"
                                autoComplete="email"
                                disabled={loading}
                                aria-invalid={
                                    Boolean(
                                        emailError
                                    )
                                }
                                className="
                                    w-full
                                    bg-gray-950
                                    border
                                    border-gray-700
                                    rounded-xl
                                    pl-11
                                    pr-4
                                    py-3
                                    outline-none
                                    transition
                                    focus:border-blue-500
                                    focus:ring-2
                                    focus:ring-blue-500/10
                                    disabled:opacity-50
                                "
                            />

                        </div>


                        {
                            emailError &&

                            <p
                                className="
                                    mt-2
                                    text-xs
                                    text-red-400
                                "
                            >
                                {emailError}
                            </p>
                        }

                    </div>


                    {/* =================================================
                        PASSWORD
                       ================================================= */}

                    <div>

                        <label
                            htmlFor="register-password"
                            className="
                                block
                                text-sm
                                font-medium
                                text-gray-300
                                mb-2
                            "
                        >
                            Password
                        </label>


                        <div
                            className="
                                relative
                            "
                        >

                            <LockKeyhole
                                size={18}
                                className="
                                    absolute
                                    left-4
                                    top-1/2
                                    -translate-y-1/2
                                    text-gray-500
                                    pointer-events-none
                                "
                            />


                            <input
                                id="register-password"
                                type={
                                    showPassword
                                        ? "text"
                                        : "password"
                                }
                                value={password}
                                onChange={
                                    handlePasswordChange
                                }
                                onBlur={() =>
                                    setTouched(
                                        previous => ({
                                            ...previous,
                                            password:
                                                true
                                        })
                                    )
                                }
                                placeholder="Create a password"
                                autoComplete="new-password"
                                disabled={loading}
                                className="
                                    w-full
                                    bg-gray-950
                                    border
                                    border-gray-700
                                    rounded-xl
                                    pl-11
                                    pr-12
                                    py-3
                                    outline-none
                                    transition
                                    focus:border-blue-500
                                    focus:ring-2
                                    focus:ring-blue-500/10
                                    disabled:opacity-50
                                "
                            />


                            <button
                                type="button"
                                onClick={() =>
                                    setShowPassword(
                                        value =>
                                            !value
                                    )
                                }
                                disabled={loading}
                                className="
                                    absolute
                                    right-3
                                    top-1/2
                                    -translate-y-1/2
                                    rounded-lg
                                    p-2
                                    text-gray-500
                                    hover:bg-white/5
                                    hover:text-gray-300
                                    disabled:opacity-50
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


                        {
                            password &&

                            <div
                                className="
                                    mt-3
                                "
                            >

                                <div
                                    className="
                                        flex
                                        gap-1
                                    "
                                >

                                    {
                                        [1, 2, 3, 4, 5]
                                            .map(
                                                level => (

                                                    <div
                                                        key={
                                                            level
                                                        }
                                                        className={`
                                                            h-1
                                                            flex-1
                                                            rounded-full
                                                            ${
                                                                level <=
                                                                passwordStrength.score
                                                                    ? "bg-blue-500"
                                                                    : "bg-gray-800"
                                                            }
                                                        `}
                                                    />

                                                )
                                            )
                                    }

                                </div>


                                <p
                                    className="
                                        mt-2
                                        text-xs
                                        text-gray-500
                                    "
                                >
                                    {
                                        passwordStrength.label ||
                                        "Enter a password"
                                    }
                                </p>

                            </div>
                        }


                        {
                            passwordError &&

                            <p
                                className="
                                    mt-2
                                    text-xs
                                    text-red-400
                                "
                            >
                                {passwordError}
                            </p>
                        }

                    </div>


                    {/* =================================================
                        CONFIRM PASSWORD
                       ================================================= */}

                    <div>

                        <label
                            htmlFor="register-confirm-password"
                            className="
                                block
                                text-sm
                                font-medium
                                text-gray-300
                                mb-2
                            "
                        >
                            Confirm password
                        </label>


                        <div
                            className="
                                relative
                            "
                        >

                            <LockKeyhole
                                size={18}
                                className="
                                    absolute
                                    left-4
                                    top-1/2
                                    -translate-y-1/2
                                    text-gray-500
                                    pointer-events-none
                                "
                            />


                            <input
                                id="register-confirm-password"
                                type={
                                    showConfirmPassword
                                        ? "text"
                                        : "password"
                                }
                                value={
                                    confirmPassword
                                }
                                onChange={
                                    handleConfirmPasswordChange
                                }
                                onBlur={() =>
                                    setTouched(
                                        previous => ({
                                            ...previous,
                                            confirmPassword:
                                                true
                                        })
                                    )
                                }
                                placeholder="Confirm your password"
                                autoComplete="new-password"
                                disabled={loading}
                                aria-invalid={
                                    Boolean(
                                        confirmPasswordError
                                    )
                                }
                                className="
                                    w-full
                                    bg-gray-950
                                    border
                                    border-gray-700
                                    rounded-xl
                                    pl-11
                                    pr-12
                                    py-3
                                    outline-none
                                    transition
                                    focus:border-blue-500
                                    focus:ring-2
                                    focus:ring-blue-500/10
                                    disabled:opacity-50
                                "
                            />


                            <button
                                type="button"
                                onClick={() =>
                                    setShowConfirmPassword(
                                        value =>
                                            !value
                                    )
                                }
                                disabled={loading}
                                className="
                                    absolute
                                    right-3
                                    top-1/2
                                    -translate-y-1/2
                                    rounded-lg
                                    p-2
                                    text-gray-500
                                    hover:bg-white/5
                                    hover:text-gray-300
                                    disabled:opacity-50
                                "
                                aria-label={
                                    showConfirmPassword
                                        ? "Hide confirmation password"
                                        : "Show confirmation password"
                                }
                            >

                                {
                                    showConfirmPassword

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


                        {
                            confirmPasswordError &&

                            <p
                                className="
                                    mt-2
                                    text-xs
                                    text-red-400
                                "
                            >
                                {confirmPasswordError}
                            </p>
                        }

                    </div>


                    {/* =================================================
                        ERROR
                       ================================================= */}

                    {
                        error &&

                        <div
                            className="
                                flex
                                items-start
                                gap-3
                                bg-red-950/60
                                border
                                border-red-800/60
                                text-red-300
                                rounded-xl
                                p-4
                                text-sm
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
                    }


                    {/* =================================================
                        SUCCESS
                       ================================================= */}

                    {
                        success &&

                        <div
                            className="
                                flex
                                items-start
                                gap-3
                                bg-green-950/60
                                border
                                border-green-800/60
                                text-green-300
                                rounded-xl
                                p-4
                                text-sm
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
                    }


                    {/* =================================================
                        SUBMIT
                       ================================================= */}

                    <button
                        type="submit"
                        disabled={loading}
                        className="
                            w-full
                            bg-blue-600
                            hover:bg-blue-700
                            active:bg-blue-800
                            disabled:bg-gray-700
                            disabled:cursor-not-allowed
                            rounded-xl
                            py-3
                            font-semibold
                            transition
                            flex
                            items-center
                            justify-center
                            gap-2
                        "
                    >

                        {
                            loading

                                ? (
                                    <>
                                        <LoaderCircle
                                            size={18}
                                            className="animate-spin"
                                        />

                                        Creating account...
                                    </>
                                )

                                : (
                                    <>
                                        <UserPlus
                                            size={18}
                                        />

                                        Create account
                                    </>
                                )
                        }

                    </button>


                    {/* =================================================
                        SECURITY NOTE
                       ================================================= */}

                    <div
                        className="
                            flex
                            items-start
                            gap-3
                            rounded-xl
                            border
                            border-gray-800
                            bg-gray-950/50
                            p-3
                        "
                    >

                        <ShieldCheck
                            size={17}
                            className="
                                mt-0.5
                                shrink-0
                                text-gray-500
                            "
                        />


                        <p
                            className="
                                text-xs
                                leading-5
                                text-gray-500
                            "
                        >
                            Your account is created through
                            Nova's backend. Nova then stores
                            the account identity locally so
                            the rest of the application can
                            associate your activity with your
                            account.
                        </p>

                    </div>


                    {/* =================================================
                        LOGIN
                       ================================================= */}

                    <p
                        className="
                            text-center
                            text-gray-400
                            text-sm
                        "
                    >

                        Already have an account?{" "}


                        <Link
                            to={
                                LOGIN_ROUTE
                            }
                            className="
                                text-blue-400
                                hover:text-blue-300
                                font-medium
                            "
                        >
                            Sign in
                        </Link>

                    </p>

                </form>

            </div>

        </main>
    );
}
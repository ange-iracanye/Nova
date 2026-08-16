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
    ArrowLeft,
    User,
    Brain,
    MessageSquare,
    SlidersHorizontal,
    Lightbulb,
    RotateCcw,
    Check,
    Sparkles,
    Save,
    Search,
    Download,
    Upload,
    ChevronDown,
    AlertTriangle,
    Info,
    ShieldCheck,
    X,
    RefreshCw,
    Keyboard,
    Trash2,
    CircleHelp,
    Settings as SettingsIcon,
    BookOpen,
    Zap,
    GraduationCap,
    Wand2
} from "lucide-react";


const API_URL =
    "http://127.0.0.1:8000";


const SETTINGS_ENDPOINT =
    `${API_URL}/settings`;


const LOCAL_SETTINGS_KEY =
    "nova_settings";


const SETTINGS_VERSION =
    1;


const REQUEST_TIMEOUT =
    12000;


/* ============================================================
   DEFAULT SETTINGS
============================================================ */

const DEFAULT_SETTINGS = {

    name: "",

    language: "English",

    level: "High School",

    teaching_style: "adaptive",

    difficulty: "adaptive",

    hints: "when_needed",

    step_by_step: true,

    adaptive_learning: true,

    response_length: "balanced",

    tone: "friendly",

    use_examples: true,

    use_analogies: true,

    encouragement: true,

    correction_style: "explain",

    show_correct_answer: true,

    creativity: "medium",

    behavior: "",

    custom_instructions: ""
};


/* ============================================================
   VALID VALUES
============================================================ */

const VALID_OPTIONS = {

    language: [
        "English",
        "French"
    ],

    level: [
        "Middle School",
        "High School",
        "University"
    ],

    teaching_style: [
        "adaptive",
        "step_by_step",
        "socratic",
        "direct"
    ],

    difficulty: [
        "adaptive",
        "easy",
        "normal",
        "advanced"
    ],

    hints: [
        "when_needed",
        "always",
        "never"
    ],

    response_length: [
        "concise",
        "balanced",
        "detailed"
    ],

    tone: [
        "friendly",
        "professional",
        "academic",
        "casual"
    ],

    correction_style: [
        "explain",
        "gentle",
        "strict",
        "minimal"
    ],

    creativity: [
        "low",
        "medium",
        "high"
    ]

};


const BOOLEAN_FIELDS = [

    "step_by_step",
    "adaptive_learning",
    "use_examples",
    "use_analogies",
    "encouragement",
    "show_correct_answer"

];


/* ============================================================
   PRESETS
============================================================ */

const PRESETS = {

    balanced: {

        label: "Balanced",

        description:
            "A general-purpose setup for everyday learning.",

        values: {

            teaching_style:
                "adaptive",

            difficulty:
                "adaptive",

            hints:
                "when_needed",

            step_by_step:
                true,

            adaptive_learning:
                true,

            response_length:
                "balanced",

            tone:
                "friendly",

            use_examples:
                true,

            use_analogies:
                true,

            encouragement:
                true,

            correction_style:
                "explain",

            show_correct_answer:
                true,

            creativity:
                "medium"

        }

    },


    exam: {

        label: "Exam preparation",

        description:
            "More direct answers, structured explanations and precise corrections.",

        values: {

            teaching_style:
                "step_by_step",

            difficulty:
                "normal",

            hints:
                "when_needed",

            step_by_step:
                true,

            adaptive_learning:
                true,

            response_length:
                "detailed",

            tone:
                "academic",

            use_examples:
                true,

            use_analogies:
                false,

            encouragement:
                false,

            correction_style:
                "strict",

            show_correct_answer:
                true,

            creativity:
                "low"

        }

    },


    beginner: {

        label: "Beginner",

        description:
            "Slower explanations with more examples and guidance.",

        values: {

            teaching_style:
                "adaptive",

            difficulty:
                "easy",

            hints:
                "always",

            step_by_step:
                true,

            adaptive_learning:
                true,

            response_length:
                "detailed",

            tone:
                "friendly",

            use_examples:
                true,

            use_analogies:
                true,

            encouragement:
                true,

            correction_style:
                "gentle",

            show_correct_answer:
                true,

            creativity:
                "medium"

        }

    },


    focused: {

        label: "Focused",

        description:
            "Shorter responses with minimal distractions.",

        values: {

            teaching_style:
                "direct",

            difficulty:
                "normal",

            hints:
                "when_needed",

            step_by_step:
                false,

            adaptive_learning:
                true,

            response_length:
                "concise",

            tone:
                "professional",

            use_examples:
                true,

            use_analogies:
                false,

            encouragement:
                false,

            correction_style:
                "minimal",

            show_correct_answer:
                true,

            creativity:
                "low"

        }

    }

};


/* ============================================================
   HELPERS
============================================================ */

function cloneDefaults() {

    return {
        ...DEFAULT_SETTINGS
    };

}


function cloneSettings(
    settings
) {

    return {
        ...DEFAULT_SETTINGS,
        ...settings
    };

}


function safeString(
    value,
    fallback = ""
) {

    if (
        typeof value ===
        "string"
    ) {

        return value;

    }

    return fallback;

}


function safeBoolean(
    value,
    fallback
) {

    if (
        typeof value ===
        "boolean"
    ) {

        return value;

    }

    return fallback;

}


function sanitizeSettings(
    incoming
) {

    const source =
        incoming &&
        typeof incoming === "object"
            ? incoming
            : {};


    const result = {
        ...DEFAULT_SETTINGS
    };


    result.name =
        safeString(
            source.name
        ).slice(
            0,
            100
        );


    for (
        const field of Object.keys(
            VALID_OPTIONS
        )
    ) {

        if (
            VALID_OPTIONS[field].includes(
                source[field]
            )
        ) {

            result[field] =
                source[field];

        }

    }


    for (
        const field of BOOLEAN_FIELDS
    ) {

        result[field] =
            safeBoolean(
                source[field],
                DEFAULT_SETTINGS[field]
            );

    }


    result.behavior =
        safeString(
            source.behavior
        ).slice(
            0,
            3000
        );


    result.custom_instructions =
        safeString(
            source.custom_instructions
        ).slice(
            0,
            5000
        );


    return result;

}


function settingsEqual(
    first,
    second
) {

    return (
        JSON.stringify(
            first
        ) ===
        JSON.stringify(
            second
        )
    );

}


function getStoredUser() {

    try {

        const raw =
            localStorage.getItem(
                "nova_user"
            );


        if (!raw) {

            return null;

        }


        const parsed =
            JSON.parse(
                raw
            );


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


function readLocalSettings() {

    try {

        const raw =
            localStorage.getItem(
                LOCAL_SETTINGS_KEY
            );


        if (!raw) {

            return null;

        }


        const parsed =
            JSON.parse(
                raw
            );


        if (
            !parsed ||
            typeof parsed !== "object"
        ) {

            return null;

        }


        return sanitizeSettings(
            parsed.settings ||
            parsed
        );

    } catch {

        return null;

    }

}


function cacheSettings(
    settings
) {

    try {

        localStorage.setItem(

            LOCAL_SETTINGS_KEY,

            JSON.stringify({

                version:
                    SETTINGS_VERSION,

                settings

            })

        );

    } catch {

        /*
         * localStorage can fail in private
         * browsing or restricted environments.
         *
         * The backend remains the source of truth.
         */

    }

}


function createTimeoutSignal(
    controller
) {

    return setTimeout(
        () =>
            controller.abort(),
        REQUEST_TIMEOUT
    );

}


async function fetchWithTimeout(
    url,
    options = {}
) {

    const controller =
        new AbortController();


    const timeout =
        createTimeoutSignal(
            controller
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
            timeout
        );

    }

}


function getErrorMessage(
    error
) {

    if (
        error?.name ===
        "AbortError"
    ) {

        return (
            "The request took too long. "
            +
            "Check that the Nova backend is running."
        );

    }


    if (
        error?.message
    ) {

        return error.message;

    }


    return (
        "An unexpected error occurred."
    );

}


/* ============================================================
   MAIN COMPONENT
============================================================ */

export default function Settings() {

    const navigate =
        useNavigate();


    const [
        settings,
        setSettings
    ] = useState(
        cloneDefaults()
    );


    const [
        originalSettings,
        setOriginalSettings
    ] = useState(
        cloneDefaults()
    );


    const [
        loading,
        setLoading
    ] = useState(true);


    const [
        saving,
        setSaving
    ] = useState(false);


    const [
        saved,
        setSaved
    ] = useState(false);


    const [
        error,
        setError
    ] = useState("");


    const [
        search,
        setSearch
    ] = useState("");


    const [
        openSections,
        setOpenSections
    ] = useState({

        profile:
            true,

        teaching:
            true,

        response:
            true,

        corrections:
            true,

        ai:
            true,

        custom:
            true

    });


    const [
        showImport,
        setShowImport
    ] = useState(false);


    const [
        importText,
        setImportText
    ] = useState("");


    const [
        importError,
        setImportError
    ] = useState("");


    const mountedRef =
        useRef(true);


    const fileInputRef =
        useRef(null);


    const saveTimerRef =
        useRef(null);


    /* ========================================================
       DIRTY STATE
    ======================================================== */

    const dirty =
        useMemo(
            () =>
                !settingsEqual(
                    settings,
                    originalSettings
                ),
            [
                settings,
                originalSettings
            ]
        );


    /* ========================================================
       USER
    ======================================================== */

    const user =
        useMemo(
            () =>
                getStoredUser(),
            []
        );


    /* ========================================================
       LOAD SETTINGS
    ======================================================== */

    const loadSettings =
        useCallback(
            async () => {

                if (
                    !mountedRef.current
                ) {

                    return;

                }


                setLoading(true);

                setError("");


                try {

                    const response =
                        await fetchWithTimeout(
                            SETTINGS_ENDPOINT
                        );


                    if (
                        !response.ok
                    ) {

                        throw new Error(
                            `Failed to load settings (HTTP ${response.status}).`
                        );

                    }


                    const data =
                        await response.json();


                    const normalized =
                        sanitizeSettings(
                            data
                        );


                    if (
                        !mountedRef.current
                    ) {

                        return;

                    }


                    setSettings(
                        normalized
                    );


                    setOriginalSettings(
                        normalized
                    );


                    cacheSettings(
                        normalized
                    );


                    setSaved(false);

                } catch (
                    err
                ) {

                    console.error(
                        "Nova settings load error:",
                        err
                    );


                    /*
                     * Local cache is only a fallback.
                     * We don't pretend it is the backend.
                     */

                    const cached =
                        readLocalSettings();


                    if (
                        cached &&
                        mountedRef.current
                    ) {

                        setSettings(
                            cached
                        );

                        setOriginalSettings(
                            cached
                        );


                        setError(
                            "The backend could not be reached. Showing your last locally cached settings."
                        );

                    } else if (
                        mountedRef.current
                    ) {

                        setError(
                            getErrorMessage(
                                err
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

                    }

                }

            },
            []
        );


    /* ========================================================
       INITIALIZATION
    ======================================================== */

    useEffect(
        () => {

            mountedRef.current =
                true;


            loadSettings();


            return () => {

                mountedRef.current =
                    false;


                if (
                    saveTimerRef.current
                ) {

                    clearTimeout(
                        saveTimerRef.current
                    );

                }

            };

        },
        [
            loadSettings
        ]
    );


    /* ========================================================
       BEFORE UNLOAD
    ======================================================== */

    useEffect(
        () => {

            function handleBeforeUnload(
                event
            ) {

                if (!dirty) {

                    return;

                }


                event.preventDefault();

                event.returnValue =
                    "";

            }


            window.addEventListener(
                "beforeunload",
                handleBeforeUnload
            );


            return () => {

                window.removeEventListener(
                    "beforeunload",
                    handleBeforeUnload
                );

            };

        },
        [
            dirty
        ]
    );


    /* ========================================================
       UPDATE SETTING
    ======================================================== */

    const update =
        useCallback(
            (
                key,
                value
            ) => {

                setSettings(
                    previous => {

                        const next = {

                            ...previous,

                            [key]:
                                value

                        };


                        cacheSettings(
                            next
                        );


                        return next;

                    }
                );


                setSaved(false);

                setError("");

            },
            []
        );


    /* ========================================================
       RESET LOCAL
    ======================================================== */

    function resetSettings() {

        const confirmed =
            window.confirm(

                "Reset Nova's settings to their defaults? " +
                "This only changes the current form until you save."

            );


        if (!confirmed) {

            return;

        }


        const defaults =
            cloneDefaults();


        setSettings(
            defaults
        );


        setSaved(false);

        setError("");

        cacheSettings(
            defaults
        );

    }


    /* ========================================================
       DISCARD
    ======================================================== */

    function discardChanges() {

        if (!dirty) {

            return;

        }


        const confirmed =
            window.confirm(
                "Discard your unsaved changes?"
            );


        if (!confirmed) {

            return;

        }


        setSettings(
            cloneSettings(
                originalSettings
            )
        );


        setSaved(false);

        setError("");

    }


    /* ========================================================
       SAVE
    ======================================================== */

    async function saveSettings() {

        if (
            saving ||
            !dirty
        ) {

            return;

        }


        setSaving(true);

        setSaved(false);

        setError("");


        const payload =
            sanitizeSettings(
                settings
            );


        try {

            const response =
                await fetchWithTimeout(

                    SETTINGS_ENDPOINT,

                    {

                        method:
                            "POST",

                        headers: {

                            "Content-Type":
                                "application/json",

                            "Accept":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                payload
                            )

                    }

                );


            if (
                !response.ok
            ) {

                let message =
                    `Failed to save settings (HTTP ${response.status}).`;


                try {

                    const errorData =
                        await response.json();


                    if (
                        errorData?.detail
                    ) {

                        message =
                            String(
                                errorData.detail
                            );

                    }

                } catch {

                    /*
                     * Some backends return plain text
                     * or completely empty error bodies.
                     */

                }


                throw new Error(
                    message
                );

            }


            const data =
                await response.json();


            const normalized =
                sanitizeSettings(
                    data
                );


            if (
                !mountedRef.current
            ) {

                return;

            }


            setSettings(
                normalized
            );


            setOriginalSettings(
                normalized
            );


            cacheSettings(
                normalized
            );


            setSaved(true);


            if (
                saveTimerRef.current
            ) {

                clearTimeout(
                    saveTimerRef.current
                );

            }


            saveTimerRef.current =
                setTimeout(
                    () => {

                        if (
                            mountedRef.current
                        ) {

                            setSaved(
                                false
                            );

                        }

                    },
                    3000
                );


        } catch (
            err
        ) {

            console.error(
                "Nova settings save error:",
                err
            );


            if (
                mountedRef.current
            ) {

                setError(
                    getErrorMessage(
                        err
                    )
                );

            }

        } finally {

            if (
                mountedRef.current
            ) {

                setSaving(
                    false
                );

            }

        }

    }


    /* ========================================================
       KEYBOARD SHORTCUTS
    ======================================================== */

    useEffect(
        () => {

            function handleKeyboard(
                event
            ) {

                if (
                    (
                        event.ctrlKey ||
                        event.metaKey
                    ) &&
                    event.key.toLowerCase() ===
                    "s"
                ) {

                    event.preventDefault();

                    saveSettings();

                }


                if (
                    event.key ===
                    "Escape"
                ) {

                    if (
                        showImport
                    ) {

                        setShowImport(
                            false
                        );

                        return;

                    }


                    if (
                        dirty
                    ) {

                        discardChanges();

                    }

                }

            }


            window.addEventListener(
                "keydown",
                handleKeyboard
            );


            return () => {

                window.removeEventListener(
                    "keydown",
                    handleKeyboard
                );

            };

        },
        [
            dirty,
            showImport
        ]
    );


    /* ========================================================
       SECTION TOGGLE
    ======================================================== */

    function toggleSection(
        section
    ) {

        setOpenSections(
            previous => ({

                ...previous,

                [section]:
                    !previous[section]

            })
        );

    }


    /* ========================================================
       PRESET
    ======================================================== */

    function applyPreset(
        presetKey
    ) {

        const preset =
            PRESETS[
                presetKey
            ];


        if (!preset) {

            return;

        }


        setSettings(
            previous => {

                const next = {

                    ...previous,

                    ...preset.values

                };


                cacheSettings(
                    next
                );


                return next;

            }
        );


        setSaved(false);

        setError("");

    }


    /* ========================================================
       EXPORT
    ======================================================== */

    function exportSettings() {

        const payload = {

            nova_settings:
                sanitizeSettings(
                    settings
                ),

            version:
                SETTINGS_VERSION,

            exported_at:
                new Date().toISOString()

        };


        const blob =
            new Blob(
                [
                    JSON.stringify(
                        payload,
                        null,
                        4
                    )
                ],
                {
                    type:
                        "application/json"
                }
            );


        const url =
            URL.createObjectURL(
                blob
            );


        const link =
            document.createElement(
                "a"
            );


        link.href =
            url;


        link.download =
            "nova-settings.json";


        document.body.appendChild(
            link
        );


        link.click();


        link.remove();


        URL.revokeObjectURL(
            url
        );

    }


    /* ========================================================
       IMPORT
    ======================================================== */

    function importSettings() {

        setImportError("");


        try {

            const parsed =
                JSON.parse(
                    importText
                );


            const source =
                parsed?.nova_settings ||
                parsed;


            const normalized =
                sanitizeSettings(
                    source
                );


            setSettings(
                normalized
            );


            cacheSettings(
                normalized
            );


            setSaved(false);

            setImportError("");

            setShowImport(
                false
            );

        } catch {

            setImportError(
                "Invalid JSON. Nova refuses to decipher the ancient scroll."
            );

        }

    }


    /* ========================================================
       FILE IMPORT
    ======================================================== */

    function handleFileImport(
        event
    ) {

        const file =
            event.target.files?.[0];


        if (!file) {

            return;

        }


        const reader =
            new FileReader();


        reader.onload =
            () => {

                setImportText(
                    String(
                        reader.result ||
                        ""
                    )
                );


                setShowImport(
                    true
                );

            };


        reader.onerror =
            () => {

                setImportError(
                    "Could not read this file."
                );

                setShowImport(
                    true
                );

            };


        reader.readAsText(
            file
        );


        event.target.value =
            "";

    }


    /* ========================================================
       SEARCH FILTER
    ======================================================== */

    const normalizedSearch =
        search
            .trim()
            .toLowerCase();


    function matchesSearch(
        ...values
    ) {

        if (
            !normalizedSearch
        ) {

            return true;

        }


        return values.some(
            value =>
                String(
                    value
                )
                    .toLowerCase()
                    .includes(
                        normalizedSearch
                    )
        );

    }


    /* ========================================================
       LOADING
    ======================================================== */

    if (loading) {

        return (

            <LoadingScreen />

        );

    }


    /* ========================================================
       MAIN UI
    ======================================================== */

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
                    sticky
                    top-0
                    z-50
                    border-b
                    border-gray-800
                    bg-gray-950/90
                    backdrop-blur-xl
                "
            >

                <div
                    className="
                        max-w-5xl
                        mx-auto
                        px-5
                        py-4
                        flex
                        items-center
                        justify-between
                        gap-4
                    "
                >

                    <button
                        onClick={() => {

                            if (dirty) {

                                discardChanges();

                                return;

                            }

                            navigate("/");

                        }}
                        className="
                            flex
                            items-center
                            gap-2
                            text-gray-400
                            hover:text-white
                            transition
                        "
                    >

                        <ArrowLeft
                            size={18}
                        />

                        <span
                            className="
                                hidden
                                sm:inline
                            "
                        >
                            Back
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
                                bg-blue-600/10
                                text-blue-400
                                flex
                                items-center
                                justify-center
                            "
                        >

                            <SettingsIcon
                                size={19}
                            />

                        </div>


                        <div>

                            <div
                                className="
                                    font-semibold
                                "
                            >
                                Nova Settings
                            </div>


                            <div
                                className="
                                    text-[11px]
                                    text-gray-500
                                "
                            >
                                Personalize your tutor
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

                        {dirty && (

                            <span
                                className="
                                    hidden
                                    md:inline
                                    text-xs
                                    text-yellow-400
                                "
                            >
                                Unsaved changes
                            </span>

                        )}


                        <button
                            onClick={
                                saveSettings
                            }
                            disabled={
                                saving ||
                                !dirty
                            }
                            className="
                                flex
                                items-center
                                gap-2
                                px-4
                                py-2
                                rounded-xl
                                bg-blue-600
                                hover:bg-blue-500
                                disabled:opacity-40
                                disabled:cursor-not-allowed
                                transition
                            "
                        >

                            {saving ? (

                                <RefreshCw
                                    size={16}
                                    className="
                                        animate-spin
                                    "
                                />

                            ) : (

                                <Save
                                    size={16}
                                />

                            )}


                            <span
                                className="
                                    hidden
                                    sm:inline
                                "
                            >
                                {saving
                                    ? "Saving"
                                    : "Save"}
                            </span>

                        </button>

                    </div>

                </div>

            </header>


            {/* =================================================
                CONTENT
            ================================================= */}

            <main
                className="
                    max-w-5xl
                    mx-auto
                    px-5
                    py-8
                    pb-24
                "
            >

                {/* =================================================
                    HERO
                ================================================= */}

                <section
                    className="
                        mb-8
                    "
                >

                    <div
                        className="
                            flex
                            items-start
                            justify-between
                            gap-6
                        "
                    >

                        <div>

                            <div
                                className="
                                    flex
                                    items-center
                                    gap-2
                                    text-blue-400
                                    text-sm
                                    font-medium
                                    mb-3
                                "
                            >

                                <Sparkles
                                    size={16}
                                />

                                PERSONALIZATION

                            </div>


                            <h1
                                className="
                                    text-3xl
                                    md:text-5xl
                                    font-bold
                                    tracking-tight
                                "
                            >
                                Make Nova work
                                <span
                                    className="
                                        text-blue-500
                                    "
                                >
                                    {" "}your way.
                                </span>
                            </h1>


                            <p
                                className="
                                    mt-4
                                    text-gray-400
                                    max-w-2xl
                                    leading-7
                                "
                            >

                                Configure how Nova teaches,
                                explains concepts, handles
                                mistakes and adapts to your
                                learning style.

                            </p>

                        </div>


                        <div
                            className="
                                hidden
                                md:flex
                                w-16
                                h-16
                                rounded-2xl
                                bg-blue-600/10
                                border
                                border-blue-500/10
                                items-center
                                justify-center
                                text-blue-400
                            "
                        >

                            <Brain
                                size={30}
                            />

                        </div>

                    </div>

                </section>


                {/* =================================================
                    USER STATUS
                ================================================= */}

                {user?.email && (

                    <div
                        className="
                            mb-6
                            rounded-2xl
                            border
                            border-gray-800
                            bg-gray-900/60
                            px-4
                            py-3
                            flex
                            items-center
                            gap-3
                        "
                    >

                        <ShieldCheck
                            size={18}
                            className="
                                text-green-400
                                shrink-0
                            "
                        />


                        <div
                            className="
                                min-w-0
                            "
                        >

                            <div
                                className="
                                    text-sm
                                    font-medium
                                "
                            >
                                Settings are linked to your account
                            </div>


                            <div
                                className="
                                    text-xs
                                    text-gray-500
                                    truncate
                                "
                            >
                                {user.email}
                            </div>

                        </div>

                    </div>

                )}


                {/* =================================================
                    ERROR
                ================================================= */}

                {error && (

                    <div
                        className="
                            mb-6
                            rounded-2xl
                            border
                            border-red-900/70
                            bg-red-950/30
                            px-4
                            py-4
                            flex
                            items-start
                            gap-3
                        "
                    >

                        <AlertTriangle
                            size={19}
                            className="
                                text-red-400
                                mt-0.5
                                shrink-0
                            "
                        />


                        <div
                            className="
                                flex-1
                            "
                        >

                            <div
                                className="
                                    text-sm
                                    text-red-200
                                    font-medium
                                "
                            >
                                Something went wrong
                            </div>


                            <div
                                className="
                                    text-xs
                                    text-red-300/70
                                    mt-1
                                "
                            >
                                {error}
                            </div>

                        </div>


                        <button
                            onClick={() =>
                                setError("")
                            }
                            className="
                                text-red-400
                                hover:text-red-200
                            "
                        >

                            <X
                                size={17}
                            />

                        </button>

                    </div>

                )}


                {/* =================================================
                    PRESETS
                ================================================= */}

                <section
                    className="
                        mb-6
                        rounded-2xl
                        border
                        border-gray-800
                        bg-gray-900
                        p-5
                    "
                >

                    <div
                        className="
                            flex
                            items-center
                            gap-3
                            mb-4
                        "
                    >

                        <Wand2
                            size={19}
                            className="
                                text-purple-400
                            "
                        />


                        <div>

                            <h2
                                className="
                                    font-semibold
                                "
                            >
                                Quick presets
                            </h2>


                            <p
                                className="
                                    text-xs
                                    text-gray-500
                                    mt-1
                                "
                            >
                                Change several teaching settings at once.
                            </p>

                        </div>

                    </div>


                    <div
                        className="
                            grid
                            sm:grid-cols-2
                            lg:grid-cols-4
                            gap-3
                        "
                    >

                        {Object.entries(
                            PRESETS
                        ).map(
                            ([
                                key,
                                preset
                            ]) => (

                                <button
                                    key={key}
                                    onClick={() =>
                                        applyPreset(
                                            key
                                        )
                                    }
                                    className="
                                        text-left
                                        rounded-xl
                                        border
                                        border-gray-800
                                        bg-gray-950
                                        hover:border-blue-500/40
                                        hover:bg-gray-900
                                        p-4
                                        transition
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

                                        {key ===
                                            "exam" ? (

                                            <GraduationCap
                                                size={17}
                                                className="
                                                    text-blue-400
                                                "
                                            />

                                        ) : key ===
                                            "beginner" ? (

                                            <BookOpen
                                                size={17}
                                                className="
                                                    text-green-400
                                                "
                                            />

                                        ) : key ===
                                            "focused" ? (

                                            <Zap
                                                size={17}
                                                className="
                                                    text-yellow-400
                                                "
                                            />

                                        ) : (

                                            <Sparkles
                                                size={17}
                                                className="
                                                    text-purple-400
                                                "
                                            />

                                        )}


                                        <span
                                            className="
                                                text-sm
                                                font-medium
                                            "
                                        >
                                            {
                                                preset.label
                                            }
                                        </span>

                                    </div>


                                    <p
                                        className="
                                            text-xs
                                            text-gray-500
                                            leading-5
                                        "
                                    >
                                        {
                                            preset.description
                                        }
                                    </p>

                                </button>

                            )
                        )}

                    </div>

                </section>


                {/* =================================================
                    TOOLS
                ================================================= */}

                <section
                    className="
                        mb-6
                        flex
                        flex-col
                        md:flex-row
                        gap-3
                    "
                >

                    <div
                        className="
                            flex-1
                            relative
                        "
                    >

                        <Search
                            size={17}
                            className="
                                absolute
                                left-4
                                top-1/2
                                -translate-y-1/2
                                text-gray-600
                            "
                        />


                        <input
                            value={
                                search
                            }
                            onChange={e =>
                                setSearch(
                                    e.target.value
                                )
                            }
                            placeholder="Search settings..."
                            className="
                                input
                                pl-11
                            "
                        />

                    </div>


                    <button
                        onClick={
                            exportSettings
                        }
                        className="
                            flex
                            items-center
                            justify-center
                            gap-2
                            px-4
                            py-3
                            rounded-xl
                            border
                            border-gray-800
                            bg-gray-900
                            text-gray-300
                            hover:text-white
                            hover:border-gray-700
                            transition
                        "
                    >

                        <Download
                            size={17}
                        />

                        Export

                    </button>


                    <button
                        onClick={() =>
                            fileInputRef
                                .current
                                ?.click()
                        }
                        className="
                            flex
                            items-center
                            justify-center
                            gap-2
                            px-4
                            py-3
                            rounded-xl
                            border
                            border-gray-800
                            bg-gray-900
                            text-gray-300
                            hover:text-white
                            hover:border-gray-700
                            transition
                        "
                    >

                        <Upload
                            size={17}
                        />

                        Import

                    </button>


                    <input
                        ref={
                            fileInputRef
                        }
                        type="file"
                        accept=".json,application/json"
                        onChange={
                            handleFileImport
                        }
                        className="
                            hidden
                        "
                    />

                </section>


                {/* =================================================
                    IMPORT PANEL
                ================================================= */}

                {showImport && (

                    <section
                        className="
                            mb-6
                            rounded-2xl
                            border
                            border-purple-900/50
                            bg-purple-950/10
                            p-5
                        "
                    >

                        <div
                            className="
                                flex
                                items-center
                                justify-between
                                mb-4
                            "
                        >

                            <div
                                className="
                                    flex
                                    items-center
                                    gap-2
                                "
                            >

                                <Upload
                                    size={18}
                                    className="
                                        text-purple-400
                                    "
                                />

                                <h2
                                    className="
                                        font-semibold
                                    "
                                >
                                    Import settings
                                </h2>

                            </div>


                            <button
                                onClick={() =>
                                    setShowImport(
                                        false
                                    )
                                }
                                className="
                                    text-gray-500
                                    hover:text-white
                                "
                            >

                                <X
                                    size={18}
                                />

                            </button>

                        </div>


                        <textarea
                            value={
                                importText
                            }
                            onChange={e => {

                                setImportText(
                                    e.target.value
                                );

                                setImportError(
                                    ""
                                );

                            }}
                            rows={8}
                            placeholder='Paste a Nova settings JSON file here...'
                            className="
                                input
                                font-mono
                                text-xs
                                resize-y
                            "
                        />


                        {importError && (

                            <div
                                className="
                                    mt-3
                                    text-sm
                                    text-red-400
                                "
                            >
                                {importError}
                            </div>

                        )}


                        <div
                            className="
                                flex
                                justify-end
                                gap-3
                                mt-4
                            "
                        >

                            <button
                                onClick={() =>
                                    setShowImport(
                                        false
                                    )
                                }
                                className="
                                    px-4
                                    py-2
                                    rounded-xl
                                    border
                                    border-gray-800
                                    text-gray-400
                                    hover:text-white
                                "
                            >
                                Cancel
                            </button>


                            <button
                                onClick={
                                    importSettings
                                }
                                className="
                                    px-4
                                    py-2
                                    rounded-xl
                                    bg-purple-600
                                    hover:bg-purple-500
                                "
                            >
                                Import settings
                            </button>

                        </div>

                    </section>

                )}


                {/* =================================================
                    SETTINGS SECTIONS
                ================================================= */}

                <div
                    className="
                        space-y-5
                    "
                >

                    {matchesSearch(
                        "profile",
                        "name",
                        "language",
                        "academic level"
                    ) && (

                        <SettingsSection
                            id="profile"
                            icon={
                                <User
                                    size={20}
                                />
                            }
                            title="Profile"
                            description="Tell Nova who it is teaching."
                            open={
                                openSections.profile
                            }
                            onToggle={() =>
                                toggleSection(
                                    "profile"
                                )
                            }
                        >

                            <Field
                                label="Your name"
                                description="Nova can use your name naturally during conversations."
                            >

                                <input
                                    value={
                                        settings.name
                                    }
                                    onChange={e =>
                                        update(
                                            "name",
                                            e.target.value
                                        )
                                    }
                                    maxLength={100}
                                    placeholder="Your name"
                                    className="
                                        input
                                    "
                                />


                                <CharacterCount
                                    value={
                                        settings.name
                                    }
                                    max={100}
                                />

                            </Field>


                            <Field
                                label="Language"
                                description="The language Nova should normally use."
                            >

                                <Select
                                    value={
                                        settings.language
                                    }
                                    onChange={value =>
                                        update(
                                            "language",
                                            value
                                        )
                                    }
                                    options={[
                                        [
                                            "English",
                                            "English"
                                        ],
                                        [
                                            "French",
                                            "French"
                                        ]
                                    ]}
                                />

                            </Field>


                            <Field
                                label="Academic level"
                                description="Nova uses this to choose vocabulary and explanation depth."
                            >

                                <Select
                                    value={
                                        settings.level
                                    }
                                    onChange={value =>
                                        update(
                                            "level",
                                            value
                                        )
                                    }
                                    options={[
                                        [
                                            "Middle School",
                                            "Middle School"
                                        ],
                                        [
                                            "High School",
                                            "High School"
                                        ],
                                        [
                                            "University",
                                            "University"
                                        ]
                                    ]}
                                />

                            </Field>

                        </SettingsSection>

                    )}


                    {matchesSearch(
                        "teaching",
                        "teaching approach",
                        "difficulty",
                        "hints",
                        "adaptive learning",
                        "step by step"
                    ) && (

                        <SettingsSection
                            id="teaching"
                            icon={
                                <Brain
                                    size={20}
                                />
                            }
                            title="Teaching intelligence"
                            description="Control how Nova teaches instead of only how it looks."
                            open={
                                openSections.teaching
                            }
                            onToggle={() =>
                                toggleSection(
                                    "teaching"
                                )
                            }
                        >

                            <Field
                                label="Teaching approach"
                                description="How Nova should normally teach."
                            >

                                <Select
                                    value={
                                        settings.teaching_style
                                    }
                                    onChange={value =>
                                        update(
                                            "teaching_style",
                                            value
                                        )
                                    }
                                    options={[
                                        [
                                            "Adaptive",
                                            "adaptive"
                                        ],
                                        [
                                            "Step by step",
                                            "step_by_step"
                                        ],
                                        [
                                            "Socratic",
                                            "socratic"
                                        ],
                                        [
                                            "Direct",
                                            "direct"
                                        ]
                                    ]}
                                />

                            </Field>


                            <Field
                                label="Difficulty"
                                description="Controls the difficulty Nova targets."
                            >

                                <Select
                                    value={
                                        settings.difficulty
                                    }
                                    onChange={value =>
                                        update(
                                            "difficulty",
                                            value
                                        )
                                    }
                                    options={[
                                        [
                                            "Adaptive",
                                            "adaptive"
                                        ],
                                        [
                                            "Easy",
                                            "easy"
                                        ],
                                        [
                                            "Normal",
                                            "normal"
                                        ],
                                        [
                                            "Advanced",
                                            "advanced"
                                        ]
                                    ]}
                                />

                            </Field>


                            <Field
                                label="Hints"
                                description="Choose when Nova should guide you instead of immediately revealing the solution."
                            >

                                <Select
                                    value={
                                        settings.hints
                                    }
                                    onChange={value =>
                                        update(
                                            "hints",
                                            value
                                        )
                                    }
                                    options={[
                                        [
                                            "When needed",
                                            "when_needed"
                                        ],
                                        [
                                            "Always",
                                            "always"
                                        ],
                                        [
                                            "Never",
                                            "never"
                                        ]
                                    ]}
                                />

                            </Field>


                            <Toggle
                                label="Adaptive learning"
                                description="Use previous learning behavior, strengths and weaknesses to personalize explanations."
                                checked={
                                    settings.adaptive_learning
                                }
                                onChange={value =>
                                    update(
                                        "adaptive_learning",
                                        value
                                    )
                                }
                            />


                            <Toggle
                                label="Step-by-step explanations"
                                description="Show logical steps when solving problems."
                                checked={
                                    settings.step_by_step
                                }
                                onChange={value =>
                                    update(
                                        "step_by_step",
                                        value
                                    )
                                }
                            />

                        </SettingsSection>

                    )}


                    {matchesSearch(
                        "response",
                        "answer length",
                        "tone",
                        "examples",
                        "analogies",
                        "encouragement"
                    ) && (

                        <SettingsSection
                            id="response"
                            icon={
                                <MessageSquare
                                    size={20}
                                />
                            }
                            title="Response behavior"
                            description="Control the shape and communication style of Nova's answers."
                            open={
                                openSections.response
                            }
                            onToggle={() =>
                                toggleSection(
                                    "response"
                                )
                            }
                        >

                            <Field
                                label="Answer length"
                                description="How much explanation Nova normally gives."
                            >

                                <Select
                                    value={
                                        settings.response_length
                                    }
                                    onChange={value =>
                                        update(
                                            "response_length",
                                            value
                                        )
                                    }
                                    options={[
                                        [
                                            "Concise",
                                            "concise"
                                        ],
                                        [
                                            "Balanced",
                                            "balanced"
                                        ],
                                        [
                                            "Detailed",
                                            "detailed"
                                        ]
                                    ]}
                                />

                            </Field>


                            <Field
                                label="Tone"
                                description="The general communication style Nova uses."
                            >

                                <Select
                                    value={
                                        settings.tone
                                    }
                                    onChange={value =>
                                        update(
                                            "tone",
                                            value
                                        )
                                    }
                                    options={[
                                        [
                                            "Friendly",
                                            "friendly"
                                        ],
                                        [
                                            "Professional",
                                            "professional"
                                        ],
                                        [
                                            "Academic",
                                            "academic"
                                        ],
                                        [
                                            "Casual",
                                            "casual"
                                        ]
                                    ]}
                                />

                            </Field>


                            <Toggle
                                label="Use examples"
                                description="Nova can use concrete examples to make concepts easier to understand."
                                checked={
                                    settings.use_examples
                                }
                                onChange={value =>
                                    update(
                                        "use_examples",
                                        value
                                    )
                                }
                            />


                            <Toggle
                                label="Use analogies"
                                description="Nova can use analogies for abstract or difficult concepts."
                                checked={
                                    settings.use_analogies
                                }
                                onChange={value =>
                                    update(
                                        "use_analogies",
                                        value
                                    )
                                }
                            />


                            <Toggle
                                label="Encouragement"
                                description="Nova can briefly acknowledge progress when appropriate."
                                checked={
                                    settings.encouragement
                                }
                                onChange={value =>
                                    update(
                                        "encouragement",
                                        value
                                    )
                                }
                            />

                        </SettingsSection>

                    )}


                    {matchesSearch(
                        "corrections",
                        "mistakes",
                        "correction style",
                        "correct answer"
                    ) && (

                        <SettingsSection
                            id="corrections"
                            icon={
                                <Lightbulb
                                    size={20}
                                />
                            }
                            title="Corrections & practice"
                            description="Control what happens when you make a mistake."
                            open={
                                openSections.corrections
                            }
                            onToggle={() =>
                                toggleSection(
                                    "corrections"
                                )
                            }
                        >

                            <Field
                                label="Correction style"
                                description="How Nova should respond to mistakes."
                            >

                                <Select
                                    value={
                                        settings.correction_style
                                    }
                                    onChange={value =>
                                        update(
                                            "correction_style",
                                            value
                                        )
                                    }
                                    options={[
                                        [
                                            "Explain the mistake",
                                            "explain"
                                        ],
                                        [
                                            "Gentle",
                                            "gentle"
                                        ],
                                        [
                                            "Strict and precise",
                                            "strict"
                                        ],
                                        [
                                            "Minimal",
                                            "minimal"
                                        ]
                                    ]}
                                />

                            </Field>


                            <Toggle
                                label="Show correct answer"
                                description="Allow Nova to reveal the final answer after explaining the reasoning."
                                checked={
                                    settings.show_correct_answer
                                }
                                onChange={value =>
                                    update(
                                        "show_correct_answer",
                                        value
                                    )
                                }
                            />

                        </SettingsSection>

                    )}


                    {matchesSearch(
                        "ai",
                        "generation",
                        "creativity"
                    ) && (

                        <SettingsSection
                            id="ai"
                            icon={
                                <SlidersHorizontal
                                    size={20}
                                />
                            }
                            title="AI generation"
                            description="These settings affect Nova's generated responses."
                            open={
                                openSections.ai
                            }
                            onToggle={() =>
                                toggleSection(
                                    "ai"
                                )
                            }
                        >

                            <Field
                                label="Creativity"
                                description="Controls how conservative or varied Nova's generated responses are."
                            >

                                <Select
                                    value={
                                        settings.creativity
                                    }
                                    onChange={value =>
                                        update(
                                            "creativity",
                                            value
                                        )
                                    }
                                    options={[
                                        [
                                            "Low · Precise",
                                            "low"
                                        ],
                                        [
                                            "Medium · Balanced",
                                            "medium"
                                        ],
                                        [
                                            "High · Creative",
                                            "high"
                                        ]
                                    ]}
                                />

                            </Field>


                            <InfoBox>
                                Creativity should affect
                                generation style, not factual
                                accuracy. For schoolwork, lower
                                or medium creativity is usually
                                more predictable.
                            </InfoBox>

                        </SettingsSection>

                    )}


                    {matchesSearch(
                        "personal instructions",
                        "behavior",
                        "custom instructions"
                    ) && (

                        <SettingsSection
                            id="custom"
                            icon={
                                <Sparkles
                                    size={20}
                                />
                            }
                            title="Personal instructions"
                            description="Give Nova additional instructions that persist between conversations."
                            open={
                                openSections.custom
                            }
                            onToggle={() =>
                                toggleSection(
                                    "custom"
                                )
                            }
                        >

                            <Field
                                label="Personal behavior"
                                description="Describe how you generally want Nova to interact with you."
                            >

                                <textarea
                                    value={
                                        settings.behavior
                                    }
                                    onChange={e =>
                                        update(
                                            "behavior",
                                            e.target.value
                                        )
                                    }
                                    maxLength={3000}
                                    rows={6}
                                    placeholder="Example: Explain difficult mathematics with simple examples and check my understanding before moving on."
                                    className="
                                        input
                                        resize-y
                                    "
                                />


                                <CharacterCount
                                    value={
                                        settings.behavior
                                    }
                                    max={3000}
                                />

                            </Field>


                            <Field
                                label="Custom AI instructions"
                                description="Additional persistent instructions for Nova."
                            >

                                <textarea
                                    value={
                                        settings.custom_instructions
                                    }
                                    onChange={e =>
                                        update(
                                            "custom_instructions",
                                            e.target.value
                                        )
                                    }
                                    maxLength={5000}
                                    rows={7}
                                    placeholder="Example: When I ask programming questions, explain the architecture before giving the code."
                                    className="
                                        input
                                        resize-y
                                    "
                                />


                                <CharacterCount
                                    value={
                                        settings.custom_instructions
                                    }
                                    max={5000}
                                />

                            </Field>

                        </SettingsSection>

                    )}

                </div>


                {/* =================================================
                    BOTTOM ACTIONS
                ================================================= */}

                <section
                    className="
                        mt-8
                        rounded-2xl
                        border
                        border-gray-800
                        bg-gray-900
                        p-5
                    "
                >

                    <div
                        className="
                            flex
                            flex-col
                            md:flex-row
                            md:items-center
                            justify-between
                            gap-5
                        "
                    >

                        <div>

                            <div
                                className="
                                    flex
                                    items-center
                                    gap-2
                                    mb-1
                                "
                            >

                                {saved ? (

                                    <Check
                                        size={18}
                                        className="
                                            text-green-400
                                        "
                                    />

                                ) : dirty ? (

                                    <AlertTriangle
                                        size={18}
                                        className="
                                            text-yellow-400
                                        "
                                    />

                                ) : (

                                    <ShieldCheck
                                        size={18}
                                        className="
                                            text-gray-500
                                        "
                                    />

                                )}


                                <span
                                    className="
                                        font-medium
                                    "
                                >

                                    {saved
                                        ? "Settings saved"
                                        : dirty
                                            ? "You have unsaved changes"
                                            : "Everything is up to date"}

                                </span>

                            </div>


                            <p
                                className="
                                    text-xs
                                    text-gray-500
                                "
                            >

                                Press
                                {" "}
                                <kbd
                                    className="
                                        px-1.5
                                        py-0.5
                                        rounded
                                        border
                                        border-gray-700
                                        bg-gray-950
                                        font-mono
                                    "
                                >
                                    Ctrl
                                </kbd>
                                {" + "}
                                <kbd
                                    className="
                                        px-1.5
                                        py-0.5
                                        rounded
                                        border
                                        border-gray-700
                                        bg-gray-950
                                        font-mono
                                    "
                                >
                                    S
                                </kbd>
                                {" "}
                                to save.
                            </p>

                        </div>


                        <div
                            className="
                                flex
                                flex-col
                                sm:flex-row
                                gap-3
                            "
                        >

                            {dirty && (

                                <button
                                    onClick={
                                        discardChanges
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
                                        border-gray-800
                                        text-gray-400
                                        hover:text-white
                                        hover:bg-gray-950
                                        transition
                                    "
                                >

                                    <RotateCcw
                                        size={17}
                                    />

                                    Discard

                                </button>

                            )}


                            <button
                                onClick={
                                    resetSettings
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
                                    border-red-900/50
                                    text-red-400
                                    hover:bg-red-950/20
                                    transition
                                "
                            >

                                <Trash2
                                    size={17}
                                />

                                Reset

                            </button>


                            <button
                                onClick={
                                    saveSettings
                                }
                                disabled={
                                    saving ||
                                    !dirty
                                }
                                className="
                                    flex
                                    items-center
                                    justify-center
                                    gap-2
                                    px-6
                                    py-3
                                    rounded-xl
                                    bg-blue-600
                                    hover:bg-blue-500
                                    disabled:opacity-40
                                    disabled:cursor-not-allowed
                                    font-semibold
                                    transition
                                "
                            >

                                {saving ? (

                                    <RefreshCw
                                        size={17}
                                        className="
                                            animate-spin
                                        "
                                    />

                                ) : saved ? (

                                    <Check
                                        size={17}
                                    />

                                ) : (

                                    <Save
                                        size={17}
                                    />

                                )}


                                {saving
                                    ? "Saving..."
                                    : saved
                                        ? "Saved"
                                        : "Save settings"}

                            </button>

                        </div>

                    </div>

                </section>


                {/* =================================================
                    FOOTER
                ================================================= */}

                <footer
                    className="
                        mt-8
                        flex
                        flex-col
                        md:flex-row
                        md:items-center
                        justify-between
                        gap-3
                        text-xs
                        text-gray-600
                    "
                >

                    <div
                        className="
                            flex
                            items-center
                            gap-2
                        "
                    >

                        <ShieldCheck
                            size={14}
                        />

                        Settings are validated before being sent to Nova.

                    </div>


                    <div
                        className="
                            flex
                            items-center
                            gap-2
                        "
                    >

                        <Keyboard
                            size={14}
                        />

                        Ctrl/Cmd + S to save

                    </div>

                </footer>

            </main>


            {/* =================================================
                STYLES
            ================================================= */}

            <style>{`

                .input {

                    width: 100%;

                    box-sizing: border-box;

                    background:
                        #030712;

                    border:
                        1px solid #374151;

                    border-radius:
                        0.75rem;

                    padding:
                        0.75rem 1rem;

                    color:
                        white;

                    outline:
                        none;

                    transition:
                        border-color 0.2s,
                        box-shadow 0.2s,
                        background 0.2s;

                }


                .input::placeholder {

                    color:
                        #4b5563;

                }


                .input:hover {

                    border-color:
                        #4b5563;

                }


                .input:focus {

                    border-color:
                        #3b82f6;

                    box-shadow:
                        0 0 0 3px
                        rgba(
                            59,
                            130,
                            246,
                            0.12
                        );

                }


                select.input {

                    cursor:
                        pointer;

                }


                select.input option {

                    background:
                        #030712;

                    color:
                        white;

                }


                textarea.input {

                    line-height:
                        1.6;

                }


                kbd {

                    font-size:
                        10px;

                }

            `}</style>

        </div>

    );

}


/* ============================================================
   LOADING SCREEN
============================================================ */

function LoadingScreen() {

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
                    flex
                    flex-col
                    items-center
                    text-center
                "
            >

                <div
                    className="
                        w-16
                        h-16
                        rounded-2xl
                        bg-blue-600/10
                        border
                        border-blue-500/10
                        flex
                        items-center
                        justify-center
                        mb-5
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


                <h1
                    className="
                        font-semibold
                        text-lg
                    "
                >
                    Loading Nova settings
                </h1>


                <p
                    className="
                        text-sm
                        text-gray-600
                        mt-2
                    "
                >
                    Checking your preferences...
                </p>

            </div>

        </div>

    );

}


/* ============================================================
   SETTINGS SECTION
============================================================ */

function SettingsSection({
    id,
    icon,
    title,
    description,
    open,
    onToggle,
    children
}) {

    return (

        <section
            id={
                `settings-${id}`
            }
            className="
                bg-gray-900
                border
                border-gray-800
                rounded-2xl
                overflow-hidden
            "
        >

            <button
                type="button"
                onClick={
                    onToggle
                }
                className="
                    w-full
                    p-6
                    flex
                    items-center
                    justify-between
                    gap-4
                    text-left
                    hover:bg-gray-900/70
                    transition
                "
            >

                <div
                    className="
                        flex
                        items-start
                        gap-3
                    "
                >

                    <div
                        className="
                            w-10
                            h-10
                            rounded-xl
                            bg-blue-600/10
                            text-blue-400
                            flex
                            items-center
                            justify-center
                            shrink-0
                        "
                    >
                        {icon}
                    </div>


                    <div>

                        <h2
                            className="
                                text-xl
                                font-semibold
                            "
                        >
                            {title}
                        </h2>


                        <p
                            className="
                                text-sm
                                text-gray-500
                                mt-1
                            "
                        >
                            {description}
                        </p>

                    </div>

                </div>


                <ChevronDown
                    size={19}
                    className={`
                        text-gray-500
                        transition-transform
                        shrink-0
                        ${
                            open
                                ? "rotate-180"
                                : ""
                        }
                    `}
                />

            </button>


            {open && (

                <div
                    className="
                        px-6
                        pb-6
                        space-y-6
                    "
                >

                    <div
                        className="
                            h-px
                            bg-gray-800
                        "
                    />


                    {children}

                </div>

            )}

        </section>

    );

}


/* ============================================================
   FIELD
============================================================ */

function Field({
    label,
    description,
    children
}) {

    return (

        <div>

            <label
                className="
                    block
                    text-sm
                    font-medium
                    text-gray-200
                    mb-1.5
                "
            >
                {label}
            </label>


            <p
                className="
                    text-xs
                    text-gray-500
                    mb-2
                    leading-5
                "
            >
                {description}
            </p>


            {children}

        </div>

    );

}


/* ============================================================
   SELECT
============================================================ */

function Select({
    value,
    onChange,
    options
}) {

    return (

        <select
            value={
                value
            }
            onChange={event =>
                onChange(
                    event.target.value
                )
            }
            className="
                input
            "
        >

            {options.map(
                ([
                    label,
                    optionValue
                ]) => (

                    <option
                        key={
                            optionValue
                        }
                        value={
                            optionValue
                        }
                    >
                        {label}
                    </option>

                )
            )}

        </select>

    );

}


/* ============================================================
   TOGGLE
============================================================ */

function Toggle({
    label,
    description,
    checked,
    onChange
}) {

    return (

        <button
            type="button"
            onClick={() =>
                onChange(
                    !checked
                )
            }
            className="
                w-full
                flex
                items-center
                justify-between
                gap-5
                text-left
                group
            "
            aria-pressed={
                checked
            }
        >

            <div>

                <div
                    className="
                        text-sm
                        font-medium
                        text-gray-200
                        group-hover:text-white
                        transition
                    "
                >
                    {label}
                </div>


                <div
                    className="
                        text-xs
                        text-gray-500
                        mt-1
                        max-w-2xl
                        leading-5
                    "
                >
                    {description}
                </div>

            </div>


            <div
                className={`
                    w-12
                    h-7
                    rounded-full
                    p-1
                    shrink-0
                    transition
                    ${
                        checked
                            ? "bg-blue-600"
                            : "bg-gray-700"
                    }
                `}
            >

                <div
                    className={`
                        w-5
                        h-5
                        bg-white
                        rounded-full
                        transition
                        ${
                            checked
                                ? "translate-x-5"
                                : "translate-x-0"
                        }
                    `}
                />

            </div>

        </button>

    );

}


/* ============================================================
   CHARACTER COUNT
============================================================ */

function CharacterCount({
    value,
    max
}) {

    const length =
        String(
            value || ""
        ).length;


    const percentage =
        max > 0
            ? (
                length /
                max
            ) * 100
            : 0;


    const warning =
        percentage >= 90;


    return (

        <div
            className="
                flex
                items-center
                justify-between
                mt-1.5
                text-[11px]
            "
        >

            <span
                className={
                    warning
                        ? "text-yellow-400"
                        : "text-gray-600"
                }
            >
                {length} / {max}
            </span>


            {warning && (

                <span
                    className="
                        text-yellow-500
                    "
                >
                    Almost full
                </span>

            )}

        </div>

    );

}


/* ============================================================
   INFO BOX
============================================================ */

function InfoBox({
    children
}) {

    return (

        <div
            className="
                rounded-xl
                border
                border-blue-900/50
                bg-blue-950/20
                p-4
                flex
                gap-3
            "
        >

            <Info
                size={17}
                className="
                    text-blue-400
                    mt-0.5
                    shrink-0
                "
            />


            <p
                className="
                    text-xs
                    text-blue-200/70
                    leading-5
                "
            >
                {children}
            </p>

        </div>

    );

}
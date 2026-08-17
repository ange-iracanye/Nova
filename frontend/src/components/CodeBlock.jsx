import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState
} from "react";

import {
    Check,
    Clipboard,
    Download,
    FileCode2,
    LoaderCircle,
    Maximize2,
    Minimize2,
    X
} from "lucide-react";

import { codeToHtml } from "shiki";


// ============================================================
// NOVA CODE BLOCK
// ============================================================
//
// Responsibilities:
//
// - Syntax highlighting with Shiki
// - Safe fallback when highlighting fails
// - Copy code to clipboard
// - Download code as a local file
// - Language display
// - Line numbers
// - Expand / collapse long code
// - Fullscreen code viewer
// - Loading state
// - Error recovery
// - Responsive layout
// - Reduced-motion support
// - Accessible controls
//
// The public API intentionally remains:
//
// <CodeBlock
//     language="javascript"
//     code="..."
// />
//
// ============================================================


// ============================================================
// CONFIGURATION
// ============================================================

const NOVA_CODE_CONFIG = {

    theme:
        "github-dark",

    defaultLanguage:
        "text",

    maxVisibleLines:
        28,

    fullscreenMaxLines:
        10000,

    copyResetDelay:
        1800,

    highlightTimeout:
        8000,

    maxHighlightCharacters:
        200000,

    defaultFileName:
        "nova-code",

    animationDuration:
        180

};


// ============================================================
// LANGUAGE ALIASES
// ============================================================
//
// Shiki accepts many language names, but users can ask Nova
// about code using common aliases. Normalize them here.
//
// ============================================================

const LANGUAGE_ALIASES = {

    js:
        "javascript",

    jsx:
        "jsx",

    ts:
        "typescript",

    tsx:
        "tsx",

    py:
        "python",

    rb:
        "ruby",

    rs:
        "rust",

    cpp:
        "cpp",

    cxx:
        "cpp",

    cc:
        "cpp",

    hpp:
        "cpp",

    c:
        "c",

    cs:
        "csharp",

    "c#":
        "csharp",

    sh:
        "shellscript",

    bash:
        "shellscript",

    zsh:
        "shellscript",

    shell:
        "shellscript",

    yml:
        "yaml",

    md:
        "markdown",

    mdx:
        "mdx",

    html:
        "html",

    htm:
        "html",

    css:
        "css",

    scss:
        "scss",

    sass:
        "sass",

    jsonc:
        "jsonc",

    text:
        "text",

    plaintext:
        "text",

    txt:
        "text",

    plain:
        "text"
};


// ============================================================
// DISPLAY LANGUAGE NAMES
// ============================================================

const LANGUAGE_LABELS = {

    javascript:
        "JavaScript",

    jsx:
        "JSX",

    typescript:
        "TypeScript",

    tsx:
        "TSX",

    python:
        "Python",

    java:
        "Java",

    c:
        "C",

    cpp:
        "C++",

    csharp:
        "C#",

    go:
        "Go",

    rust:
        "Rust",

    php:
        "PHP",

    ruby:
        "Ruby",

    swift:
        "Swift",

    kotlin:
        "Kotlin",

    html:
        "HTML",

    css:
        "CSS",

    scss:
        "SCSS",

    sass:
        "Sass",

    json:
        "JSON",

    jsonc:
        "JSONC",

    yaml:
        "YAML",

    markdown:
        "Markdown",

    mdx:
        "MDX",

    shellscript:
        "Shell",

    sql:
        "SQL",

    graphql:
        "GraphQL",

    xml:
        "XML",

    text:
        "Text"
};


// ============================================================
// FILE EXTENSIONS
// ============================================================

const FILE_EXTENSIONS = {

    javascript:
        "js",

    jsx:
        "jsx",

    typescript:
        "ts",

    tsx:
        "tsx",

    python:
        "py",

    java:
        "java",

    c:
        "c",

    cpp:
        "cpp",

    csharp:
        "cs",

    go:
        "go",

    rust:
        "rs",

    php:
        "php",

    ruby:
        "rb",

    swift:
        "swift",

    kotlin:
        "kt",

    html:
        "html",

    css:
        "css",

    scss:
        "scss",

    sass:
        "sass",

    json:
        "json",

    jsonc:
        "jsonc",

    yaml:
        "yaml",

    markdown:
        "md",

    mdx:
        "mdx",

    shellscript:
        "sh",

    sql:
        "sql",

    graphql:
        "graphql",

    xml:
        "xml",

    text:
        "txt"
};


// ============================================================
// SAFE STRING
// ============================================================

function safeString(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";

    }


    return String(value);
}


// ============================================================
// NORMALIZE LANGUAGE
// ============================================================

function normalizeLanguage(language) {

    const normalized =
        safeString(language)
            .trim()
            .toLowerCase();


    if (!normalized) {

        return NOVA_CODE_CONFIG.defaultLanguage;
    }


    return (
        LANGUAGE_ALIASES[normalized] ||
        normalized
    );
}


// ============================================================
// DISPLAY LANGUAGE
// ============================================================

function getLanguageLabel(language) {

    return (
        LANGUAGE_LABELS[language] ||
        language
            .replace(/[-_]/g, " ")
            .replace(/\b\w/g, char =>
                char.toUpperCase()
            )
    );
}


// ============================================================
// FILE EXTENSION
// ============================================================

function getFileExtension(language) {

    return (
        FILE_EXTENSIONS[language] ||
        "txt"
    );
}


// ============================================================
// SAFE FILE NAME
// ============================================================

function createFileName(language) {

    const extension =
        getFileExtension(language);


    const label =
        getLanguageLabel(language)
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, "-")
            .replace(/^-+|-+$/g, "");


    return (
        label
            ? `nova-code-${label}.${extension}`
            : `${NOVA_CODE_CONFIG.defaultFileName}.${extension}`
    );
}


// ============================================================
// LINE COUNT
// ============================================================

function getLineCount(code) {

    if (!code) {

        return 0;
    }


    return code.split("\n").length;
}


// ============================================================
// CLIPBOARD SUPPORT
// ============================================================

async function copyToClipboard(text) {

    if (
        navigator.clipboard &&
        typeof navigator.clipboard.writeText ===
            "function"
    ) {

        await navigator.clipboard.writeText(
            text
        );

        return true;
    }


    // --------------------------------------------------------
    // Legacy fallback.
    // Some browsers / restricted contexts still do not expose
    // navigator.clipboard.
    // --------------------------------------------------------

    const textarea =
        document.createElement("textarea");


    textarea.value =
        text;


    textarea.setAttribute(
        "readonly",
        ""
    );


    textarea.style.position =
        "fixed";

    textarea.style.opacity =
        "0";

    textarea.style.pointerEvents =
        "none";


    document.body.appendChild(
        textarea
    );


    textarea.select();


    let successful =
        false;


    try {

        successful =
            document.execCommand(
                "copy"
            );

    } finally {

        document.body.removeChild(
            textarea
        );

    }


    if (!successful) {

        throw new Error(
            "Clipboard access was unavailable."
        );
    }


    return true;
}


// ============================================================
// DOWNLOAD CODE
// ============================================================

function downloadCode(
    code,
    language
) {

    const extension =
        getFileExtension(
            language
        );


    const fileName =
        createFileName(
            language
        );


    const blob =
        new Blob(
            [code],
            {
                type:
                    extension === "html"
                        ? "text/html;charset=utf-8"
                        : "text/plain;charset=utf-8"
            }
        );


    const url =
        URL.createObjectURL(
            blob
        );


    const anchor =
        document.createElement(
            "a"
        );


    anchor.href =
        url;


    anchor.download =
        fileName;


    anchor.style.display =
        "none";


    document.body.appendChild(
        anchor
    );


    anchor.click();


    document.body.removeChild(
        anchor
    );


    setTimeout(
        () => {
            URL.revokeObjectURL(
                url
            );
        },
        1000
    );
}


// ============================================================
// SHIKI HIGHLIGHTER
// ============================================================

async function highlightCode(
    code,
    language,
    signal
) {

    if (!code) {

        return "";
    }


    // --------------------------------------------------------
    // Very large code blocks can make syntax highlighting
    // unnecessarily expensive.
    //
    // In that case the component falls back to plain text.
    // --------------------------------------------------------

    if (
        code.length >
        NOVA_CODE_CONFIG.maxHighlightCharacters
    ) {

        return "";
    }


    const highlightPromise =
        codeToHtml(
            code,
            {
                lang:
                    language,

                theme:
                    NOVA_CODE_CONFIG.theme,

                structure:
                    "classic"
            }
        );


    const timeoutPromise =
        new Promise(
            (_, reject) => {

                const timer =
                    setTimeout(
                        () => {

                            reject(
                                new Error(
                                    "Syntax highlighting timed out."
                                )
                            );

                        },
                        NOVA_CODE_CONFIG.highlightTimeout
                    );


                if (signal) {

                    signal.addEventListener(
                        "abort",
                        () => {

                            clearTimeout(
                                timer
                            );

                            reject(
                                new DOMException(
                                    "Highlighting aborted.",
                                    "AbortError"
                                )
                            );

                        },
                        {
                            once:
                                true
                        }
                    );

                }

            }
        );


    return Promise.race([
        highlightPromise,
        timeoutPromise
    ]);
}


// ============================================================
// CODE LINE NUMBERS
// ============================================================

function LineNumbers({
    lineCount
}) {

    if (
        lineCount <= 0
    ) {

        return null;
    }


    return (

        <div
            aria-hidden="true"
            className="
                nova-code-line-numbers
                select-none
                shrink-0
                border-r
                border-white/[0.06]
                bg-black/10
                px-3
                py-4
                text-right
                font-mono
                text-[12px]
                leading-6
                text-slate-600
            "
        >

            {Array.from(
                {
                    length:
                        lineCount
                },
                (_, index) => (

                    <div
                        key={index}
                        className="
                            h-6
                        "
                    >
                        {index + 1}
                    </div>

                )
            )}

        </div>
    );
}


// ============================================================
// CODE TOOLBAR BUTTON
// ============================================================

function ToolbarButton({
    children,
    label,
    onClick,
    disabled = false,
    active = false
}) {

    return (

        <button
            type="button"
            aria-label={label}
            title={label}
            onClick={onClick}
            disabled={disabled}
            className={`
                inline-flex
                h-8
                items-center
                gap-1.5
                rounded-lg
                border
                px-2.5
                text-xs
                font-medium
                transition-all
                duration-150
                focus:outline-none
                focus-visible:ring-2
                focus-visible:ring-white/30
                disabled:cursor-not-allowed
                disabled:opacity-40

                ${
                    active
                        ? `
                            border-emerald-400/20
                            bg-emerald-400/10
                            text-emerald-300
                        `
                        : `
                            border-white/[0.06]
                            bg-white/[0.035]
                            text-slate-400
                            hover:border-white/[0.12]
                            hover:bg-white/[0.07]
                            hover:text-white
                        `
                }
            `}
        >

            {children}

        </button>
    );
}


// ============================================================
// FULLSCREEN VIEWER
// ============================================================

function FullscreenCodeViewer({
    code,
    html,
    language,
    lineCount,
    onClose
}) {

    const closeButtonRef =
        useRef(null);


    useEffect(() => {

        closeButtonRef.current?.focus();


        const handleKeyDown =
            event => {

                if (
                    event.key === "Escape"
                ) {

                    onClose();

                }

            };


        document.addEventListener(
            "keydown",
            handleKeyDown
        );


        const previousOverflow =
            document.body.style.overflow;


        document.body.style.overflow =
            "hidden";


        return () => {

            document.removeEventListener(
                "keydown",
                handleKeyDown
            );


            document.body.style.overflow =
                previousOverflow;

        };

    }, [
        onClose
    ]);


    const lineNumbers =
        lineCount > 0
            ? (
                <LineNumbers
                    lineCount={
                        lineCount
                    }
                />
            )
            : null;


    return (

        <div
            className="
                fixed
                inset-0
                z-[10000]
                flex
                flex-col
                bg-slate-950/95
                backdrop-blur-xl
            "
            role="dialog"
            aria-modal="true"
            aria-label={
                `${getLanguageLabel(language)} code viewer`
            }
        >

            {/* ========================================== */}
            {/* HEADER */}
            {/* ========================================== */}

            <header
                className="
                    flex
                    min-h-14
                    shrink-0
                    items-center
                    justify-between
                    gap-4
                    border-b
                    border-white/[0.08]
                    bg-black/20
                    px-4
                    md:px-6
                "
            >

                <div
                    className="
                        flex
                        min-w-0
                        items-center
                        gap-3
                    "
                >

                    <div
                        className="
                            flex
                            h-8
                            w-8
                            shrink-0
                            items-center
                            justify-center
                            rounded-lg
                            border
                            border-white/[0.08]
                            bg-white/[0.04]
                            text-slate-300
                        "
                    >

                        <FileCode2
                            size={16}
                        />

                    </div>


                    <div
                        className="
                            min-w-0
                        "
                    >

                        <div
                            className="
                                truncate
                                text-sm
                                font-semibold
                                text-slate-200
                            "
                        >
                            {getLanguageLabel(language)}
                        </div>


                        <div
                            className="
                                text-[11px]
                                text-slate-500
                            "
                        >
                            {lineCount}{" "}
                            {lineCount === 1
                                ? "line"
                                : "lines"}
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

                    <ToolbarButton
                        label="Copy code"
                        onClick={() =>
                            copyToClipboard(
                                code
                            )
                        }
                    >

                        <Clipboard
                            size={14}
                        />

                        Copy

                    </ToolbarButton>


                    <button
                        ref={
                            closeButtonRef
                        }
                        type="button"
                        onClick={onClose}
                        aria-label="Close code viewer"
                        title="Close"
                        className="
                            inline-flex
                            h-8
                            w-8
                            items-center
                            justify-center
                            rounded-lg
                            border
                            border-white/[0.06]
                            bg-white/[0.035]
                            text-slate-400
                            transition
                            hover:bg-white/[0.08]
                            hover:text-white
                            focus:outline-none
                            focus-visible:ring-2
                            focus-visible:ring-white/30
                        "
                    >

                        <X
                            size={16}
                        />

                    </button>

                </div>

            </header>


            {/* ========================================== */}
            {/* CODE */}
            {/* ========================================== */}

            <main
                className="
                    min-h-0
                    flex-1
                    overflow-auto
                    nova-code-scrollbar
                "
            >

                <div
                    className="
                        mx-auto
                        min-w-max
                        w-full
                        max-w-[1800px]
                        p-4
                        md:p-8
                    "
                >

                    <div
                        className="
                            overflow-hidden
                            rounded-2xl
                            border
                            border-white/[0.08]
                            bg-[#0d1117]
                            shadow-2xl
                        "
                    >

                        <div
                            className="
                                flex
                                min-w-max
                            "
                        >

                            {lineNumbers}


                            <div
                                className="
                                    min-w-0
                                    flex-1
                                "
                            >

                                {html ? (

                                    <div
                                        className="
                                            nova-code-content
                                            p-4
                                            text-[13px]
                                            leading-6
                                        "
                                        dangerouslySetInnerHTML={{
                                            __html:
                                                html
                                        }}
                                    />

                                ) : (

                                    <pre
                                        className="
                                            m-0
                                            p-4
                                            font-mono
                                            text-[13px]
                                            leading-6
                                            text-slate-200
                                            whitespace-pre
                                        "
                                    >

                                        <code>
                                            {code}
                                        </code>

                                    </pre>

                                )}

                            </div>

                        </div>

                    </div>

                </div>

            </main>

        </div>
    );
}


// ============================================================
// MAIN COMPONENT
// ============================================================

export default function CodeBlock({
    language,
    code
}) {

    // --------------------------------------------------------
    // Normalize input once per prop change.
    // --------------------------------------------------------

    const normalizedCode =
        useMemo(
            () =>
                safeString(
                    code
                ),
            [code]
        );


    const normalizedLanguage =
        useMemo(
            () =>
                normalizeLanguage(
                    language
                ),
            [language]
        );


    const languageLabel =
        useMemo(
            () =>
                getLanguageLabel(
                    normalizedLanguage
                ),
            [normalizedLanguage]
        );


    const lineCount =
        useMemo(
            () =>
                getLineCount(
                    normalizedCode
                ),
            [normalizedCode]
        );


    const isLong =
        lineCount >
        NOVA_CODE_CONFIG.maxVisibleLines;


    // --------------------------------------------------------
    // State
    // --------------------------------------------------------

    const [
        html,
        setHtml
    ] = useState("");


    const [
        highlighting,
        setHighlighting
    ] = useState(
        false
    );


    const [
        highlightFailed,
        setHighlightFailed
    ] = useState(
        false
    );


    const [
        copied,
        setCopied
    ] = useState(
        false
    );


    const [
        copyError,
        setCopyError
    ] = useState(
        false
    );


    const [
        expanded,
        setExpanded
    ] = useState(
        false
    );


    const [
        fullscreen,
        setFullscreen
    ] = useState(
        false
    );


    const copyTimer =
        useRef(null);


    // --------------------------------------------------------
    // Highlight code.
    // --------------------------------------------------------

    useEffect(() => {

        let cancelled =
            false;


        const controller =
            new AbortController();


        async function runHighlight() {

            if (!normalizedCode) {

                setHtml("");

                setHighlighting(
                    false
                );

                setHighlightFailed(
                    false
                );

                return;
            }


            setHighlighting(
                true
            );

            setHighlightFailed(
                false
            );


            try {

                const result =
                    await highlightCode(
                        normalizedCode,
                        normalizedLanguage,
                        controller.signal
                    );


                if (
                    cancelled
                ) {

                    return;
                }


                setHtml(
                    result || ""
                );


                setHighlightFailed(
                    !result
                );

            } catch (error) {

                if (
                    cancelled ||
                    error?.name ===
                        "AbortError"
                ) {

                    return;
                }


                console.warn(
                    "[Nova] Code highlighting failed:",
                    error
                );


                setHtml("");

                setHighlightFailed(
                    true
                );

            } finally {

                if (
                    !cancelled
                ) {

                    setHighlighting(
                        false
                    );

                }

            }

        }


        runHighlight();


        return () => {

            cancelled =
                true;


            controller.abort();

        };

    }, [
        normalizedCode,
        normalizedLanguage
    ]);


    // --------------------------------------------------------
    // Clean timers on unmount.
    // --------------------------------------------------------

    useEffect(() => {

        return () => {

            if (
                copyTimer.current
            ) {

                clearTimeout(
                    copyTimer.current
                );

            }

        };

    }, []);


    // ========================================================
    // COPY
    // ========================================================

    const handleCopy =
        useCallback(
            async () => {

                if (
                    !normalizedCode
                ) {

                    return;
                }


                try {

                    await copyToClipboard(
                        normalizedCode
                    );


                    setCopied(
                        true
                    );

                    setCopyError(
                        false
                    );


                    if (
                        copyTimer.current
                    ) {

                        clearTimeout(
                            copyTimer.current
                        );

                    }


                    copyTimer.current =
                        setTimeout(
                            () => {

                                setCopied(
                                    false
                                );

                            },
                            NOVA_CODE_CONFIG.copyResetDelay
                        );

                } catch (error) {

                    console.error(
                        "[Nova] Could not copy code:",
                        error
                    );


                    setCopyError(
                        true
                    );

                    setCopied(
                        false
                    );


                    if (
                        copyTimer.current
                    ) {

                        clearTimeout(
                            copyTimer.current
                        );

                    }


                    copyTimer.current =
                        setTimeout(
                            () => {

                                setCopyError(
                                    false
                                );

                            },
                            NOVA_CODE_CONFIG.copyResetDelay
                        );

                }

            },
            [
                normalizedCode
            ]
        );


    // ========================================================
    // DOWNLOAD
    // ========================================================

    const handleDownload =
        useCallback(
            () => {

                try {

                    downloadCode(
                        normalizedCode,
                        normalizedLanguage
                    );

                } catch (error) {

                    console.error(
                        "[Nova] Could not download code:",
                        error
                    );

                }

            },
            [
                normalizedCode,
                normalizedLanguage
            ]
        );


    // ========================================================
    // FULLSCREEN
    // ========================================================

    const handleFullscreen =
        useCallback(
            () => {

                setFullscreen(
                    true
                );

            },
            []
        );


    const handleCloseFullscreen =
        useCallback(
            () => {

                setFullscreen(
                    false
                );

            },
            []
        );


    // ========================================================
    // EMPTY CODE
    // ========================================================

    if (
        !normalizedCode
    ) {

        return (

            <div
                className="
                    my-4
                    rounded-xl
                    border
                    border-white/[0.06]
                    bg-black/20
                    p-4
                    text-sm
                    text-slate-500
                "
            >
                No code to display.
            </div>
        );
    }


    // ========================================================
    // VISIBLE LINE COUNT
    // ========================================================

    const visibleLineCount =
        expanded || !isLong
            ? lineCount
            : NOVA_CODE_CONFIG.maxVisibleLines;


    // ========================================================
    // CODE CONTENT
    // ========================================================

    const displayedCode =
        expanded || !isLong
            ? normalizedCode
            : normalizedCode
                .split("\n")
                .slice(
                    0,
                    NOVA_CODE_CONFIG.maxVisibleLines
                )
                .join("\n");


    // --------------------------------------------------------
    // When collapsed, use highlighted HTML only if the full
    // code fits. For long code, the partial source is shown
    // plainly to avoid mismatching highlighted lines.
    // --------------------------------------------------------

    const displayedHtml =
        expanded || !isLong
            ? html
            : "";


    // ========================================================
    // RENDER
    // ========================================================

    return (

        <>

            <div
                className="
                    nova-code-block
                    my-4
                    overflow-hidden
                    rounded-2xl
                    border
                    border-white/[0.08]
                    bg-[#0d1117]
                    shadow-lg
                    shadow-black/20
                "
            >

                {/* ========================================== */}
                {/* TOOLBAR */}
                {/* ========================================== */}

                <div
                    className="
                        flex
                        min-h-11
                        items-center
                        justify-between
                        gap-3
                        border-b
                        border-white/[0.07]
                        bg-white/[0.025]
                        px-3
                        md:px-4
                    "
                >

                    <div
                        className="
                            flex
                            min-w-0
                            items-center
                            gap-2
                        "
                    >

                        <FileCode2
                            size={15}
                            className="
                                shrink-0
                                text-slate-500
                            "
                        />


                        <span
                            className="
                                truncate
                                text-xs
                                font-semibold
                                text-slate-400
                            "
                        >
                            {languageLabel}
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


                        <span
                            className="
                                hidden
                                text-[11px]
                                text-slate-600
                                sm:inline
                            "
                        >
                            {lineCount}{" "}
                            {lineCount === 1
                                ? "line"
                                : "lines"}
                        </span>


                        {highlighting && (

                            <span
                                className="
                                    flex
                                    items-center
                                    gap-1.5
                                    text-[11px]
                                    text-slate-600
                                "
                            >

                                <LoaderCircle
                                    size={12}
                                    className="
                                        animate-spin
                                    "
                                />

                                Highlighting

                            </span>

                        )}


                        {highlightFailed &&
                        !highlighting && (

                            <span
                                className="
                                    hidden
                                    text-[11px]
                                    text-amber-500/70
                                    sm:inline
                                "
                            >
                                Plain text mode
                            </span>

                        )}

                    </div>


                    <div
                        className="
                            flex
                            shrink-0
                            items-center
                            gap-1.5
                        "
                    >

                        {isLong && (

                            <ToolbarButton
                                label={
                                    expanded
                                        ? "Collapse code"
                                        : "Show all code"
                                }
                                active={
                                    expanded
                                }
                                onClick={() =>
                                    setExpanded(
                                        previous =>
                                            !previous
                                    )
                                }
                            >

                                {expanded ? (

                                    <Minimize2
                                        size={14}
                                    />

                                ) : (

                                    <Maximize2
                                        size={14}
                                    />

                                )}

                                <span
                                    className="
                                        hidden
                                        sm:inline
                                    "
                                >
                                    {expanded
                                        ? "Collapse"
                                        : "Expand"}
                                </span>

                            </ToolbarButton>

                        )}


                        <ToolbarButton
                            label="Download code"
                            onClick={
                                handleDownload
                            }
                        >

                            <Download
                                size={14}
                            />

                            <span
                                className="
                                    hidden
                                    md:inline
                                "
                            >
                                Download
                            </span>

                        </ToolbarButton>


                        <ToolbarButton
                            label={
                                copied
                                    ? "Code copied"
                                    : copyError
                                        ? "Copy failed"
                                        : "Copy code"
                            }
                            onClick={
                                handleCopy
                            }
                            active={
                                copied
                            }
                        >

                            {copied ? (

                                <Check
                                    size={14}
                                />

                            ) : (

                                <Clipboard
                                    size={14}
                                />

                            )}

                            <span
                                className="
                                    hidden
                                    sm:inline
                                "
                            >
                                {copied
                                    ? "Copied"
                                    : copyError
                                        ? "Retry"
                                        : "Copy"}
                            </span>

                        </ToolbarButton>


                        <ToolbarButton
                            label="Open fullscreen"
                            onClick={
                                handleFullscreen
                            }
                        >

                            <Maximize2
                                size={14}
                            />

                        </ToolbarButton>

                    </div>

                </div>


                {/* ========================================== */}
                {/* CODE */}
                {/* ========================================== */}

                <div
                    className="
                        nova-code-scrollbar
                        overflow-x-auto
                        overflow-y-hidden
                    "
                >

                    <div
                        className="
                            flex
                            min-w-max
                        "
                    >

                        <LineNumbers
                            lineCount={
                                visibleLineCount
                            }
                        />


                        <div
                            className="
                                min-w-0
                                flex-1
                            "
                        >

                            {displayedHtml ? (

                                <div
                                    className="
                                        nova-code-content
                                        p-4
                                        font-mono
                                        text-[13px]
                                        leading-6
                                    "
                                    dangerouslySetInnerHTML={{
                                        __html:
                                            displayedHtml
                                    }}
                                />

                            ) : (

                                <pre
                                    className="
                                        m-0
                                        p-4
                                        font-mono
                                        text-[13px]
                                        leading-6
                                        text-slate-200
                                        whitespace-pre
                                    "
                                >

                                    <code>
                                        {displayedCode}
                                    </code>

                                </pre>

                            )}

                        </div>

                    </div>

                </div>


                {/* ========================================== */}
                {/* COLLAPSED FOOTER */}
                {/* ========================================== */}

                {isLong &&
                !expanded && (

                    <div
                        className="
                            flex
                            items-center
                            justify-between
                            gap-4
                            border-t
                            border-white/[0.06]
                            bg-black/10
                            px-4
                            py-2.5
                        "
                    >

                        <span
                            className="
                                text-[11px]
                                text-slate-600
                            "
                        >
                            Showing{" "}
                            {NOVA_CODE_CONFIG.maxVisibleLines}
                            {" "}of{" "}
                            {lineCount} lines
                        </span>


                        <button
                            type="button"
                            onClick={() =>
                                setExpanded(
                                    true
                                )
                            }
                            className="
                                text-[11px]
                                font-medium
                                text-slate-400
                                transition
                                hover:text-white
                                focus:outline-none
                                focus-visible:ring-2
                                focus-visible:ring-white/30
                                rounded
                            "
                        >
                            Show all code
                        </button>

                    </div>

                )}

            </div>


            {/* ============================================== */}
            {/* FULLSCREEN */}
            {/* ============================================== */}

            {fullscreen && (

                <FullscreenCodeViewer
                    code={
                        normalizedCode
                    }
                    html={
                        html
                    }
                    language={
                        normalizedLanguage
                    }
                    lineCount={
                        lineCount
                    }
                    onClose={
                        handleCloseFullscreen
                    }
                />

            )}


            {/* ============================================== */}
            {/* COMPONENT STYLES */}
            {/* ============================================== */}

            <style>{`

                .nova-code-block {
    animation: none;
}


                


                .nova-code-content pre {
                    margin:
                        0 !important;

                    background:
                        transparent !important;

                    padding:
                        0 !important;

                    overflow:
                        visible !important;
                }


                .nova-code-content code {
                    font-family:
                        ui-monospace,
                        SFMono-Regular,
                        Menlo,
                        Monaco,
                        Consolas,
                        "Liberation Mono",
                        "Courier New",
                        monospace;

                    font-size:
                        13px;

                    line-height:
                        1.5;
                }


                .nova-code-content .line {
                    min-height:
                        24px;
                }


                .nova-code-scrollbar::-webkit-scrollbar {
                    width:
                        8px;

                    height:
                        8px;
                }


                .nova-code-scrollbar::-webkit-scrollbar-track {
                    background:
                        transparent;
                }


                .nova-code-scrollbar::-webkit-scrollbar-thumb {
                    background:
                        rgba(
                            148,
                            163,
                            184,
                            0.20
                        );

                    border:
                        2px solid transparent;

                    border-radius:
                        999px;

                    background-clip:
                        padding-box;
                }


                .nova-code-scrollbar::-webkit-scrollbar-thumb:hover {
                    background:
                        rgba(
                            148,
                            163,
                            184,
                            0.35
                        );

                    border:
                        2px solid transparent;

                    background-clip:
                        padding-box;
                }


                .nova-code-scrollbar {
                    scrollbar-width:
                        thin;

                    scrollbar-color:
                        rgba(
                            148,
                            163,
                            184,
                            0.22
                        )
                        transparent;
                }


                .nova-code-line-numbers {
                    font-variant-numeric:
                        tabular-nums;
                }


                @media (
                    prefers-reduced-motion: reduce
                ) {

                    .nova-code-block {
                        animation:
                            none;
                    }

                }


                @media (
                    max-width: 640px
                ) {

                    .nova-code-content,
                    .nova-code-block pre {
                        font-size:
                            12px;
                    }


                    .nova-code-line-numbers {
                        padding-left:
                            8px;

                        padding-right:
                            8px;

                        font-size:
                            11px;
                    }

                }

            `}</style>

        </>

    );
}
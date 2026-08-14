import {
    useState,
    useRef,
    useEffect
} from "react";

import {
    Send,
    Bot,
    User,
    Trash2,
    Pencil,
    ArrowLeft,
    Settings,
    LogOut,
    ChevronUp
} from "lucide-react";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
    useLocation,
    useNavigate
} from "react-router-dom";

import CodeBlock from "../components/CodeBlock";

const API_URL = "http://127.0.0.1:8000";

export default function Chat() {

    const location = useLocation();
    const navigate = useNavigate();

    const params =
        new URLSearchParams(
            location.search
        );

    const demoMode =
        params.get("demo") === "true";

    const tutorMode =
        params.get("mode") || null;


    const [messages, setMessages] =
        useState([]);

    const [history, setHistory] =
        useState([]);

    const [conversationId, setConversationId] =
        useState(null);

    const [demoSessionId, setDemoSessionId] =
        useState(null);

    const [input, setInput] =
        useState("");

    const [loading, setLoading] =
        useState(false);

    const [accountOpen, setAccountOpen] =
        useState(false);

    const messagesEnd =
        useRef(null);

    const accountRef =
        useRef(null);


    // =====================================
    // SAVE LAST PAGE
    // =====================================

    useEffect(() => {

        if (!demoMode) {

            localStorage.setItem(
                "nova_last_page",
                `${location.pathname}${location.search}`
            );

        }

    }, [
        location.pathname,
        location.search,
        demoMode
    ]);


    // =====================================
    // AUTO SCROLL
    // =====================================

    useEffect(() => {

        messagesEnd.current?.scrollIntoView({
            behavior: "smooth"
        });

    }, [messages, loading]);


    // =====================================
    // CLOSE ACCOUNT MENU
    // =====================================

    useEffect(() => {

        function handleClickOutside(event) {

            if (
                accountRef.current &&
                !accountRef.current.contains(
                    event.target
                )
            ) {

                setAccountOpen(false);

            }

        }

        document.addEventListener(
            "mousedown",
            handleClickOutside
        );

        return () => {

            document.removeEventListener(
                "mousedown",
                handleClickOutside
            );

        };

    }, []);


    // =====================================
    // CREATE DEMO SESSION
    // =====================================

    async function createDemoSession() {

        try {

            const response = await fetch(
                `${API_URL}/demo/session`,
                {
                    method: "POST"
                }
            );

            if (!response.ok) {

                throw new Error(
                    "Could not create demo session."
                );

            }

            const data =
                await response.json();

            setDemoSessionId(
                data.session_id
            );

            return data.session_id;

        } catch (error) {

            console.error(
                "Demo session error:",
                error
            );

            return null;

        }

    }


    // =====================================
    // INITIAL LOAD
    // =====================================

    useEffect(() => {

        async function initialize() {

            if (demoMode) {

                setMessages([]);

                setHistory([]);

                setConversationId(null);

                await createDemoSession();

                return;

            }


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


            await loadHistory();

            const savedConversationId =
                localStorage.getItem(
                    "nova_current_conversation"
                );

            if (savedConversationId) {

                await openConversation(
                    savedConversationId
                );

            }

        }

        initialize();

    }, [demoMode]);


    // =====================================
    // LOAD HISTORY
    // =====================================

    async function loadHistory() {

        if (demoMode) {
            return;
        }

        try {

            const user =
                JSON.parse(
                    localStorage.getItem(
                        "nova_user"
                    ) || "null"
                );

            if (!user?.email) {
                return;
            }


            const response =
                await fetch(
                    `${API_URL}/conversations/${encodeURIComponent(
                        user.email
                    )}`
                );


            if (!response.ok) {

                throw new Error(
                    `History request failed: HTTP ${response.status}`
                );

            }


            const data =
                await response.json();


            setHistory(
                Object.entries(data).map(
                    ([id, conversation]) => ({
                        id,
                        ...conversation
                    })
                )
            );

        } catch (error) {

            console.error(
                "Failed to load conversations:",
                error
            );

        }

    }


    // =====================================
    // OPEN CONVERSATION
    // =====================================

    async function openConversation(id) {

        if (
            loading ||
            demoMode
        ) {
            return;
        }


        const user =
            JSON.parse(
                localStorage.getItem(
                    "nova_user"
                ) || "null"
            );


        if (!user?.email) {
            return;
        }


        try {

            const response =
                await fetch(
                    `${API_URL}/conversation/${encodeURIComponent(
                        user.email
                    )}/${id}`
                );


            if (!response.ok) {

                throw new Error(
                    `Could not open conversation: HTTP ${response.status}`
                );

            }


            const conversation =
                await response.json();


            setConversationId(id);


            localStorage.setItem(
                "nova_current_conversation",
                id
            );


            const loadedMessages =
                (
                    conversation.messages ||
                    []
                ).map(message => ({
                    role: message.role,
                    text: message.text
                }));


            setMessages(
                loadedMessages
            );

        } catch (error) {

            console.error(
                "Failed to open conversation:",
                error
            );

        }

    }


    // =====================================
    // CREATE ACCOUNT CONVERSATION
    // =====================================

    async function createConversation() {

        if (demoMode) {
            return null;
        }


        const user =
            JSON.parse(
                localStorage.getItem(
                    "nova_user"
                ) || "null"
            );


        if (!user?.email) {
            return null;
        }


        try {

            const response =
                await fetch(
                    `${API_URL}/conversation/new`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            email: user.email
                        })
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Conversation creation failed."
                );

            }


            const data =
                await response.json();


            localStorage.setItem(
                "nova_current_conversation",
                data.id
            );


            setConversationId(
                data.id
            );


            return data.id;

        } catch (error) {

            console.error(
                "Failed to create conversation:",
                error
            );

            return null;

        }

    }


    // =====================================
    // NEW CHAT
    // =====================================

    async function newConversation() {

        if (loading) {
            return;
        }


        if (demoMode) {

            setMessages([]);

            setConversationId(null);

            const newSession =
                await createDemoSession();

            setDemoSessionId(
                newSession
            );

            return;

        }


        const id =
            await createConversation();


        if (!id) {
            return;
        }


        setConversationId(id);

        setMessages([]);

        await loadHistory();

    }


    // =====================================
    // DELETE CONVERSATION
    // =====================================

    async function deleteConversation(
        id
    ) {

        if (
            loading ||
            demoMode
        ) {
            return;
        }


        const user =
            JSON.parse(
                localStorage.getItem(
                    "nova_user"
                ) || "null"
            );


        if (!user?.email) {
            return;
        }


        try {

            const response =
                await fetch(
                    `${API_URL}/conversation/${encodeURIComponent(
                        user.email
                    )}/${id}`,
                    {
                        method: "DELETE"
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Could not delete conversation."
                );

            }


            const currentId =
                localStorage.getItem(
                    "nova_current_conversation"
                );


            if (
                currentId === id
            ) {

                localStorage.removeItem(
                    "nova_current_conversation"
                );

                setConversationId(
                    null
                );

                setMessages([]);

            }


            await loadHistory();

        } catch (error) {

            console.error(
                "Failed to delete conversation:",
                error
            );

        }

    }


    // =====================================
    // RENAME
    // =====================================

    async function renameConversation(
        id,
        oldTitle
    ) {

        if (
            loading ||
            demoMode
        ) {
            return;
        }


        const user =
            JSON.parse(
                localStorage.getItem(
                    "nova_user"
                ) || "null"
            );


        if (!user?.email) {
            return;
        }


        const newTitle =
            window.prompt(
                "Conversation name:",
                oldTitle ||
                    "New Chat"
            );


        if (
            !newTitle ||
            !newTitle.trim()
        ) {
            return;
        }


        try {

            const response =
                await fetch(
                    `${API_URL}/conversation/${encodeURIComponent(
                        user.email
                    )}/${id}/rename`,
                    {
                        method: "PUT",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            email:
                                user.email,
                            title:
                                newTitle.trim()
                        })
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Unable to rename conversation."
                );

            }


            await loadHistory();

        } catch (error) {

            console.error(
                "Failed to rename conversation:",
                error
            );

        }

    }


    // =====================================
    // LOG OUT
    // =====================================

    function logout() {

        localStorage.removeItem(
            "nova_user"
        );

        localStorage.removeItem(
            "nova_current_conversation"
        );

        localStorage.removeItem(
            "nova_last_page"
        );

        navigate(
            "/login"
        );

    }


    // =====================================
    // PERSONALIZE
    // =====================================

    function personalizeAccount() {

        setAccountOpen(false);

        navigate(
            "/settings"
        );

    }


    // =====================================
    // SEND MESSAGE
    // =====================================

    async function sendMessage() {

        if (
            !input.trim() ||
            loading
        ) {
            return;
        }


        const text =
            input.trim();


        const userMessage = {
            role: "user",
            text
        };


        // Append instead of replacing
        // the existing conversation.
        setMessages(prev => [
            ...prev,
            userMessage
        ]);


        setInput("");

        setLoading(true);


        try {

            let response;


            // =====================================
            // DEMO
            // =====================================

            if (demoMode) {

                let session =
                    demoSessionId;


                if (!session) {

                    session =
                        await createDemoSession();

                }


                if (!session) {

                    throw new Error(
                        "Could not create demo session."
                    );

                }


                response =
                    await fetch(
                        `${API_URL}/demo/chat/stream`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                message: text,
                                session_id:
                                    session,
                                tutor_mode:
                                    tutorMode
                            })
                        }
                    );

            }

            // =====================================
            // ACCOUNT
            // =====================================

            else {

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


                let currentConversationId =
                    localStorage.getItem(
                        "nova_current_conversation"
                    );


                if (!currentConversationId) {

                    currentConversationId =
                        await createConversation();

                }


                if (!currentConversationId) {

                    throw new Error(
                        "Could not create conversation."
                    );

                }


                setConversationId(
                    currentConversationId
                );


                response =
                    await fetch(
                        `${API_URL}/chat/stream`,
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                message: text,
                                email:
                                    user.email,
                                conversation_id:
                                    currentConversationId,
                                tutor_mode:
                                    tutorMode
                            })
                        }
                    );

            }


            if (!response.ok) {

                throw new Error(
                    `Nova request failed: HTTP ${response.status}`
                );

            }


            if (!response.body) {

                throw new Error(
                    "The server returned no response body."
                );

            }


            const returnedConversationId =
                response.headers.get(
                    "X-Conversation-ID"
                );


            if (
                returnedConversationId &&
                !demoMode
            ) {

                setConversationId(
                    returnedConversationId
                );


                localStorage.setItem(
                    "nova_current_conversation",
                    returnedConversationId
                );

            }


            const reader =
                response.body.getReader();


            const decoder =
                new TextDecoder();


            let assistant = {
                role: "nova",
                text: ""
            };


            setMessages(prev => [
                ...prev,
                assistant
            ]);


            while (true) {

                const {
                    done,
                    value
                } = await reader.read();


                if (done) {
                    break;
                }


                assistant.text +=
                    decoder.decode(
                        value,
                        {
                            stream: true
                        }
                    );


                setMessages(prev => {

                    const copy =
                        [...prev];


                    copy[
                        copy.length - 1
                    ] = {
                        ...assistant
                    };


                    return copy;

                });

            }


            assistant.text +=
                decoder.decode();


            setMessages(prev => {

                const copy =
                    [...prev];


                copy[
                    copy.length - 1
                ] = {
                    ...assistant
                };


                return copy;

            });


            // NovaCore already saves both messages.
            // Do NOT manually save either message.

            if (!demoMode) {

                await loadHistory();

            }

        } catch (error) {

            console.error(
                "Failed to send message:",
                error
            );


            setMessages(prev => [
                ...prev,
                {
                    role: "nova",
                    text:
                        "Sorry, I couldn't connect to Nova.\n\n" +
                        `Error: ${error.message}`
                }
            ]);

        } finally {

            setLoading(false);

        }

    }


    // =====================================
    // KEYBOARD
    // =====================================

    function handleKey(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();

        }

    }


    // =====================================
    // USER
    // =====================================

    const currentUser =
        JSON.parse(
            localStorage.getItem(
                "nova_user"
            ) || "null"
        );


    const userEmail =
        currentUser?.email ||
        "Nova User";


    // =====================================
    // MODE LABEL
    // =====================================

    let modeLabel =
        "AI Learning Assistant";


    if (demoMode) {

        modeLabel =
            "Demo Mode • No Account";

    } else if (
        tutorMode === "adaptive"
    ) {

        modeLabel =
            "Adaptive AI";

    } else if (
        tutorMode === "personal"
    ) {

        modeLabel =
            "Personal Tutor";

    }


    // =====================================
    // UI
    // =====================================

    return (

        <div
            className="
                nova-page-enter
                h-screen
                bg-gray-950
                text-white
                flex
                overflow-hidden
            "
        >

            {/* SIDEBAR */}

            <aside
                className="
                    w-72
                    bg-gray-900
                    border-r
                    border-gray-800
                    flex
                    flex-col
                    shrink-0
                    nova-sidebar-enter
                "
            >

                <div
                    className="
                        h-16
                        px-4
                        border-b
                        border-gray-800
                        flex
                        items-center
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
                            text-gray-300
                            hover:text-white
                            transition
                            group
                        "
                    >

                        <ArrowLeft
                            size={19}
                            className="
                                transition-transform
                                group-hover:-translate-x-1
                            "
                        />

                        <span className="font-medium">
                            Home
                        </span>

                    </button>

                </div>


                <button
                    onClick={newConversation}
                    disabled={loading}
                    className="
                        mx-4
                        mt-4
                        mb-3
                        w-[calc(100%-2rem)]
                        bg-blue-600
                        hover:bg-blue-700
                        disabled:bg-gray-700
                        rounded-xl
                        py-3
                        font-semibold
                        transition
                        flex
                        items-center
                        justify-center
                        gap-2
                        shadow-lg
                        shadow-blue-900/20
                    "
                >

                    <span className="text-lg">
                        +
                    </span>

                    New Chat

                </button>


                <div
                    className="
                        flex-1
                        overflow-y-auto
                        nova-scrollbar
                    "
                >

                    {demoMode ? (

                        <div
                            className="
                                px-5
                                py-6
                                text-gray-500
                                text-sm
                            "
                        >

                            Demo conversations disappear
                            when you leave demo mode.

                        </div>

                    ) : history.length === 0 ? (

                        <div
                            className="
                                px-5
                                py-6
                                text-gray-500
                                text-sm
                            "
                        >
                            No conversations yet.
                        </div>

                    ) : (

                        history.map(item => (

                            <div
                                key={item.id}
                                className={`
                                    group
                                    mx-2
                                    my-1
                                    p-3
                                    rounded-xl
                                    transition
                                    ${
                                        conversationId ===
                                        item.id
                                            ? "bg-gray-800"
                                            : "hover:bg-gray-800/70"
                                    }
                                `}
                            >

                                <div
                                    onClick={() =>
                                        openConversation(
                                            item.id
                                        )
                                    }
                                    className="
                                        cursor-pointer
                                        min-w-0
                                    "
                                >

                                    <div
                                        className="
                                            font-semibold
                                            truncate
                                            text-sm
                                        "
                                    >
                                        {item.title ||
                                            "New Chat"}
                                    </div>


                                    <div
                                        className="
                                            text-gray-500
                                            text-xs
                                            truncate
                                            mt-1
                                        "
                                    >

                                        {item.messages?.length
                                            ? item.messages[
                                                item.messages.length -
                                                1
                                            ].text
                                            : "No messages yet"}

                                    </div>

                                </div>


                                <div
                                    className="
                                        flex
                                        items-center
                                        gap-1
                                        mt-2
                                        opacity-0
                                        group-hover:opacity-100
                                        transition
                                    "
                                >

                                    <button
                                        onClick={() =>
                                            renameConversation(
                                                item.id,
                                                item.title
                                            )
                                        }
                                        disabled={loading}
                                        className="
                                            p-1.5
                                            rounded-lg
                                            hover:bg-gray-700
                                            text-gray-500
                                            hover:text-white
                                        "
                                    >
                                        <Pencil size={15} />
                                    </button>


                                    <button
                                        onClick={() =>
                                            deleteConversation(
                                                item.id
                                            )
                                        }
                                        disabled={loading}
                                        className="
                                            p-1.5
                                            rounded-lg
                                            hover:bg-red-900/70
                                            text-gray-500
                                            hover:text-red-300
                                        "
                                    >
                                        <Trash2 size={15} />
                                    </button>

                                </div>

                            </div>

                        ))

                    )}

                </div>


                {/* ACCOUNT */}

                {!demoMode && (

                    <div
                        ref={accountRef}
                        className="
                            relative
                            border-t
                            border-gray-800
                            p-3
                        "
                    >

                        {accountOpen && (

                            <div
                                className="
                                    absolute
                                    left-3
                                    right-3
                                    bottom-[calc(100%-0.25rem)]
                                    bg-gray-900
                                    border
                                    border-gray-700
                                    rounded-2xl
                                    shadow-2xl
                                    overflow-hidden
                                    z-50
                                "
                            >

                                <button
                                    onClick={
                                        personalizeAccount
                                    }
                                    className="
                                        w-full
                                        flex
                                        items-center
                                        gap-3
                                        px-4
                                        py-3
                                        text-left
                                        text-gray-300
                                        hover:bg-gray-800
                                        hover:text-white
                                    "
                                >

                                    <Settings size={18} />

                                    Personalize account

                                </button>


                                <div
                                    className="
                                        h-px
                                        bg-gray-800
                                    "
                                />


                                <button
                                    onClick={logout}
                                    className="
                                        w-full
                                        flex
                                        items-center
                                        gap-3
                                        px-4
                                        py-3
                                        text-left
                                        text-gray-300
                                        hover:bg-red-950
                                        hover:text-red-300
                                    "
                                >

                                    <LogOut size={18} />

                                    Log out

                                </button>

                            </div>

                        )}


                        <button
                            onClick={() =>
                                setAccountOpen(
                                    prev => !prev
                                )
                            }
                            className="
                                w-full
                                flex
                                items-center
                                gap-3
                                p-3
                                rounded-xl
                                hover:bg-gray-800
                                transition
                                text-left
                            "
                        >

                            <div
                                className="
                                    w-10
                                    h-10
                                    rounded-full
                                    bg-gray-800
                                    border
                                    border-gray-700
                                    flex
                                    items-center
                                    justify-center
                                "
                            >

                                <User size={18} />

                            </div>


                            <div
                                className="
                                    flex-1
                                    min-w-0
                                "
                            >

                                <div
                                    className="
                                        font-medium
                                        truncate
                                        text-sm
                                    "
                                >
                                    {userEmail}
                                </div>

                                <div
                                    className="
                                        text-xs
                                        text-gray-500
                                        mt-0.5
                                    "
                                >
                                    Account
                                </div>

                            </div>


                            <ChevronUp
                                size={17}
                                className={`
                                    text-gray-500
                                    transition-transform
                                    ${
                                        accountOpen
                                            ? "rotate-180"
                                            : ""
                                    }
                                `}
                            />

                        </button>

                    </div>

                )}

            </aside>


            {/* CHAT */}

            <div
                className="
                    flex-1
                    flex
                    flex-col
                    min-w-0
                    nova-content-enter
                "
            >

                {/* HEADER */}

                <header
                    className="
                        h-16
                        px-5
                        border-b
                        border-gray-800
                        flex
                        items-center
                    "
                >

                    <div
                        className="
                            flex
                            items-center
                            gap-3
                        "
                    >

                        <Bot
                            size={25}
                            className="text-gray-200"
                        />


                        <div>

                            <h1
                                className="
                                    text-lg
                                    font-semibold
                                "
                            >
                                Nova
                            </h1>


                            <p
                                className="
                                    text-xs
                                    text-gray-500
                                "
                            >
                                {modeLabel}
                            </p>

                        </div>

                    </div>

                </header>


                {/* MESSAGES */}

                <main
                    className="
                        flex-1
                        overflow-y-auto
                        nova-scrollbar
                        relative
                    "
                >

                    {messages.length === 0 &&
                    !loading && (

                        <div
                            className="
                                absolute
                                inset-0
                                flex
                                items-center
                                justify-center
                                pointer-events-none
                            "
                        >

                            <div
                                className="
                                    text-center
                                    max-w-xl
                                    px-6
                                    -translate-y-8
                                "
                            >

                                <div
                                    className="
                                        flex
                                        justify-center
                                        mb-5
                                    "
                                >

                                    <Bot
                                        size={52}
                                        strokeWidth={1.4}
                                        className="
                                            text-gray-400
                                        "
                                    />

                                </div>


                                <h2
                                    className="
                                        text-3xl
                                        md:text-4xl
                                        font-semibold
                                        tracking-tight
                                        text-gray-100
                                    "
                                >
                                    How can I help you
                                    learn today?
                                </h2>


                                <p
                                    className="
                                        mt-3
                                        text-gray-500
                                        text-sm
                                        md:text-base
                                    "
                                >

                                    Ask Nova a question,
                                    explain a concept,
                                    solve a problem,
                                    or start studying.

                                </p>

                            </div>

                        </div>

                    )}


                    {messages.length > 0 && (

                        <div
                            className="
                                max-w-5xl
                                mx-auto
                                px-4
                                md:px-6
                                py-8
                                space-y-6
                            "
                        >

                            {messages.map(
                                (msg, index) => (

                                    <div
                                        key={index}
                                        className={`
                                            flex
                                            ${
                                                msg.role === "user"
                                                    ? "justify-end"
                                                    : "justify-start"
                                            }
                                        `}
                                    >

                                        <div
                                            className={`
                                                max-w-4xl
                                                flex
                                                gap-3
                                                ${
                                                    msg.role === "user"
                                                        ? "flex-row-reverse"
                                                        : ""
                                                }
                                            `}
                                        >

                                            <div
                                                className="
                                                    shrink-0
                                                    pt-1
                                                    text-gray-400
                                                "
                                            >

                                                {msg.role ===
                                                "user"
                                                    ? (
                                                        <User
                                                            size={20}
                                                        />
                                                    )
                                                    : (
                                                        <Bot
                                                            size={20}
                                                        />
                                                    )}

                                            </div>


                                            <div
                                                className={`
                                                    px-4
                                                    py-3
                                                    rounded-2xl
                                                    leading-relaxed
                                                    ${
                                                        msg.role ===
                                                        "user"
                                                            ? "bg-blue-600 text-white rounded-tr-md"
                                                            : "bg-gray-900 border border-gray-800 text-gray-200 rounded-tl-md"
                                                    }
                                                `}
                                            >

                                                <div
                                                    className="
                                                        prose
                                                        prose-invert
                                                        prose-sm
                                                        md:prose-base
                                                        max-w-none
                                                    "
                                                >

                                                    <ReactMarkdown
                                                        remarkPlugins={[
                                                            remarkGfm
                                                        ]}
                                                        components={{
                                                            code({
                                                                inline,
                                                                className,
                                                                children,
                                                                ...props
                                                            }) {

                                                                const match =
                                                                    /language-(\w+)/
                                                                        .exec(
                                                                            className ||
                                                                            ""
                                                                        );


                                                                const code =
                                                                    String(
                                                                        children
                                                                    ).replace(
                                                                        /\n$/,
                                                                        ""
                                                                    );


                                                                if (
                                                                    inline ||
                                                                    !match
                                                                ) {

                                                                    return (
                                                                        <code
                                                                            className="
                                                                                bg-gray-800
                                                                                px-1.5
                                                                                py-0.5
                                                                                rounded
                                                                                text-sm
                                                                            "
                                                                            {...props}
                                                                        >
                                                                            {children}
                                                                        </code>
                                                                    );

                                                                }


                                                                return (
                                                                    <CodeBlock
                                                                        language={
                                                                            match[1]
                                                                        }
                                                                        code={
                                                                            code
                                                                        }
                                                                    />
                                                                );

                                                            }
                                                        }}
                                                    >

                                                        {msg.text}

                                                    </ReactMarkdown>

                                                </div>

                                            </div>

                                        </div>

                                    </div>

                                )
                            )}


                            {loading && (

                                <div
                                    className="
                                        flex
                                        items-center
                                        gap-3
                                        text-gray-500
                                    "
                                >

                                    <Bot size={19} />

                                    <span
                                        className="
                                            text-sm
                                            animate-pulse
                                        "
                                    >
                                        Nova is thinking...
                                    </span>

                                </div>

                            )}


                            <div
                                ref={messagesEnd}
                            />

                        </div>

                    )}


                    {messages.length === 0 &&
                    loading && (

                        <div
                            className="
                                absolute
                                inset-0
                                flex
                                items-center
                                justify-center
                            "
                        >

                            <div
                                className="
                                    flex
                                    items-center
                                    gap-3
                                    text-gray-500
                                "
                            >

                                <Bot size={20} />

                                <span className="animate-pulse">
                                    Nova is thinking...
                                </span>

                            </div>

                        </div>

                    )}

                </main>


                {/* INPUT */}

                <div
                    className="
                        border-t
                        border-gray-800
                        bg-gray-950
                        p-4
                    "
                >

                    <div
                        className="
                            max-w-5xl
                            mx-auto
                            flex
                            gap-3
                            items-end
                        "
                    >

                        <input
                            value={input}
                            onChange={event =>
                                setInput(
                                    event.target.value
                                )
                            }
                            onKeyDown={handleKey}
                            placeholder="Ask Nova anything..."
                            disabled={loading}
                            className="
                                w-full
                                bg-gray-900
                                border
                                border-gray-800
                                rounded-2xl
                                px-5
                                py-3.5
                                outline-none
                                text-gray-100
                                placeholder-gray-600
                                focus:border-gray-600
                                transition
                            "
                        />


                        <button
                            onClick={sendMessage}
                            disabled={
                                loading ||
                                !input.trim()
                            }
                            className="
                                h-[52px]
                                w-[52px]
                                shrink-0
                                bg-blue-600
                                hover:bg-blue-700
                                disabled:bg-gray-800
                                disabled:text-gray-600
                                rounded-2xl
                                flex
                                items-center
                                justify-center
                                transition
                            "
                        >

                            <Send size={19} />

                        </button>

                    </div>


                    <p
                        className="
                            text-center
                            text-[11px]
                            text-gray-600
                            mt-2
                        "
                    >

                        Nova can make mistakes.
                        Check important information.

                    </p>

                </div>

            </div>


            <style>{`

                /* =====================================
                   PAGE TRANSITION
                   ===================================== */

                .nova-page-enter {
                    animation:
                        novaPageSlideIn
                        0.55s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        )
                        both;
                }


                @keyframes novaPageSlideIn {

                    from {
                        opacity: 0;
                        transform:
                            translateX(90px);
                    }

                    to {
                        opacity: 1;
                        transform:
                            translateX(0);
                    }

                }


                /* =====================================
                   SIDEBAR ENTER
                   ===================================== */

                .nova-sidebar-enter {

                    animation:
                        novaSidebarIn
                        0.65s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        )
                        0.05s
                        both;

                }


                @keyframes novaSidebarIn {

                    from {
                        opacity: 0;
                        transform:
                            translateX(-35px);
                    }

                    to {
                        opacity: 1;
                        transform:
                            translateX(0);
                    }

                }


                /* =====================================
                   MAIN CONTENT ENTER
                   ===================================== */

                .nova-content-enter {

                    animation:
                        novaContentIn
                        0.6s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        )
                        0.08s
                        both;

                }


                @keyframes novaContentIn {

                    from {
                        opacity: 0;
                        transform:
                            translateX(65px);
                    }

                    to {
                        opacity: 1;
                        transform:
                            translateX(0);
                    }

                }


                /* =====================================
                   SCROLLBAR
                   ===================================== */

                .nova-scrollbar::-webkit-scrollbar {
                    width: 8px;
                }

                .nova-scrollbar::-webkit-scrollbar-track {
                    background: transparent;
                }

                .nova-scrollbar::-webkit-scrollbar-thumb {
                    background:
                        rgba(
                            75,
                            85,
                            99,
                            0.35
                        );

                    border-radius: 999px;

                    border:
                        2px solid transparent;

                    background-clip:
                        padding-box;
                }

                .nova-scrollbar::-webkit-scrollbar-thumb:hover {
                    background:
                        rgba(
                            107,
                            114,
                            128,
                            0.55
                        );

                    border:
                        2px solid transparent;

                    background-clip:
                        padding-box;
                }

                .nova-scrollbar {
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


                /* =====================================
                   REDUCE MOTION
                   ===================================== */

                @media (
                    prefers-reduced-motion: reduce
                ) {

                    .nova-page-enter,
                    .nova-sidebar-enter,
                    .nova-content-enter {

                        animation: none;

                    }

                }

            `}</style>

        </div>

    );

}

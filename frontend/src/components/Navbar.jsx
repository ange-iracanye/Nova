import {
    Link,
    useNavigate
} from "react-router-dom";

import {
    Bot,
    Settings,
    LogOut,
    ChevronDown
} from "lucide-react";

import {
    useEffect,
    useRef,
    useState
} from "react";


export default function Navbar() {

    const navigate = useNavigate();

    const [accountOpen, setAccountOpen] =
        useState(false);

    const [user, setUser] =
        useState(null);

    const accountRef =
        useRef(null);


    // =====================================
    // LOAD USER
    // =====================================

    useEffect(() => {

        function loadUser() {

            try {

                const storedUser =
                    JSON.parse(
                        localStorage.getItem(
                            "nova_user"
                        ) || "null"
                    );

                setUser(storedUser);

            } catch {

                setUser(null);

            }

        }

        loadUser();

        window.addEventListener(
            "storage",
            loadUser
        );

        return () => {

            window.removeEventListener(
                "storage",
                loadUser
            );

        };

    }, []);


    // =====================================
    // CLOSE ACCOUNT MENU
    // =====================================

    useEffect(() => {

        function handleOutsideClick(event) {

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
            handleOutsideClick
        );

        return () => {

            document.removeEventListener(
                "mousedown",
                handleOutsideClick
            );

        };

    }, []);


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

        setUser(null);

        setAccountOpen(false);

        navigate("/");

    }


    // =====================================
    // PERSONALIZE
    // =====================================

    function personalize() {

        setAccountOpen(false);

        navigate("/settings");

    }


    // =====================================
    // UI
    // =====================================

    return (

        <nav
            className="
                sticky
                top-0
                z-50
                border-b
                border-slate-800/80
                bg-slate-950/85
                backdrop-blur-xl
            "
        >

            <div
                className="
                    max-w-7xl
                    mx-auto
                    flex
                    justify-between
                    items-center
                    px-6
                    py-4
                "
            >

                {/* =================================
                    NOVA LOGO
                ================================= */}

                <Link
                    to="/"
                    className="
                        flex
                        items-center
                        gap-2.5
                        group
                        shrink-0
                    "
                >

                    <div
                        className="
                            flex
                            items-center
                            justify-center
                            text-blue-400
                            transition-all
                            duration-300
                            group-hover:scale-110
                            group-hover:rotate-3
                        "
                    >

                        <Bot
                            size={27}
                            strokeWidth={1.8}
                        />

                    </div>

                    <span
                        className="
                            text-2xl
                            font-bold
                            tracking-tight
                            text-white
                        "
                    >
                        Nova
                    </span>

                </Link>


                {/* =================================
                    NAVIGATION
                ================================= */}

                <div
                    className="
                        flex
                        items-center
                        gap-2
                    "
                >

                    <Link
                        to="/chat"
                        className="
                            px-4
                            py-2
                            rounded-xl
                            text-slate-300
                            hover:text-white
                            hover:bg-slate-900
                            transition-all
                            duration-300
                        "
                    >
                        Chat
                    </Link>


                    <Link
                        to="/dashboard"
                        className="
                            px-4
                            py-2
                            rounded-xl
                            text-slate-300
                            hover:text-white
                            hover:bg-slate-900
                            transition-all
                            duration-300
                        "
                    >
                        Dashboard
                    </Link>


                    <Link
                        to="/settings"
                        className="
                            px-4
                            py-2
                            rounded-xl
                            text-slate-300
                            hover:text-white
                            hover:bg-slate-900
                            transition-all
                            duration-300
                        "
                    >
                        Settings
                    </Link>


                    {/* =================================
                        ACCOUNT / LOGIN
                    ================================= */}

                    {!user ? (

                        <Link
                            to="/login"
                            className="
                                ml-2
                                px-5
                                py-2.5
                                rounded-xl
                                bg-blue-600
                                hover:bg-blue-500
                                text-white
                                font-medium
                                shadow-lg
                                shadow-blue-900/20
                                transition-all
                                duration-300
                                hover:-translate-y-0.5
                                hover:shadow-blue-900/40
                            "
                        >
                            Login
                        </Link>

                    ) : (

                        <div
                            ref={accountRef}
                            className="
                                relative
                                ml-2
                            "
                        >

                            <button
                                onClick={() =>
                                    setAccountOpen(
                                        previous =>
                                            !previous
                                    )
                                }
                                className="
                                    flex
                                    items-center
                                    gap-2.5
                                    px-3
                                    py-2
                                    rounded-xl
                                    hover:bg-slate-900
                                    transition-all
                                    duration-300
                                "
                            >

                                <div
                                    className="
                                        w-9
                                        h-9
                                        rounded-full
                                        bg-slate-800
                                        border
                                        border-slate-700
                                        flex
                                        items-center
                                        justify-center
                                    "
                                >

                                    <span
                                        className="
                                            text-sm
                                            font-semibold
                                            text-blue-400
                                        "
                                    >
                                        {(
                                            user.email ||
                                            "N"
                                        )[0].toUpperCase()}
                                    </span>

                                </div>


                                <div
                                    className="
                                        hidden
                                        md:block
                                        text-left
                                        max-w-32
                                    "
                                >

                                    <div
                                        className="
                                            text-sm
                                            font-medium
                                            text-white
                                            truncate
                                        "
                                    >
                                        {user.email}
                                    </div>

                                    <div
                                        className="
                                            text-[11px]
                                            text-slate-500
                                        "
                                    >
                                        Account
                                    </div>

                                </div>


                                <ChevronDown
                                    size={16}
                                    className={`
                                        text-slate-500
                                        transition-transform
                                        duration-300
                                        ${
                                            accountOpen
                                                ? "rotate-180"
                                                : ""
                                        }
                                    `}
                                />

                            </button>


                            {/* ACCOUNT MENU */}

                            {accountOpen && (

                                <div
                                    className="
                                        absolute
                                        right-0
                                        top-full
                                        mt-2
                                        w-60
                                        rounded-2xl
                                        border
                                        border-slate-800
                                        bg-slate-900
                                        shadow-2xl
                                        shadow-black/40
                                        overflow-hidden
                                        animate-account-menu
                                    "
                                >

                                    <button
                                        onClick={
                                            personalize
                                        }
                                        className="
                                            w-full
                                            flex
                                            items-center
                                            gap-3
                                            px-4
                                            py-3.5
                                            text-left
                                            text-slate-300
                                            hover:bg-slate-800
                                            hover:text-white
                                            transition
                                        "
                                    >

                                        <Settings
                                            size={18}
                                        />

                                        <span>
                                            Personalize account
                                        </span>

                                    </button>


                                    <div
                                        className="
                                            h-px
                                            bg-slate-800
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
                                            py-3.5
                                            text-left
                                            text-slate-300
                                            hover:bg-red-950/60
                                            hover:text-red-300
                                            transition
                                        "
                                    >

                                        <LogOut
                                            size={18}
                                        />

                                        <span>
                                            Log out
                                        </span>

                                    </button>

                                </div>

                            )}

                        </div>

                    )}

                </div>

            </div>


            <style>{`

                @keyframes accountMenu {

                    from {

                        opacity: 0;

                        transform:
                            translateY(-8px)
                            scale(0.96);

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
                        0.2s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        );

                    transform-origin:
                        top right;

                }

            `}</style>

        </nav>

    );

}
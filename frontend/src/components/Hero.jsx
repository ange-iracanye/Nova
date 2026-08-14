import {
    ArrowRight,
    Sparkles,
    Bot,
    RotateCcw
} from "lucide-react";

import {
    useEffect,
    useState
} from "react";

import {
    useNavigate
} from "react-router-dom";


export default function Hero() {

    const navigate = useNavigate();

    const [user, setUser] =
        useState(null);

    const [animationKey, setAnimationKey] =
        useState(0);


    // =====================================
    // CHECK ACCOUNT
    // =====================================

    useEffect(() => {

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

        setAnimationKey(
            previous => previous + 1
        );

    }, []);


    // =====================================
    // START LEARNING
    // =====================================

    function startLearning() {

        navigate("/login");

    }


    // =====================================
    // DEMO
    // =====================================

    function viewDemo() {

        /*
         * Demo mode is handled by Chat.
         *
         * demo=true tells Chat not to use
         * the user's account, history or
         * personalization.
         */

        navigate("/chat?demo=true");

    }


    // =====================================
    // CONTINUE
    // =====================================

    function continueLearning() {

        const lastRoute =
            localStorage.getItem(
                "nova_last_route"
            );

        if (
            lastRoute &&
            lastRoute !== "/"
        ) {

            navigate(lastRoute);

            return;

        }

        navigate("/chat");

    }


    // =====================================
    // NEW TOPIC
    // =====================================

    function learnSomethingNew() {

        /*
         * new=true tells Chat to start
         * completely fresh.
         */

        navigate("/chat?new=true");

    }


    return (

        <section
            key={animationKey}
            className="
                relative
                min-h-[620px]
                flex
                items-center
                justify-center
                overflow-hidden
            "
        >

            {/* =================================
                BACKGROUND EFFECTS
            ================================= */}

            <div
                className="
                    absolute
                    inset-0
                    pointer-events-none
                "
            >

                <div
                    className="
                        absolute
                        top-10
                        left-1/2
                        -translate-x-1/2
                        w-[500px]
                        h-[300px]
                        bg-blue-600/10
                        blur-[120px]
                        rounded-full
                        animate-pulse
                    "
                />

                <div
                    className="
                        absolute
                        top-1/2
                        left-1/4
                        w-32
                        h-32
                        bg-blue-500/5
                        blur-3xl
                        rounded-full
                        animate-floating-one
                    "
                />

                <div
                    className="
                        absolute
                        bottom-20
                        right-1/4
                        w-40
                        h-40
                        bg-indigo-500/5
                        blur-3xl
                        rounded-full
                        animate-floating-two
                    "
                />

            </div>


            {/* =================================
                HERO CONTENT
            ================================= */}

            <div
                className="
                    relative
                    z-10
                    max-w-5xl
                    mx-auto
                    text-center
                    px-6
                "
            >

                {/* MINI LABEL */}

                <div
                    className="
                        nova-assemble
                        nova-assemble-1
                        inline-flex
                        items-center
                        gap-2
                        px-4
                        py-2
                        rounded-full
                        border
                        border-blue-500/20
                        bg-blue-500/5
                        text-blue-400
                        text-sm
                        font-medium
                        mb-7
                    "
                >

                    <Sparkles
                        size={16}
                    />

                    AI-Powered Learning

                </div>


                {/* LOGO */}

                <div
                    className="
                        nova-assemble
                        nova-assemble-2
                        flex
                        justify-center
                        mb-6
                    "
                >

                    <div
                        className="
                            relative
                            w-20
                            h-20
                            flex
                            items-center
                            justify-center
                        "
                    >

                        <div
                            className="
                                absolute
                                inset-0
                                rounded-3xl
                                bg-blue-500/10
                                blur-xl
                                animate-pulse
                            "
                        />

                        <Bot
                            size={62}
                            strokeWidth={1.4}
                            className="
                                relative
                                text-blue-400
                            "
                        />

                    </div>

                </div>


                {/* TITLE */}

                <h1
                    className="
                        nova-assemble
                        nova-assemble-3
                        text-5xl
                        md:text-7xl
                        font-bold
                        leading-[1.05]
                        tracking-tight
                    "
                >

                    Learn Smarter with

                    <span
                        className="
                            block
                            mt-2
                            text-blue-500
                        "
                    >
                        Nova AI
                    </span>

                </h1>


                {/* DESCRIPTION */}

                <p
                    className="
                        nova-assemble
                        nova-assemble-4
                        text-slate-400
                        text-lg
                        md:text-xl
                        mt-8
                        max-w-2xl
                        mx-auto
                        leading-8
                    "
                >

                    Your personal AI tutor that adapts
                    to your level, remembers what you've
                    learned, and helps you improve every day.

                </p>


                {/* =================================
                    BUTTONS
                ================================= */}

                <div
                    className="
                        nova-assemble
                        nova-assemble-5
                        flex
                        flex-col
                        sm:flex-row
                        justify-center
                        gap-4
                        mt-12
                    "
                >

                    {!user ? (

                        <>

                            {/* START LEARNING */}

                            <button
                                onClick={
                                    startLearning
                                }
                                className="
                                    group
                                    bg-blue-600
                                    hover:bg-blue-500
                                    px-8
                                    py-4
                                    rounded-2xl
                                    flex
                                    items-center
                                    justify-center
                                    gap-3
                                    font-semibold
                                    shadow-xl
                                    shadow-blue-900/20
                                    hover:shadow-blue-900/40
                                    hover:-translate-y-1
                                    transition-all
                                    duration-300
                                "
                            >

                                Start Learning

                                <ArrowRight
                                    size={20}
                                    className="
                                        transition-transform
                                        duration-300
                                        group-hover:translate-x-1
                                    "
                                />

                            </button>


                            {/* DEMO */}

                            <button
                                onClick={
                                    viewDemo
                                }
                                className="
                                    group
                                    border
                                    border-slate-700
                                    bg-slate-900/40
                                    hover:bg-slate-900
                                    px-8
                                    py-4
                                    rounded-2xl
                                    flex
                                    items-center
                                    justify-center
                                    gap-3
                                    text-slate-200
                                    hover:text-white
                                    hover:-translate-y-1
                                    transition-all
                                    duration-300
                                "
                            >

                                View Demo

                                <RotateCcw
                                    size={18}
                                    className="
                                        transition-transform
                                        duration-500
                                        group-hover:rotate-180
                                    "
                                />

                            </button>

                        </>

                    ) : (

                        <>

                            {/* CONTINUE */}

                            <button
                                onClick={
                                    continueLearning
                                }
                                className="
                                    group
                                    bg-blue-600
                                    hover:bg-blue-500
                                    px-8
                                    py-4
                                    rounded-2xl
                                    flex
                                    items-center
                                    justify-center
                                    gap-3
                                    font-semibold
                                    shadow-xl
                                    shadow-blue-900/20
                                    hover:shadow-blue-900/40
                                    hover:-translate-y-1
                                    transition-all
                                    duration-300
                                "
                            >

                                Continue Learning

                                <ArrowRight
                                    size={20}
                                    className="
                                        transition-transform
                                        duration-300
                                        group-hover:translate-x-1
                                    "
                                />

                            </button>


                            {/* NEW */}

                            <button
                                onClick={
                                    learnSomethingNew
                                }
                                className="
                                    group
                                    border
                                    border-slate-700
                                    bg-slate-900/40
                                    hover:bg-slate-900
                                    px-8
                                    py-4
                                    rounded-2xl
                                    flex
                                    items-center
                                    justify-center
                                    gap-3
                                    text-slate-200
                                    hover:text-white
                                    hover:-translate-y-1
                                    transition-all
                                    duration-300
                                "
                            >

                                Learn Something New

                                <Sparkles
                                    size={18}
                                    className="
                                        transition-transform
                                        duration-500
                                        group-hover:rotate-12
                                        group-hover:scale-110
                                    "
                                />

                            </button>

                        </>

                    )}

                </div>

            </div>


            {/* =================================
                ANIMATIONS
            ================================= */}

            <style>{`

                /*
                 * ELEMENTS ASSEMBLE INTO PLACE
                 */

                .nova-assemble {

                    opacity: 0;

                    animation:
                        novaAssemble
                        0.9s
                        cubic-bezier(
                            0.22,
                            1,
                            0.36,
                            1
                        )
                        forwards;

                }


                .nova-assemble-1 {

                    transform:
                        translateY(-80px)
                        translateX(-40px)
                        rotate(-8deg)
                        scale(0.8);

                    animation-delay: 0.05s;

                }


                .nova-assemble-2 {

                    transform:
                        translateY(70px)
                        translateX(50px)
                        rotate(10deg)
                        scale(0.7);

                    animation-delay: 0.12s;

                }


                .nova-assemble-3 {

                    transform:
                        translateX(-120px)
                        translateY(30px)
                        rotate(-3deg)
                        scale(0.9);

                    animation-delay: 0.2s;

                }


                .nova-assemble-4 {

                    transform:
                        translateX(100px)
                        translateY(40px)
                        rotate(2deg)
                        scale(0.92);

                    animation-delay: 0.32s;

                }


                .nova-assemble-5 {

                    transform:
                        translateY(100px)
                        scale(0.8);

                    animation-delay: 0.44s;

                }


                @keyframes novaAssemble {

                    0% {

                        opacity: 0;

                    }

                    60% {

                        opacity: 1;

                    }

                    100% {

                        opacity: 1;

                        transform:
                            translateX(0)
                            translateY(0)
                            rotate(0)
                            scale(1);

                    }

                }


                /*
                 * FLOATING BACKGROUND
                 */

                @keyframes floatingOne {

                    0%,
                    100% {

                        transform:
                            translate(0, 0);

                    }

                    50% {

                        transform:
                            translate(30px, -25px);

                    }

                }


                @keyframes floatingTwo {

                    0%,
                    100% {

                        transform:
                            translate(0, 0);

                    }

                    50% {

                        transform:
                            translate(-25px, 30px);

                    }

                }


                .animate-floating-one {

                    animation:
                        floatingOne
                        7s
                        ease-in-out
                        infinite;

                }


                .animate-floating-two {

                    animation:
                        floatingTwo
                        9s
                        ease-in-out
                        infinite;

                }

            `}</style>

        </section>

    );

}
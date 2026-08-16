import React from "react";
import { Link } from "react-router-dom";
import {
    ArrowRight,
    Brain,
    ChartNoAxesCombined,
    Sparkles,
    BookOpen,
    ChevronRight
} from "lucide-react";


// ============================================================
// NOVA HOME PAGE
// ============================================================

export default function Home() {

    return (
        <main className="relative min-h-screen overflow-hidden bg-[#020617] text-white">

            {/* =================================================
                BACKGROUND
               ================================================= */}

            <div
                className="pointer-events-none absolute inset-0 overflow-hidden"
                aria-hidden="true"
            >

                <div
                    className="
                        absolute
                        left-1/2
                        top-[-260px]
                        h-[620px]
                        w-[620px]
                        -translate-x-1/2
                        rounded-full
                        bg-cyan-500/[0.08]
                        blur-[120px]
                    "
                />

                <div
                    className="
                        absolute
                        left-[-180px]
                        top-[35%]
                        h-[420px]
                        w-[420px]
                        rounded-full
                        bg-violet-500/[0.07]
                        blur-[110px]
                    "
                />

                <div
                    className="
                        absolute
                        right-[-180px]
                        top-[55%]
                        h-[420px]
                        w-[420px]
                        rounded-full
                        bg-blue-500/[0.06]
                        blur-[110px]
                    "
                />

                <div
                    className="
                        absolute
                        inset-0
                        opacity-[0.035]
                        [background-image:linear-gradient(rgba(255,255,255,.5)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.5)_1px,transparent_1px)]
                        [background-size:48px_48px]
                    "
                />

            </div>


            {/* =================================================
                NAVIGATION
               ================================================= */}

            <header
                className="
                    relative
                    z-10
                    mx-auto
                    flex
                    w-full
                    max-w-7xl
                    items-center
                    justify-between
                    px-6
                    py-6
                    lg:px-8
                "
            >

                <Link
                    to="/"
                    className="group flex items-center gap-3"
                >

                    <div
                        className="
                            relative
                            flex
                            h-10
                            w-10
                            items-center
                            justify-center
                            overflow-hidden
                            rounded-xl
                            border
                            border-white/10
                            bg-white/[0.06]
                            shadow-[0_0_30px_rgba(34,211,238,0.08)]
                        "
                    >

                        <div
                            className="
                                absolute
                                inset-0
                                bg-gradient-to-br
                                from-cyan-400/20
                                via-transparent
                                to-violet-500/20
                            "
                        />

                        <span
                            className="
                                relative
                                text-sm
                                font-bold
                                tracking-tight
                            "
                        >
                            N
                        </span>

                    </div>


                    <div>

                        <div
                            className="
                                text-sm
                                font-semibold
                                tracking-[0.18em]
                            "
                        >
                            NOVA
                        </div>

                        <div
                            className="
                                text-[10px]
                                font-medium
                                tracking-[0.18em]
                                text-slate-500
                            "
                        >
                            AI LEARNING
                        </div>

                    </div>

                </Link>


                <nav
                    className="
                        hidden
                        items-center
                        gap-1
                        md:flex
                    "
                >

                    <Link
                        to="/chat"
                        className="
                            rounded-lg
                            px-4
                            py-2
                            text-sm
                            text-slate-400
                            transition
                            hover:bg-white/[0.05]
                            hover:text-white
                        "
                    >
                        Learn
                    </Link>

                    <Link
                        to="/dashboard"
                        className="
                            rounded-lg
                            px-4
                            py-2
                            text-sm
                            text-slate-400
                            transition
                            hover:bg-white/[0.05]
                            hover:text-white
                        "
                    >
                        Dashboard
                    </Link>

                    <Link
                        to="/settings"
                        className="
                            rounded-lg
                            px-4
                            py-2
                            text-sm
                            text-slate-400
                            transition
                            hover:bg-white/[0.05]
                            hover:text-white
                        "
                    >
                        Settings
                    </Link>

                </nav>


                <Link
                    to="/chat"
                    className="
                        hidden
                        items-center
                        gap-2
                        rounded-xl
                        border
                        border-white/10
                        bg-white/[0.06]
                        px-4
                        py-2.5
                        text-sm
                        font-medium
                        transition
                        hover:border-white/20
                        hover:bg-white/[0.10]
                        sm:flex
                    "
                >
                    Start learning

                    <ArrowRight size={15} />

                </Link>

            </header>


            {/* =================================================
                HERO
               ================================================= */}

            <section
                className="
                    relative
                    z-10
                    mx-auto
                    flex
                    min-h-[calc(100vh-88px)]
                    w-full
                    max-w-7xl
                    items-center
                    px-6
                    pb-24
                    pt-16
                    lg:px-8
                    lg:pt-8
                "
            >

                <div
                    className="
                        grid
                        w-full
                        items-center
                        gap-16
                        lg:grid-cols-[1.05fr_0.95fr]
                        lg:gap-12
                    "
                >

                    {/* =================================================
                        HERO COPY
                       ================================================= */}

                    <div>

                        <div
                            className="
                                mb-7
                                inline-flex
                                items-center
                                gap-2
                                rounded-full
                                border
                                border-cyan-400/10
                                bg-cyan-400/[0.06]
                                px-3.5
                                py-2
                                text-xs
                                font-medium
                                text-cyan-200
                            "
                        >

                            <Sparkles size={13} />

                            Adaptive learning, built around you

                        </div>


                        <h1
                            className="
                                max-w-3xl
                                text-5xl
                                font-semibold
                                leading-[0.98]
                                tracking-[-0.045em]
                                sm:text-6xl
                                lg:text-7xl
                            "
                        >

                            Learn smarter.

                            <span
                                className="
                                    block
                                    bg-gradient-to-r
                                    from-cyan-200
                                    via-white
                                    to-violet-300
                                    bg-clip-text
                                    text-transparent
                                "
                            >
                                Understand more.
                            </span>

                        </h1>


                        <p
                            className="
                                mt-7
                                max-w-xl
                                text-base
                                leading-7
                                text-slate-400
                                sm:text-lg
                            "
                        >
                            Nova is your adaptive AI tutor. It explains
                            difficult ideas, remembers how you learn,
                            and adjusts its teaching to your progress.
                        </p>


                        <div
                            className="
                                mt-9
                                flex
                                flex-col
                                gap-3
                                sm:flex-row
                            "
                        >

                            <Link
                                to="/chat"
                                className="
                                    group
                                    inline-flex
                                    items-center
                                    justify-center
                                    gap-2.5
                                    rounded-xl
                                    bg-white
                                    px-5
                                    py-3.5
                                    text-sm
                                    font-semibold
                                    text-slate-950
                                    shadow-[0_10px_40px_rgba(255,255,255,0.08)]
                                    transition
                                    hover:-translate-y-0.5
                                    hover:bg-slate-100
                                "
                            >

                                Start learning

                                <ArrowRight
                                    size={17}
                                    className="
                                        transition
                                        group-hover:translate-x-0.5
                                    "
                                />

                            </Link>


                            <Link
                                to="/dashboard"
                                className="
                                    inline-flex
                                    items-center
                                    justify-center
                                    gap-2
                                    rounded-xl
                                    border
                                    border-white/10
                                    bg-white/[0.04]
                                    px-5
                                    py-3.5
                                    text-sm
                                    font-medium
                                    text-white
                                    transition
                                    hover:border-white/20
                                    hover:bg-white/[0.07]
                                "
                            >
                                View dashboard

                                <ChevronRight size={16} />

                            </Link>

                        </div>


                        {/* TRUST LINE */}

                        <div
                            className="
                                mt-10
                                flex
                                items-center
                                gap-3
                                text-xs
                                text-slate-500
                            "
                        >

                            <div
                                className="
                                    h-1.5
                                    w-1.5
                                    rounded-full
                                    bg-emerald-400
                                    shadow-[0_0_10px_rgba(52,211,153,0.7)]
                                "
                            />

                            Ready to help you learn

                            <span className="text-slate-700">
                                •
                            </span>

                            Available whenever you need it

                        </div>

                    </div>


                    {/* =================================================
                        NOVA ORB / PRODUCT PREVIEW
                       ================================================= */}

                    <div
                        className="
                            relative
                            flex
                            min-h-[480px]
                            items-center
                            justify-center
                        "
                    >

                        {/* Outer glow */}

                        <div
                            className="
                                absolute
                                h-72
                                w-72
                                rounded-full
                                bg-cyan-400/[0.10]
                                blur-[90px]
                            "
                        />


                        {/* Orbit */}

                        <div
                            className="
                                absolute
                                h-[390px]
                                w-[390px]
                                rounded-full
                                border
                                border-white/[0.05]
                            "
                        />

                        <div
                            className="
                                absolute
                                h-[300px]
                                w-[300px]
                                rounded-full
                                border
                                border-white/[0.07]
                            "
                        />


                        {/* Main orb */}

                        <div
                            className="
                                relative
                                flex
                                h-52
                                w-52
                                items-center
                                justify-center
                                rounded-full
                                border
                                border-white/10
                                bg-gradient-to-br
                                from-cyan-300/20
                                via-slate-900
                                to-violet-500/20
                                shadow-[0_0_100px_rgba(34,211,238,0.12)]
                            "
                        >

                            <div
                                className="
                                    absolute
                                    inset-5
                                    rounded-full
                                    border
                                    border-white/[0.08]
                                    bg-slate-950/70
                                    backdrop-blur-xl
                                "
                            />

                            <div
                                className="
                                    relative
                                    flex
                                    h-24
                                    w-24
                                    items-center
                                    justify-center
                                    rounded-[30%]
                                    border
                                    border-cyan-200/20
                                    bg-white/[0.05]
                                    shadow-[0_0_50px_rgba(34,211,238,0.12)]
                                "
                            >

                                <span
                                    className="
                                        text-5xl
                                        font-semibold
                                        tracking-[-0.06em]
                                        text-white
                                    "
                                >
                                    N
                                </span>

                            </div>

                        </div>


                        {/* Floating cards */}

                        <div
                            className="
                                absolute
                                left-0
                                top-16
                                rounded-2xl
                                border
                                border-white/10
                                bg-slate-950/80
                                p-4
                                shadow-2xl
                                backdrop-blur-xl
                                sm:left-5
                            "
                        >

                            <div
                                className="
                                    flex
                                    items-center
                                    gap-3
                                "
                            >

                                <div
                                    className="
                                        flex
                                        h-9
                                        w-9
                                        items-center
                                        justify-center
                                        rounded-xl
                                        bg-cyan-400/10
                                        text-cyan-300
                                    "
                                >
                                    <Brain size={17} />
                                </div>

                                <div>

                                    <p
                                        className="
                                            text-xs
                                            font-medium
                                            text-white
                                        "
                                    >
                                        Adaptive tutoring
                                    </p>

                                    <p
                                        className="
                                            mt-0.5
                                            text-[11px]
                                            text-slate-500
                                        "
                                    >
                                        Adjusting to your level
                                    </p>

                                </div>

                            </div>

                        </div>


                        <div
                            className="
                                absolute
                                bottom-16
                                right-0
                                rounded-2xl
                                border
                                border-white/10
                                bg-slate-950/80
                                p-4
                                shadow-2xl
                                backdrop-blur-xl
                                sm:right-5
                            "
                        >

                            <div
                                className="
                                    flex
                                    items-center
                                    gap-3
                                "
                            >

                                <div
                                    className="
                                        flex
                                        h-9
                                        w-9
                                        items-center
                                        justify-center
                                        rounded-xl
                                        bg-violet-400/10
                                        text-violet-300
                                    "
                                >
                                    <ChartNoAxesCombined size={17} />
                                </div>

                                <div>

                                    <p
                                        className="
                                            text-xs
                                            font-medium
                                            text-white
                                        "
                                    >
                                        Your progress
                                    </p>

                                    <p
                                        className="
                                            mt-0.5
                                            text-[11px]
                                            text-slate-500
                                        "
                                    >
                                        Track what you understand
                                    </p>

                                </div>

                            </div>

                        </div>

                    </div>

                </div>

            </section>


            {/* =================================================
                FEATURES
               ================================================= */}

            <section
                className="
                    relative
                    z-10
                    border-t
                    border-white/[0.06]
                "
            >

                <div
                    className="
                        mx-auto
                        w-full
                        max-w-7xl
                        px-6
                        py-20
                        lg:px-8
                    "
                >

                    <div
                        className="
                            max-w-2xl
                        "
                    >

                        <p
                            className="
                                text-xs
                                font-semibold
                                tracking-[0.18em]
                                text-cyan-300
                            "
                        >
                            BUILT FOR LEARNING
                        </p>

                        <h2
                            className="
                                mt-3
                                text-3xl
                                font-semibold
                                tracking-[-0.03em]
                                sm:text-4xl
                            "
                        >
                            More than just an AI chatbot.
                        </h2>

                        <p
                            className="
                                mt-4
                                text-sm
                                leading-6
                                text-slate-400
                                sm:text-base
                            "
                        >
                            Nova is designed around the learning process,
                            not just generating another answer and sending
                            you on your way.
                        </p>

                    </div>


                    <div
                        className="
                            mt-12
                            grid
                            gap-4
                            md:grid-cols-3
                        "
                    >

                        <FeatureCard
                            icon={<Brain size={20} />}
                            title="Adaptive learning"
                            description="Nova adjusts explanations and difficulty based on what you actually understand."
                        />

                        <FeatureCard
                            icon={<BookOpen size={20} />}
                            title="Learn by understanding"
                            description="Break complicated subjects into clear steps instead of throwing walls of information at you."
                        />

                        <FeatureCard
                            icon={<ChartNoAxesCombined size={20} />}
                            title="Track your progress"
                            description="See what you have learned, what needs work, and how your understanding develops over time."
                        />

                    </div>

                </div>

            </section>


            {/* =================================================
                FOOTER
               ================================================= */}

            <footer
                className="
                    relative
                    z-10
                    border-t
                    border-white/[0.06]
                "
            >

                <div
                    className="
                        mx-auto
                        flex
                        max-w-7xl
                        flex-col
                        gap-4
                        px-6
                        py-8
                        text-xs
                        text-slate-500
                        sm:flex-row
                        sm:items-center
                        sm:justify-between
                        lg:px-8
                    "
                >

                    <span>
                        Nova AI · Adaptive learning
                    </span>

                    <div
                        className="
                            flex
                            items-center
                            gap-5
                        "
                    >

                        <Link
                            to="/settings"
                            className="transition hover:text-white"
                        >
                            Settings
                        </Link>

                        <Link
                            to="/chat"
                            className="transition hover:text-white"
                        >
                            Start learning
                        </Link>

                    </div>

                </div>

            </footer>

        </main>
    );
}


// ============================================================
// FEATURE CARD
// ============================================================

function FeatureCard({
    icon,
    title,
    description
}) {

    return (

        <div
            className="
                group
                relative
                overflow-hidden
                rounded-2xl
                border
                border-white/[0.08]
                bg-white/[0.025]
                p-6
                transition
                duration-300
                hover:-translate-y-1
                hover:border-white/[0.14]
                hover:bg-white/[0.04]
            "
        >

            <div
                className="
                    absolute
                    right-0
                    top-0
                    h-24
                    w-24
                    translate-x-8
                    -translate-y-8
                    rounded-full
                    bg-cyan-400/[0.05]
                    blur-2xl
                    transition
                    group-hover:bg-cyan-400/[0.10]
                "
            />


            <div
                className="
                    relative
                    flex
                    h-11
                    w-11
                    items-center
                    justify-center
                    rounded-xl
                    border
                    border-white/[0.08]
                    bg-white/[0.04]
                    text-cyan-300
                "
            >
                {icon}
            </div>


            <h3
                className="
                    relative
                    mt-5
                    text-base
                    font-semibold
                "
            >
                {title}
            </h3>


            <p
                className="
                    relative
                    mt-2
                    text-sm
                    leading-6
                    text-slate-500
                "
            >
                {description}
            </p>

        </div>
    );
}
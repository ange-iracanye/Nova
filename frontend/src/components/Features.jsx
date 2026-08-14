import {
    Brain,
    GraduationCap,
    BarChart3,
    ArrowRight
} from "lucide-react";

import { useNavigate } from "react-router-dom";

const features = [

    {
        icon: Brain,
        title: "Adaptive AI",
        text: "Nova changes explanations based on your understanding.",
        action: "/chat?mode=adaptive"
    },

    {
        icon: GraduationCap,
        title: "Personal Tutor",
        text: "Learn step by step instead of receiving simple answers.",
        action: "/chat?mode=personal"
    },

    {
        icon: BarChart3,
        title: "Track Progress",
        text: "See your learning activity, subjects, strengths and progress.",
        action: "/dashboard"
    }

];

export default function Features() {

    const navigate = useNavigate();

    return (

        <section
            className="
                py-20
            "
        >

            <h2
                className="
                    text-4xl
                    font-bold
                    text-center
                    mb-16
                "
            >
                Why Nova?
            </h2>


            <div
                className="
                    grid
                    md:grid-cols-3
                    gap-8
                "
            >

                {features.map(
                    (feature, index) => {

                        const Icon = feature.icon;

                        return (

                            <button
                                key={index}
                                onClick={() =>
                                    navigate(
                                        feature.action
                                    )
                                }
                                className="
                                    group
                                    text-left
                                    bg-slate-900
                                    rounded-2xl
                                    p-8
                                    border
                                    border-slate-800
                                    hover:border-blue-500/60
                                    transition-all
                                    duration-500
                                    hover:-translate-y-2
                                    hover:shadow-2xl
                                    hover:shadow-blue-900/10
                                    relative
                                    overflow-hidden
                                "
                            >

                                {/* GLOW */}

                                <div
                                    className="
                                        absolute
                                        -top-20
                                        -right-20
                                        w-40
                                        h-40
                                        bg-blue-500/10
                                        blur-3xl
                                        opacity-0
                                        group-hover:opacity-100
                                        transition
                                    "
                                />


                                <div
                                    className="
                                        relative
                                    "
                                >

                                    <Icon
                                        className="
                                            text-blue-500
                                            mb-6
                                            transition-all
                                            duration-500
                                            group-hover:scale-110
                                            group-hover:-rotate-3
                                        "
                                        size={40}
                                    />


                                    <h3
                                        className="
                                            text-2xl
                                            font-semibold
                                            mb-4
                                        "
                                    >
                                        {feature.title}
                                    </h3>


                                    <p
                                        className="
                                            text-slate-400
                                            leading-7
                                        "
                                    >
                                        {feature.text}
                                    </p>


                                    <div
                                        className="
                                            mt-7
                                            flex
                                            items-center
                                            gap-2
                                            text-blue-400
                                            text-sm
                                            font-semibold
                                            transition
                                            group-hover:gap-3
                                        "
                                    >

                                        Explore

                                        <ArrowRight
                                            size={16}
                                        />

                                    </div>

                                </div>

                            </button>

                        );

                    }
                )}

            </div>

        </section>

    );
}


import {
    ArrowLeft,
    BarChart3,
    BookOpen,
    Brain,
    Target,
    TrendingUp
} from "lucide-react";

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";


const API_URL = "http://127.0.0.1:8000";


export default function Progress() {

    const navigate = useNavigate();

    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);


    useEffect(() => {

        async function loadProgress() {

            try {

                const response = await fetch(
                    `${API_URL}/dashboard`
                );

                if (!response.ok) {
                    throw new Error(
                        "Unable to load progress."
                    );
                }

                const result =
                    await response.json();

                setData(result);

            } catch (error) {

                console.error(
                    "Progress error:",
                    error
                );

            } finally {

                setLoading(false);

            }

        }

        loadProgress();

    }, []);


    const student =
        data?.student || {};

    const knowledge =
        data?.knowledge || {};

    const memory =
        data?.memory || 0;


    const questionCount =
        student.questions ||
        student.question_count ||
        student.questions_asked ||
        0;


    const subjects =
        typeof knowledge === "object"
            ? Object.keys(knowledge)
            : [];


    return (

        <div
            className="
                min-h-screen
                bg-slate-950
                text-white
                px-6
                py-10
            "
        >

            <div
                className="
                    max-w-6xl
                    mx-auto
                "
            >

                {/* HEADER */}

                <button
                    onClick={() =>
                        navigate("/")
                    }
                    className="
                        flex
                        items-center
                        gap-2
                        text-slate-400
                        hover:text-white
                        transition
                        mb-10
                    "
                >

                    <ArrowLeft size={18} />

                    Back to Home

                </button>


                <div className="mb-12">

                    <div
                        className="
                            flex
                            items-center
                            gap-3
                            text-blue-400
                            mb-4
                        "
                    >

                        <BarChart3 size={24} />

                        Learning Progress

                    </div>


                    <h1
                        className="
                            text-4xl
                            md:text-5xl
                            font-bold
                        "
                    >
                        Your Progress
                    </h1>


                    <p
                        className="
                            text-slate-400
                            mt-4
                            text-lg
                        "
                    >
                        See how your learning activity is developing
                        across Nova.
                    </p>

                </div>


                {loading ? (

                    <div
                        className="
                            text-slate-500
                            animate-pulse
                        "
                    >
                        Loading your progress...
                    </div>

                ) : (

                    <>

                        {/* STAT CARDS */}

                        <div
                            className="
                                grid
                                md:grid-cols-4
                                gap-5
                                mb-10
                            "
                        >

                            <StatCard
                                icon={BookOpen}
                                title="Questions"
                                value={questionCount}
                            />

                            <StatCard
                                icon={Brain}
                                title="Memory"
                                value={memory}
                            />

                            <StatCard
                                icon={Target}
                                title="Subjects"
                                value={subjects.length}
                            />

                            <StatCard
                                icon={TrendingUp}
                                title="Learning"
                                value={
                                    subjects.length > 0
                                        ? "Active"
                                        : "Starting"
                                }
                            />

                        </div>


                        {/* SUBJECTS */}

                        <div
                            className="
                                bg-slate-900
                                border
                                border-slate-800
                                rounded-2xl
                                p-7
                            "
                        >

                            <h2
                                className="
                                    text-2xl
                                    font-semibold
                                    mb-6
                                "
                            >
                                Subjects
                            </h2>


                            {subjects.length === 0 ? (

                                <div
                                    className="
                                        text-slate-500
                                        py-8
                                    "
                                >
                                    Start asking Nova questions to
                                    begin building your learning
                                    progress.
                                </div>

                            ) : (

                                <div
                                    className="
                                        grid
                                        md:grid-cols-2
                                        lg:grid-cols-3
                                        gap-4
                                    "
                                >

                                    {subjects.map(
                                        subject => {

                                            const subjectData =
                                                knowledge[
                                                    subject
                                                ];

                                            return (

                                                <div
                                                    key={subject}
                                                    className="
                                                        bg-slate-950
                                                        border
                                                        border-slate-800
                                                        rounded-xl
                                                        p-5
                                                        hover:border-blue-500/40
                                                        transition
                                                    "
                                                >

                                                    <div
                                                        className="
                                                            font-semibold
                                                            capitalize
                                                        "
                                                    >
                                                        {subject}
                                                    </div>


                                                    <div
                                                        className="
                                                            text-slate-500
                                                            text-sm
                                                            mt-2
                                                        "
                                                    >
                                                        {typeof subjectData ===
                                                        "object"
                                                            ? "Learning data recorded"
                                                            : String(
                                                                subjectData
                                                            )}
                                                    </div>

                                                </div>

                                            );

                                        }
                                    )}

                                </div>

                            )}

                        </div>

                    </>

                )}

            </div>

        </div>

    );

}


function StatCard({
    icon: Icon,
    title,
    value
}) {

    return (

        <div
            className="
                bg-slate-900
                border
                border-slate-800
                rounded-2xl
                p-6
                hover:border-blue-500/40
                hover:-translate-y-1
                transition-all
                duration-300
            "
        >

            <Icon
                size={25}
                className="text-blue-500 mb-5"
            />


            <div
                className="
                    text-3xl
                    font-bold
                "
            >
                {value}
            </div>


            <div
                className="
                    text-slate-500
                    mt-2
                "
            >
                {title}
            </div>

        </div>

    );

}
import { useEffect, useState } from "react";

import {
    Save,
    ArrowLeft,
    User,
    Brain,
    MessageSquare,
    SlidersHorizontal,
    Lightbulb,
    RotateCcw,
    Check,
    Sparkles
} from "lucide-react";

import { useNavigate } from "react-router-dom";


const API_URL =
    "http://127.0.0.1:8000";


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


export default function Settings() {

    const navigate = useNavigate();


    const [
        settings,
        setSettings
    ] = useState(
        DEFAULT_SETTINGS
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


    useEffect(() => {

        loadSettings();

    }, []);


    async function loadSettings() {

        try {

            const response =
                await fetch(
                    `${API_URL}/settings`
                );


            if (!response.ok) {

                throw new Error(
                    "Failed to load settings."
                );

            }


            const data =
                await response.json();


            setSettings({

                ...DEFAULT_SETTINGS,

                ...data

            });

        } catch (err) {

            console.error(err);

            setError(
                "Could not load your settings."
            );

        } finally {

            setLoading(false);

        }

    }


    function update(
        key,
        value
    ) {

        setSettings(
            previous => ({

                ...previous,

                [key]: value

            })
        );


        setSaved(false);

    }


    async function saveSettings() {

        setSaving(true);

        setSaved(false);

        setError("");


        try {

            const response =
                await fetch(

                    `${API_URL}/settings`,

                    {

                        method:
                            "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                settings
                            )
                    }
                );


            if (!response.ok) {

                throw new Error(
                    "Failed to save settings."
                );

            }


            const data =
                await response.json();


            setSettings({

                ...DEFAULT_SETTINGS,

                ...data

            });


            setSaved(true);


            setTimeout(
                () => setSaved(false),
                2500
            );


        } catch (err) {

            console.error(err);

            setError(
                "Could not save your settings."
            );

        } finally {

            setSaving(false);

        }

    }


    function resetSettings() {

        const confirmed =
            window.confirm(
                "Reset all Nova settings to their defaults?"
            );


        if (!confirmed) {

            return;

        }


        setSettings(
            DEFAULT_SETTINGS
        );

        setSaved(false);

    }


    if (loading) {

        return (

            <div className="
                min-h-screen
                bg-gray-950
                text-white
                flex
                items-center
                justify-center
            ">

                <div className="
                    text-gray-400
                    animate-pulse
                ">

                    Loading Nova settings...

                </div>

            </div>
        );

    }


    return (

        <div className="
            min-h-screen
            bg-gray-950
            text-white
            px-5
            py-8
        ">

            <div className="
                max-w-4xl
                mx-auto
            ">

                {/* =================================
                    HEADER
                ================================= */}

                <div className="
                    flex
                    items-center
                    justify-between
                    mb-10
                ">

                    <div>

                        <button
                            onClick={() =>
                                navigate("/")
                            }
                            className="
                                flex
                                items-center
                                gap-2
                                text-gray-400
                                hover:text-white
                                transition
                                mb-6
                            "
                        >

                            <ArrowLeft
                                size={18}
                            />

                            Back

                        </button>


                        <div className="
                            flex
                            items-center
                            gap-3
                            mb-2
                        ">

                            <Sparkles
                                size={28}
                                className="text-blue-400"
                            />

                            <h1 className="
                                text-4xl
                                font-bold
                            ">

                                Nova Settings

                            </h1>

                        </div>


                        <p className="
                            text-gray-400
                            max-w-2xl
                        ">

                            Configure how Nova thinks,
                            teaches, explains and
                            interacts with you.

                        </p>

                    </div>


                    <button
                        onClick={resetSettings}
                        className="
                            hidden
                            sm:flex
                            items-center
                            gap-2
                            px-4
                            py-2
                            rounded-xl
                            border
                            border-gray-800
                            text-gray-400
                            hover:text-white
                            hover:bg-gray-900
                            transition
                        "
                    >

                        <RotateCcw
                            size={16}
                        />

                        Reset

                    </button>

                </div>


                {error && (

                    <div className="
                        mb-6
                        rounded-xl
                        border
                        border-red-900
                        bg-red-950/40
                        px-4
                        py-3
                        text-red-300
                    ">

                        {error}

                    </div>

                )}


                <div className="
                    space-y-6
                ">


                    {/* =================================
                        PROFILE
                    ================================= */}

                    <Section
                        icon={<User size={20} />}
                        title="Profile"
                        description="Tell Nova who it is teaching."
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
                                placeholder="Your name"
                                className="
                                    input
                                "
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
                            description="Nova uses this when deciding vocabulary and explanation depth."
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

                    </Section>


                    {/* =================================
                        TEACHING
                    ================================= */}

                    <Section
                        icon={<Brain size={20} />}
                        title="Teaching intelligence"
                        description="Control how Nova teaches instead of only how it looks."
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
                            description="Use your previous learning behavior, strengths and weaknesses to personalize explanations."
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
                            label="Step-by-step reasoning"
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

                    </Section>


                    {/* =================================
                        RESPONSE
                    ================================= */}

                    <Section
                        icon={<MessageSquare size={20} />}
                        title="Response behavior"
                        description="Control the shape and personality of Nova's answers."
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

                    </Section>


                    {/* =================================
                        CORRECTIONS
                    ================================= */}

                    <Section
                        icon={<Lightbulb size={20} />}
                        title="Corrections & practice"
                        description="Control what happens when you make a mistake."
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

                    </Section>


                    {/* =================================
                        AI
                    ================================= */}

                    <Section
                        icon={
                            <SlidersHorizontal
                                size={20}
                            />
                        }
                        title="AI generation"
                        description="These settings affect Nova's actual Qwen generation."
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

                    </Section>


                    {/* =================================
                        CUSTOM
                    ================================= */}

                    <Section
                        icon={
                            <Sparkles
                                size={20}
                            />
                        }
                        title="Personal instructions"
                        description="Give Nova additional instructions that should persist between conversations."
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
                                rows={5}
                                placeholder="Example: Explain difficult mathematics with simple examples and check my understanding before moving on."
                                className="
                                    input
                                    resize-none
                                "
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
                                rows={5}
                                placeholder="Example: When I ask programming questions, explain the architecture before giving the code."
                                className="
                                    input
                                    resize-none
                                "
                            />

                        </Field>

                    </Section>


                    {/* =================================
                        SAVE
                    ================================= */}

                    <button
                        onClick={
                            saveSettings
                        }
                        disabled={saving}
                        className="
                            w-full
                            bg-blue-600
                            hover:bg-blue-700
                            disabled:opacity-60
                            rounded-2xl
                            py-4
                            font-semibold
                            flex
                            items-center
                            justify-center
                            gap-2
                            transition
                            shadow-lg
                            shadow-blue-950/30
                        "
                    >

                        {saved ? (

                            <>

                                <Check
                                    size={19}
                                />

                                Settings saved

                            </>

                        ) : (

                            <>

                                <Save
                                    size={19}
                                />

                                {saving
                                    ? "Saving..."
                                    : "Save Nova settings"}

                            </>

                        )}

                    </button>

                </div>

            </div>


            {/* =================================
                LOCAL STYLES
            ================================= */}

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
                        box-shadow 0.2s;

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

            `}</style>

        </div>
    );
}


/* =====================================
   SECTION
===================================== */

function Section({
    icon,
    title,
    description,
    children
}) {

    return (

        <section className="
            bg-gray-900
            border
            border-gray-800
            rounded-2xl
            p-6
        ">

            <div className="
                flex
                items-start
                gap-3
                mb-6
            ">

                <div className="
                    w-10
                    h-10
                    rounded-xl
                    bg-blue-600/10
                    text-blue-400
                    flex
                    items-center
                    justify-center
                    shrink-0
                ">

                    {icon}

                </div>


                <div>

                    <h2 className="
                        text-xl
                        font-semibold
                    ">

                        {title}

                    </h2>


                    <p className="
                        text-sm
                        text-gray-400
                        mt-1
                    ">

                        {description}

                    </p>

                </div>

            </div>


            <div className="
                space-y-6
            ">

                {children}

            </div>

        </section>
    );
}


/* =====================================
   FIELD
===================================== */

function Field({
    label,
    description,
    children
}) {

    return (

        <div>

            <label className="
                block
                text-sm
                font-medium
                text-gray-200
                mb-1.5
            ">

                {label}

            </label>


            <p className="
                text-xs
                text-gray-500
                mb-2
            ">

                {description}

            </p>


            {children}

        </div>
    );
}


/* =====================================
   SELECT
===================================== */

function Select({
    value,
    onChange,
    options
}) {

    return (

        <select
            value={value}
            onChange={e =>
                onChange(
                    e.target.value
                )
            }
            className="
                input
            "
        >

            {options.map(
                ([label, value]) => (

                    <option
                        key={value}
                        value={value}
                    >

                        {label}

                    </option>

                )
            )}

        </select>
    );
}


/* =====================================
   TOGGLE
===================================== */

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
                onChange(!checked)
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
        >

            <div>

                <div className="
                    text-sm
                    font-medium
                    text-gray-200
                    group-hover:text-white
                    transition
                ">

                    {label}

                </div>


                <div className="
                    text-xs
                    text-gray-500
                    mt-1
                    max-w-2xl
                ">

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
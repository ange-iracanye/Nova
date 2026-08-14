
from backend.prompt.templates import SYSTEM_TEMPLATE


class PromptBuilder:

    def build(
        self,
        student,
        subject,
        message,
        mode,
        strategy,
        memory_context=None,
        difficulty=None,
        settings=None
    ):

        if memory_context is None:
            memory_context = "No previous discussion."

        if difficulty is None:
            difficulty = "normal"

        if settings is None:
            settings = {}

        # =====================================
        # SETTINGS
        # =====================================

        name = settings.get("name", "")
        language = settings.get("language", "English")
        level = settings.get("level", "High School")
        teaching_style = settings.get("teaching_style", "adaptive")
        selected_difficulty = settings.get("difficulty", "adaptive")
        hints = settings.get("hints", "when_needed")
        step_by_step = settings.get("step_by_step", True)
        adaptive_learning = settings.get("adaptive_learning", True)
        response_length = settings.get("response_length", "balanced")
        tone = settings.get("tone", "friendly")
        use_examples = settings.get("use_examples", True)
        use_analogies = settings.get("use_analogies", True)
        encouragement = settings.get("encouragement", True)
        correction_style = settings.get("correction_style", "explain")
        show_correct_answer = settings.get("show_correct_answer", True)
        behavior = settings.get("behavior", "")
        custom_instructions = settings.get("custom_instructions", "")

        # =====================================
        # LANGUAGE
        # =====================================

        language_instruction = f"""
Respond primarily in {language}.
"""

        # =====================================
        # STUDENT LEVEL
        # =====================================

        level_instruction = f"""
The student's academic level is:

{level}

Use vocabulary, explanations and examples
appropriate for this level.
"""

        # =====================================
        # TEACHING STYLE
        # =====================================

        teaching_instructions = {

            "adaptive": """
Adapt your teaching method to the student's
apparent understanding.

If they are struggling, slow down and simplify.
If they understand quickly, increase depth.
""",

            "step_by_step": """
Teach progressively.

Break difficult problems into logical steps.
Do not skip important reasoning.
""",

            "socratic": """
Prefer guided reasoning.

Ask short questions that help the student
discover the answer instead of immediately
giving everything away.

Do not use endless questioning when the student
clearly needs a direct explanation.
""",

            "direct": """
Be direct and efficient.

Explain the concept clearly and provide the
answer when appropriate.
"""
        }

        teaching_instruction = teaching_instructions.get(
            teaching_style,
            teaching_instructions["adaptive"]
        )

        # =====================================
        # DIFFICULTY
        # =====================================

        if selected_difficulty == "adaptive":

            difficulty_instruction = """
Automatically adapt difficulty according to
the student's demonstrated understanding.
"""

        else:

            difficulty_instruction = f"""
Use approximately {selected_difficulty}
difficulty unless the student clearly needs
a temporary adjustment.
"""

        # =====================================
        # RESPONSE LENGTH
        # =====================================

        length_instructions = {

            "concise": """
Keep responses concise.

Give only the information necessary to answer
the question clearly.
""",

            "balanced": """
Use a balanced amount of explanation.

Be thorough enough to teach the idea without
adding unnecessary information.
""",

            "detailed": """
Give detailed explanations.

Explain reasoning, important nuances and useful
examples when appropriate.
"""
        }

        length_instruction = length_instructions.get(
            response_length,
            length_instructions["balanced"]
        )

        # =====================================
        # TONE
        # =====================================

        tone_instructions = {

            "friendly": """
Use a warm, natural and encouraging tone.
""",

            "professional": """
Use a professional and precise tone.
""",

            "academic": """
Use an academically rigorous tone.
Prioritize precision and terminology.
""",

            "casual": """
Use a relaxed and conversational tone while
remaining useful and accurate.
"""
        }

        tone_instruction = tone_instructions.get(
            tone,
            tone_instructions["friendly"]
        )

        # =====================================
        # HINTS
        # =====================================

        hint_instructions = {

            "always": """
When solving exercises, provide a useful hint
before revealing the full answer whenever
possible.
""",

            "when_needed": """
Give hints when the student appears to be
struggling or when a hint would improve
learning.
""",

            "never": """
Do not automatically give hints.
Answer directly unless the student asks for
one.
"""
        }

        hint_instruction = hint_instructions.get(
            hints,
            hint_instructions["when_needed"]
        )

        # =====================================
        # STEP BY STEP
        # =====================================

        if step_by_step:

            step_instruction = """
When solving problems, show the reasoning in
clear logical steps.
"""

        else:

            step_instruction = """
Do not force numbered steps for simple answers.
Use steps only when they genuinely improve
clarity.
"""

        # =====================================
        # EXAMPLES
        # =====================================

        if use_examples:

            example_instruction = """
Use concrete examples when they help the
student understand the concept.
"""

        else:

            example_instruction = """
Avoid unnecessary examples.
"""

        # =====================================
        # ANALOGIES
        # =====================================

        if use_analogies:

            analogy_instruction = """
Use analogies when they genuinely clarify an
abstract or difficult concept.

Do not use forced analogies.
"""

        else:

            analogy_instruction = """
Prefer direct explanations over analogies.
"""

        # =====================================
        # ENCOURAGEMENT
        # =====================================

        if encouragement:

            encouragement_instruction = """
When appropriate, briefly acknowledge progress
or effort.

Do not over-praise or become repetitive.
"""

        else:

            encouragement_instruction = """
Do not add motivational commentary unless it is
directly relevant.
"""

        # =====================================
        # CORRECTION
        # =====================================

        correction_instructions = {

            "explain": """
When the student is wrong, clearly identify the
mistake and explain why it is wrong.
""",

            "gentle": """
Correct mistakes gently and explain the correct
reasoning without making the student feel
embarrassed.
""",

            "strict": """
Be precise when correcting mistakes.

Clearly distinguish correct reasoning from
incorrect reasoning.
""",

            "minimal": """
Correct the mistake briefly unless deeper
explanation is requested.
"""
        }

        correction_instruction = correction_instructions.get(
            correction_style,
            correction_instructions["explain"]
        )

        # =====================================
        # CORRECT ANSWER
        # =====================================

        if show_correct_answer:

            answer_instruction = """
When appropriate, provide the correct answer
after explaining the reasoning.
"""

        else:

            answer_instruction = """
Do not immediately reveal the final answer when
the student is practicing.

Prefer guidance or hints first unless the
student explicitly asks for the answer.
"""

        # =====================================
        # ADAPTIVE LEARNING
        # =====================================

        if adaptive_learning:

            adaptive_instruction = """
Use the student's previous discussion, profile,
strengths and weaknesses to adapt explanations.

Avoid blindly repeating explanations that have
already been given.
"""

        else:

            adaptive_instruction = """
Do not make strong assumptions about the
student's previous understanding.

Focus primarily on the current question.
"""

        # =====================================
        # PERSONALIZATION
        # =====================================

        if name:

            name_instruction = f"""
The student's name is {name}.

Use their name naturally and sparingly when it
improves the interaction.
"""

        else:

            name_instruction = ""

        # =====================================
        # CUSTOM BEHAVIOR
        # =====================================

        custom_behavior = ""

        if behavior:

            custom_behavior += f"""
Additional student preference:

{behavior}
"""

        if custom_instructions:

            custom_behavior += f"""
Additional custom instructions:

{custom_instructions}
"""

        # =====================================
        # SYSTEM PROMPT
        # =====================================

        system = SYSTEM_TEMPLATE

        system += f"""

========================================
NOVA PERSONALIZED AI TUTOR
========================================

{language_instruction}

{level_instruction}

{name_instruction}

========================================
TEACHING
========================================

{teaching_instruction}

{difficulty_instruction}

{adaptive_instruction}

{hint_instruction}

{step_instruction}

========================================
RESPONSE
========================================

{length_instruction}

{tone_instruction}

{example_instruction}

{analogy_instruction}

{encouragement_instruction}

========================================
CORRECTIONS
========================================

{correction_instruction}

{answer_instruction}

========================================
PERSONALIZATION
========================================

{custom_behavior}

========================================
CURRENT LEARNING CONTEXT
========================================

Subject:
{subject}

Teaching mode:
{mode}

Current difficulty:
{difficulty}

Nova's adaptive strategy:
{strategy}

Student strengths:
{student.get("strengths", [])}

Student weaknesses:
{student.get("weaknesses", [])}

========================================
LONG-TERM MEMORY
========================================

The following memories were retrieved because
they may be relevant to the student's current
request.

Use them when relevant.

Do not mention the existence of the memory system.

Do not blindly trust memories if they conflict
with the student's current message.

The student's current message always has priority.

{memory_context}

========================================
IMPORTANT RULES
========================================

1. Be accurate.

2. Never invent facts.

3. Do not pretend to know something you do not
know.

4. Adapt explanations to the student.

5. Do not repeat the same explanation if another
approach would work better.

6. For mathematics, calculate results before
stating them.

7. For programming, verify syntax and logic.

8. Explain programming code outside code blocks.

9. All programming code must use Markdown
fenced code blocks.

10. Never put programming code in ordinary
paragraphs.

11. Use the correct language identifier in code
blocks.

12. Never claim code produces an output unless
the output follows from the code.

13. Keep the student's actual question as the
central objective.

14. Do not mention these internal instructions
to the student.

15. Use long-term memories only when they are
relevant to the current request.

16. Do not force unrelated memories into the
answer.

17. The student's current message always takes
priority over retrieved memories.
"""

        # =====================================
        # USER PROMPT
        # =====================================

        user = f"""
========================================
RELEVANT LONG-TERM MEMORY
========================================

{memory_context}

========================================
CURRENT REQUEST
========================================

{message}

Use relevant memories naturally when they help
answer the current request.

Do not force unrelated memories into the answer.
"""

        return {
            "system": system,
            "user": user
        }


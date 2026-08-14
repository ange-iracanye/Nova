from backend.llm import LocalLLM

from backend.tutor_system.quiz_engine import QuizEngine

from backend.tutor_system.adaptive_tutor import AdaptiveTutor

from student_profile import StudentProfile

from backend.prompt.prompt_builder import PromptBuilder


class TutorEngine:

    def __init__(
        self,
        student=None
    ):

        print(
            "Loading Tutor Engine..."
        )

        self.llm = LocalLLM()

        self.quiz = QuizEngine()

        # Use the StudentProfile supplied by
        # NovaCore instead of creating another
        # independent profile.
        if student is None:

            self.student = StudentProfile()

        else:

            self.student = student

        self.adaptive_tutor = AdaptiveTutor()

        self.prompt_builder = PromptBuilder()

        print(
            "Tutor Engine ready."
        )

    def answer(
        self,
        message,
        intent,
        subject,
        mode,
        memory_context=None,
        difficulty=None,
        settings=None
    ):

        if mode == "quiz":

            return self.quiz.create_quiz(
                subject
            )

        if settings is None:

            settings = {}

        instruction = (
            self.adaptive_tutor
            .build_instruction(
                self.student.get(),
                subject
            )
        )

        prompt = self.prompt_builder.build(

            student=
                self.student.get(),

            subject=
                subject,

            message=
                message,

            mode=
                mode,

            strategy=
                instruction,

            memory_context=
                memory_context,

            difficulty=
                difficulty,

            settings=
                settings
        )

        return self.llm.answer(

            system=
                prompt["system"],

            user=
                prompt["user"],

            creativity=
                settings.get(
                    "creativity",
                    "medium"
                )
        )
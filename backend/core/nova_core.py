from backend.memory_system.memory_manager import MemoryManager
from backend.memory_system.learning_memory import LearningMemory
from backend.memory_system.conversation_manager import ConversationManager

from backend.tutor_system.tutor_engine import TutorEngine
from backend.tutor_system.tutor_mode import TutorModeDetector
from backend.tutor_system.adaptive_tutor import AdaptiveTutor
from backend.tutor_system.teacher_brain import TeacherBrain

from backend.brain.brain import NovaBrain

from student_profile import StudentProfile
from backend.student.knowledge_map import KnowledgeMap

from backend.learning_graph import LearningGraph
from backend.learning.analyzer import LearningAnalyzer
from backend.learning.understanding import UnderstandingTracker
from backend.learning.understanding import UnderstandingAnalyzer
from backend.learning.session_manager import SessionManager
from backend.learning.progress_tracker import ProgressTracker
from backend.learning.difficulty_engine import DifficultyEngine

from backend.intent_detector import IntentDetector
from backend.subject_detector import SubjectDetector

from backend.prompt.response_formatter import format_response

from backend.learning.answer_verifier import AnswerVerifier

from backend.settings import SettingsManager


class NovaCore:

    def __init__(
        self,
        demo=False
    ):

        print(
            "Initializing Nova Core..."
        )

        self.demo = demo

        # =====================================
        # MEMORY
        # =====================================

        self.memory = MemoryManager()

        # =====================================
        # LEARNING MEMORY
        # =====================================

        self.learning_memory = (
            LearningMemory()
        )

        # =====================================
        # CONVERSATIONS
        # =====================================

        self.conversations = (
            ConversationManager(
                persist=not demo
            )
        )

        # =====================================
        # STUDENT PROFILE
        # =====================================
        #
        # There is intentionally ONE
        # StudentProfile instance.
        #
        # TutorEngine receives this same
        # instance below.
        #

        self.student = StudentProfile()

        # =====================================
        # TUTOR
        # =====================================

        self.tutor = TutorEngine(
            student=self.student
        )

        # =====================================
        # LEARNING
        # =====================================

        self.learning = LearningGraph()

        self.intent = IntentDetector()

        self.subject = SubjectDetector()

        self.mode = TutorModeDetector()

        self.understanding = (
            UnderstandingAnalyzer()
        )

        self.knowledge_map = None

        self.analyzer = LearningAnalyzer()

        self.understanding_tracker = (
            UnderstandingTracker()
        )

        self.session = SessionManager()

        self.adaptive_tutor = AdaptiveTutor()

        self.teacher_brain = TeacherBrain()

        self.brain = NovaBrain()

        self.progress = None

        self.difficulty = DifficultyEngine()

        self.answer_verifier = (
            AnswerVerifier()
        )

        self.settings = SettingsManager()

        print(
            "Nova Core ready."
        )

    def process(
        self,
        message,
        conversation_id=None,
        user_email=None,
        forced_mode=None
    ):

        # =====================================
        # VALIDATE
        # =====================================

        if not user_email:

            raise ValueError(
                "A user email is required."
            )

        user_email = (
            user_email
            .strip()
            .lower()
        )

        # =====================================
        # USER-SPECIFIC LEARNING SYSTEMS
        # =====================================

        self.knowledge_map = KnowledgeMap(
            user_email
        )

        self.progress = ProgressTracker(
            user_email
        )

        # =====================================
        # ORIGINAL MESSAGE
        # =====================================

        message = message.strip()

        original_message = message

        # =====================================
        # CONVERSATION
        # =====================================

        if conversation_id is None:

            conversation_id = (
                self.conversations.create(
                    user_email
                )
            )

        elif self.conversations.get(
            user_email,
            conversation_id
        ) is None:

            conversation_id = (
                self.conversations.create(
                    user_email
                )
            )

        # =====================================
        # SAVE USER MESSAGE
        # =====================================

        self.conversations.add_message(
            user_email,
            conversation_id,
            "user",
            original_message
        )

        # =====================================
        # STUDENT PROFILE
        # =====================================

        self.student.add_question()

        # =====================================
        # INTENT
        # =====================================

        intent = self.intent.detect(
            original_message
        )

        # =====================================
        # TUTOR MODE
        # =====================================

        if forced_mode:

            if forced_mode == "adaptive":

                mode = "adaptive"

            elif forced_mode == "personal":

                mode = "personal"

            else:

                mode = self.mode.detect(
                    original_message
                )

        else:

            mode = self.mode.detect(
                original_message
            )

        # =====================================
        # SUBJECT
        # =====================================

        subject = self.subject.detect(
            original_message
        )

        if subject:

            self.session.start(
                subject,
                original_message,
                mode
            )

        # =====================================
        # STUDENT TRACKING
        # =====================================

        self.student.add_question(
            subject
        )

        self.understanding_tracker.update(
            subject,
            "easy"
        )

        if subject:

            self.learning.add_subject(
                subject
            )

        # =====================================
        # ANALYZE STUDENT
        # =====================================

        analysis = self.analyzer.analyze(
            self.student.get()
        )

        self.student.profile[
            "strengths"
        ] = analysis["strengths"]

        self.student.profile[
            "weaknesses"
        ] = analysis["weaknesses"]

        self.student.save()

        # =====================================
        # TEACHING STYLE
        # =====================================

        teaching_style = (
            self.teacher_brain.decide(
                self.knowledge_map.get(),
                subject
            )
        )

        # =====================================
        # BRAIN
        # =====================================

        brain_strategy = self.brain.think(
            self.student.get(),
            subject,
            original_message,
            self.knowledge_map.get()
        )

        # =====================================
        # DIFFICULTY
        # =====================================

        difficulty = (
            self.difficulty.decide(
                brain_strategy["confidence"]
            )
        )

        # =====================================
        # LONG-TERM MEMORY
        # =====================================

        memory_context = (
            "No relevant long-term memory."
        )

        if not self.demo:

            memory_context = (
                self.memory.build_context(

                    email=user_email,

                    query=original_message,

                    subject=subject,

                    limit=8
                )
            )

        # =====================================
        # SETTINGS
        # =====================================

        if self.demo:

            settings = {

                "name": "",

                "language":
                    "English",

                "level":
                    "High School",

                "teaching_style":
                    "adaptive",

                "difficulty":
                    "adaptive",

                "hints":
                    "when_needed",

                "step_by_step":
                    True,

                "adaptive_learning":
                    True,

                "response_length":
                    "balanced",

                "tone":
                    "friendly",

                "use_examples":
                    True,

                "use_analogies":
                    True,

                "encouragement":
                    True,

                "correction_style":
                    "explain",

                "show_correct_answer":
                    True,

                "creativity":
                    "medium",

                "behavior":
                    "",

                "custom_instructions":
                    ""
            }

        else:

            settings = (
                self.settings.get()
            )

        # =====================================
        # APPLY SETTINGS TO MESSAGE
        # =====================================

        student_name = settings.get(
            "name",
            ""
        )

        language = settings.get(
            "language",
            "English"
        )

        level = settings.get(
            "level",
            "High School"
        )

        personalization = settings.get(
            "behavior",
            ""
        )

        custom_instructions = settings.get(
            "custom_instructions",
            ""
        )

        if personalization or custom_instructions:

            message = f"""
Student profile:

Name:
{student_name}

Language:
{language}

Academic level:
{level}

Personal preferences:
{personalization}

Custom instructions:
{custom_instructions}

Student's original question:

{original_message}
"""

        else:

            message = original_message

        # =====================================
        # GENERATE
        # =====================================

        answer = self.tutor.answer(

            message,

            intent,

            subject,

            mode,

            memory_context,

            difficulty,

            settings=settings
        )

        # =====================================
        # VERIFY
        # =====================================

        answer = (
            self.answer_verifier.verify(
                original_message,
                answer
            )
        )

        # =====================================
        # FORMAT
        # =====================================

        answer = format_response(
            answer
        )

        # =====================================
        # DEBUG
        # =====================================

        print(
            "\n"
            "========== VERIFIED NOVA RESPONSE =========="
        )

        print(answer)

        print(
            "=============================================\n"
        )

        # =====================================
        # UNDERSTANDING
        # =====================================

        understanding = (
            self.understanding.analyze(
                subject,
                original_message,
                answer
            )
        )

        # =====================================
        # NORMALIZE MEMORY CONFIDENCE
        # =====================================

        memory_confidence = understanding.get(
            "confidence",
            50
        )

        if memory_confidence > 1:

            memory_confidence /= 100

        memory_confidence = max(
            0.0,
            min(
                1.0,
                float(memory_confidence)
            )
        )

        # =====================================
        # STORE LONG-TERM MEMORY
        # =====================================

        if not self.demo:

            self.memory.remember(

                email=user_email,

                user_message=
                    original_message,

                assistant_message=
                    answer,

                subject=
                    subject,

                confidence=
                    memory_confidence,

                conversation_id=
                    conversation_id
            )

        # =====================================
        # PROGRESS
        # =====================================

        self.progress.update(

            subject,

            original_message,

            understanding[
                "confidence"
            ]
        )

        # =====================================
        # LEARNING MEMORY
        # =====================================

        if subject and understanding:

            confidence = understanding.get(
                "confidence",
                50
            )

            self.learning_memory.record_attempt(

                subject,

                confidence
            )

        # =====================================
        # KNOWLEDGE MAP
        # =====================================

        if subject and understanding:

            self.knowledge_map.update(

                subject,

                original_message,

                understanding[
                    "confidence"
                ]
            )

            # =====================================
            # LEARNING MEMORY CONCEPT
            # =====================================

            self.learning_memory.update_concept(

                subject=subject,

                concept=original_message,

                confidence=
                    understanding.get(
                        "confidence",
                        50
                    ),

                difficulty=
                    difficulty.get(
                        "level"
                    )
                    if isinstance(
                        difficulty,
                        dict
                    )
                    else None
            )

        # =====================================
        # SAVE NOVA RESPONSE
        # =====================================

        self.conversations.add_message(

            user_email,

            conversation_id,

            "nova",

            answer
        )

        # =====================================
        # RETURN
        # =====================================

        return {

            "answer":
                answer,

            "conversation_id":
                conversation_id
        }
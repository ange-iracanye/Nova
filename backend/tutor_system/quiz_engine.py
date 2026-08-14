from __future__ import annotations

import random
import re
import uuid
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional


class QuizEngine:
    """
    Nova Quiz Engine.

    This class is responsible for creating, storing and grading
    educational quizzes.

    The engine is intentionally independent from the LLM.

    This means Nova can create reliable basic quizzes without
    depending on an AI-generated question being valid every time.

    Main responsibilities
    ---------------------

    - Create quizzes
    - Generate different question types
    - Adapt quiz difficulty
    - Adapt quiz length
    - Store active quizzes
    - Validate submitted answers
    - Grade answers
    - Calculate scores
    - Provide explanations
    - Track quiz statistics
    - Support multiple subjects
    - Support specific topics
    - Provide backward compatibility with:

        quiz.create_quiz("physics")

    The engine does NOT:

    - call the LLM
    - modify long-term student memory
    - determine the student's global learning level
    - decide the student's confidence

    Those responsibilities belong to Nova's other systems.
    """

    # ============================================================
    # CONSTANTS
    # ============================================================

    DEFAULT_SUBJECT = "general"

    DEFAULT_TOPIC = "general concepts"

    DEFAULT_DIFFICULTY = "medium"

    DEFAULT_QUESTION_COUNT = 5

    MIN_QUESTION_COUNT = 1

    MAX_QUESTION_COUNT = 20

    VALID_DIFFICULTIES = {
        "easy",
        "medium",
        "hard",
        "adaptive"
    }

    VALID_TYPES = {
        "multiple_choice",
        "true_false",
        "short_answer"
    }

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        seed: Optional[int] = None
    ):
        """
        Initialize the quiz engine.

        Parameters
        ----------
        seed:
            Optional random seed.

            Useful for testing because the same seed produces
            reproducible question ordering.
        """

        self.random = random.Random(seed)

        # Active quizzes currently known to Nova.
        #
        # {
        #     quiz_id: quiz_data
        # }
        self.active_quizzes: Dict[str, Dict[str, Any]] = {}

        # Completed quiz attempts.
        #
        # This is intentionally kept in memory for now.
        # A future persistence system can store it on disk.
        self.history: List[Dict[str, Any]] = []

        # Built-in question banks.
        self.question_banks = self._build_question_banks()

    # ============================================================
    # PUBLIC API
    # ============================================================

    def create_quiz(
        self,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: str = DEFAULT_DIFFICULTY,
        question_count: int = DEFAULT_QUESTION_COUNT,
        question_types: Optional[List[str]] = None,
        seed: Optional[int] = None
    ) -> str:
        """
        Backward-compatible quiz creation method.

        The old Nova code expects:

            quiz.create_quiz("physics")

        Therefore this method still returns a human-readable
        quiz string.

        For applications that need structured quiz data,
        use:

            create_quiz_data()

        Parameters
        ----------
        subject:
            Academic subject.

        topic:
            More specific topic.

        difficulty:
            easy / medium / hard / adaptive

        question_count:
            Number of questions.

        question_types:
            Optional list such as:

                [
                    "multiple_choice",
                    "true_false",
                    "short_answer"
                ]

        seed:
            Optional random seed for deterministic generation.

        Returns
        -------
        str
            Human-readable quiz.
        """

        quiz = self.create_quiz_data(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            question_count=question_count,
            question_types=question_types,
            seed=seed
        )

        return self.format_quiz(
            quiz
        )

    # ============================================================

    def create_quiz_data(
        self,
        subject: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty: str = DEFAULT_DIFFICULTY,
        question_count: int = DEFAULT_QUESTION_COUNT,
        question_types: Optional[List[str]] = None,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a structured quiz.

        This is the preferred API for Nova's internal systems.

        Example result:

            {
                "quiz_id": "...",
                "subject": "physics",
                "topic": "newton",
                "difficulty": "medium",
                "questions": [...]
            }
        """

        subject = self._normalize_subject(
            subject
        )

        topic = self._normalize_topic(
            topic
        )

        difficulty = self._normalize_difficulty(
            difficulty
        )

        question_count = self._normalize_question_count(
            question_count
        )

        question_types = self._normalize_question_types(
            question_types
        )

        generator = (
            random.Random(seed)
            if seed is not None
            else self.random
        )

        questions = self._generate_questions(
            subject=subject,
            topic=topic,
            difficulty=difficulty,
            question_count=question_count,
            question_types=question_types,
            generator=generator
        )

        quiz_id = self._generate_quiz_id()

        quiz = {
            "quiz_id": quiz_id,

            "subject": subject,

            "topic": topic,

            "difficulty": difficulty,

            "question_count": len(
                questions
            ),

            "created_at":
                self._timestamp(),

            "completed": False,

            "score": None,

            "questions": questions
        }

        self.active_quizzes[
            quiz_id
        ] = quiz

        return deepcopy(
            quiz
        )

    # ============================================================

    def get_quiz(
        self,
        quiz_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an active quiz.
        """

        if not quiz_id:
            return None

        quiz = self.active_quizzes.get(
            quiz_id
        )

        if quiz is None:
            return None

        return deepcopy(
            quiz
        )

    # ============================================================

    def submit_answers(
        self,
        quiz_id: str,
        answers: Any
    ) -> Dict[str, Any]:
        """
        Grade a completed quiz.

        Parameters
        ----------
        quiz_id:
            ID returned by create_quiz_data().

        answers:
            Can be:

                {
                    "q1": "A",
                    "q2": "true"
                }

            or:

                [
                    "A",
                    "true",
                    "gravity"
                ]

        Returns
        -------
        dict
            Detailed grading result.
        """

        quiz = self.active_quizzes.get(
            quiz_id
        )

        if quiz is None:

            return {
                "success": False,
                "error": "Quiz not found.",
                "score": 0,
                "percentage": 0
            }

        normalized_answers = (
            self._normalize_answers(
                answers,
                quiz
            )
        )

        results = []

        correct_count = 0

        total_questions = len(
            quiz.get(
                "questions",
                []
            )
        )

        for index, question in enumerate(
            quiz.get(
                "questions",
                []
            )
        ):

            question_id = question.get(
                "id"
            )

            user_answer = (
                normalized_answers.get(
                    question_id
                )
            )

            result = self._grade_question(
                question,
                user_answer
            )

            if result["correct"]:
                correct_count += 1

            results.append(
                result
            )

        percentage = self._calculate_percentage(
            correct_count,
            total_questions
        )

        score = self._build_score(
            correct_count,
            total_questions,
            percentage
        )

        quiz["completed"] = True

        quiz["completed_at"] = (
            self._timestamp()
        )

        quiz["score"] = score

        quiz["results"] = results

        self.history.append(
            deepcopy(
                quiz
            )
        )

        return {
            "success": True,

            "quiz_id":
                quiz_id,

            "subject":
                quiz.get(
                    "subject"
                ),

            "topic":
                quiz.get(
                    "topic"
                ),

            "difficulty":
                quiz.get(
                    "difficulty"
                ),

            "score":
                score,

            "percentage":
                percentage,

            "correct":
                correct_count,

            "total":
                total_questions,

            "results":
                results,

            "message":
                self._build_score_message(
                    percentage
                )
        }

    # ============================================================

    def grade_answer(
        self,
        question: Dict[str, Any],
        answer: Any
    ) -> Dict[str, Any]:
        """
        Grade one question independently.

        Useful when Nova wants to correct an answer
        immediately instead of waiting for the complete quiz.
        """

        if not isinstance(
            question,
            dict
        ):

            return {
                "correct": False,
                "error": "Invalid question."
            }

        return self._grade_question(
            question,
            answer
        )

    # ============================================================

    def format_quiz(
        self,
        quiz: Dict[str, Any],
        show_answers: bool = False
    ) -> str:
        """
        Convert structured quiz data into readable text.

        Answers are hidden by default.
        """

        if not isinstance(
            quiz,
            dict
        ):

            return (
                "Unable to format quiz."
            )

        subject = quiz.get(
            "subject",
            "General"
        )

        topic = quiz.get(
            "topic",
            "General concepts"
        )

        difficulty = quiz.get(
            "difficulty",
            "medium"
        )

        questions = quiz.get(
            "questions",
            []
        )

        lines = []

        lines.append(
            f"{subject.title()} Quiz"
        )

        lines.append(
            f"Topic: {topic}"
        )

        lines.append(
            f"Difficulty: {difficulty}"
        )

        lines.append(
            f"Questions: {len(questions)}"
        )

        lines.append("")

        lines.append(
            "Answer the questions and Nova will correct your answers."
        )

        lines.append("")

        for number, question in enumerate(
            questions,
            start=1
        ):

            lines.append(
                f"Question {number}"
            )

            lines.append(
                question.get(
                    "question",
                    "Question unavailable."
                )
            )

            question_type = question.get(
                "type"
            )

            if question_type == "multiple_choice":

                options = question.get(
                    "options",
                    {}
                )

                for key, value in options.items():

                    lines.append(
                        f"{key}. {value}"
                    )

            elif question_type == "true_false":

                lines.append(
                    "A. True"
                )

                lines.append(
                    "B. False"
                )

            if show_answers:

                lines.append(
                    "Correct answer: "
                    + str(
                        question.get(
                            "answer",
                            ""
                        )
                    )
                )

            lines.append("")

        return "\n".join(
            lines
        ).strip()

    # ============================================================

    def get_statistics(self) -> Dict[str, Any]:
        """
        Return global quiz statistics for this engine instance.
        """

        total_attempts = len(
            self.history
        )

        if total_attempts == 0:

            return {
                "total_quizzes": 0,
                "average_percentage": 0,
                "best_percentage": 0,
                "worst_percentage": 0,
                "total_questions": 0,
                "correct_answers": 0
            }

        percentages = []

        total_questions = 0

        correct_answers = 0

        for attempt in self.history:

            score = attempt.get(
                "score",
                {}
            )

            percentage = score.get(
                "percentage",
                0
            )

            percentages.append(
                percentage
            )

            total_questions += (
                score.get(
                    "total",
                    0
                )
            )

            correct_answers += (
                score.get(
                    "correct",
                    0
                )
            )

        return {
            "total_quizzes":
                total_attempts,

            "average_percentage":
                round(
                    sum(percentages)
                    / len(percentages),
                    2
                ),

            "best_percentage":
                max(percentages),

            "worst_percentage":
                min(percentages),

            "total_questions":
                total_questions,

            "correct_answers":
                correct_answers
        }

    # ============================================================

    def get_subject_statistics(
        self,
        subject: str
    ) -> Dict[str, Any]:
        """
        Return statistics for one subject.
        """

        subject = self._normalize_subject(
            subject
        )

        attempts = [

            attempt

            for attempt in self.history

            if attempt.get(
                "subject"
            ) == subject
        ]

        if not attempts:

            return {
                "subject": subject,
                "attempts": 0,
                "average_percentage": 0,
                "best_percentage": 0
            }

        percentages = [

            attempt.get(
                "score",
                {}
            ).get(
                "percentage",
                0
            )

            for attempt in attempts
        ]

        return {
            "subject":
                subject,

            "attempts":
                len(attempts),

            "average_percentage":
                round(
                    sum(percentages)
                    / len(percentages),
                    2
                ),

            "best_percentage":
                max(percentages)
        }

    # ============================================================

    def clear_completed_quizzes(
        self
    ) -> None:
        """
        Remove completed quizzes from active memory.
        """

        completed_ids = [

            quiz_id

            for quiz_id, quiz in
            self.active_quizzes.items()

            if quiz.get(
                "completed",
                False
            )
        ]

        for quiz_id in completed_ids:

            del self.active_quizzes[
                quiz_id
            ]

    # ============================================================
    # QUESTION GENERATION
    # ============================================================

    def _generate_questions(
        self,
        subject: str,
        topic: str,
        difficulty: str,
        question_count: int,
        question_types: List[str],
        generator: random.Random
    ) -> List[Dict[str, Any]]:
        """
        Generate questions from the internal question bank.

        The system first searches for topic-specific questions,
        then subject-level questions, then general questions.

        This makes the engine useful even when a specific topic
        is not available.
        """

        candidates = self._get_candidates(
            subject,
            topic,
            difficulty
        )

        if not candidates:

            candidates = (
                self._get_general_candidates(
                    difficulty
                )
            )

        if not candidates:

            candidates = (
                self._fallback_questions(
                    subject,
                    topic,
                    difficulty
                )
            )

        generator.shuffle(
            candidates
        )

        selected = []

        # --------------------------------------------------------
        # First pass:
        # respect requested question types
        # --------------------------------------------------------

        typed_candidates = [

            candidate

            for candidate in candidates

            if candidate.get(
                "type"
            ) in question_types
        ]

        generator.shuffle(
            typed_candidates
        )

        for candidate in typed_candidates:

            if len(selected) >= question_count:

                break

            selected.append(
                deepcopy(
                    candidate
                )
            )

        # --------------------------------------------------------
        # Second pass:
        # fill remaining slots with any suitable question
        # --------------------------------------------------------

        if len(selected) < question_count:

            for candidate in candidates:

                if len(selected) >= question_count:

                    break

                if candidate in selected:

                    continue

                selected.append(
                    deepcopy(
                        candidate
                    )
                )

        # --------------------------------------------------------
        # If the bank is too small, generate fallback questions
        # --------------------------------------------------------

        while len(selected) < question_count:

            fallback = (
                self._fallback_questions(
                    subject,
                    topic,
                    difficulty
                )
            )

            if not fallback:

                break

            candidate = generator.choice(
                fallback
            )

            candidate = deepcopy(
                candidate
            )

            # Avoid duplicate IDs.
            candidate["id"] = (
                self._generate_question_id()
            )

            selected.append(
                candidate
            )

        # --------------------------------------------------------
        # Finalize question IDs
        # --------------------------------------------------------

        finalized = []

        for question in selected:

            question["id"] = (
                self._generate_question_id()
            )

            question["subject"] = subject

            question["topic"] = topic

            question["difficulty"] = difficulty

            finalized.append(
                question
            )

        return finalized

    # ============================================================

    def _get_candidates(
        self,
        subject: str,
        topic: str,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve suitable questions.
        """

        bank = self.question_banks.get(
            subject,
            {}
        )

        candidates = []

        # --------------------------------------------------------
        # Exact topic
        # --------------------------------------------------------

        topic_questions = bank.get(
            topic,
            []
        )

        candidates.extend(
            topic_questions
        )

        # --------------------------------------------------------
        # Subject-wide questions
        # --------------------------------------------------------

        for topic_name, questions in bank.items():

            if topic_name == topic:

                continue

            candidates.extend(
                questions
            )

        # --------------------------------------------------------
        # Difficulty filter
        # --------------------------------------------------------

        if difficulty == "adaptive":

            return candidates

        filtered = [

            question

            for question in candidates

            if question.get(
                "difficulty"
            ) == difficulty
        ]

        # If the requested difficulty does not have
        # enough questions, use the subject bank instead.
        if filtered:

            return filtered

        return candidates

    # ============================================================

    def _get_general_candidates(
        self,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve questions from all subjects.
        """

        candidates = []

        for subject_bank in (
            self.question_banks.values()
        ):

            for questions in subject_bank.values():

                for question in questions:

                    if (
                        difficulty == "adaptive"
                        or question.get(
                            "difficulty"
                        ) == difficulty
                    ):

                        candidates.append(
                            question
                        )

        return candidates

    # ============================================================
    # QUESTION BANK
    # ============================================================

    def _build_question_banks(
        self
    ) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """
        Build Nova's built-in educational question bank.

        The bank is intentionally modest for now.

        Later, it can be moved into JSON files or a database
        without changing the public QuizEngine API.
        """

        return {

            # ====================================================
            # PHYSICS
            # ====================================================

            "physics": {

                "gravity": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "easy",

                        "question":
                            "What force pulls objects toward Earth?",

                        "options": {
                            "A": "Gravity",
                            "B": "Magnetism",
                            "C": "Friction",
                            "D": "Electricity"
                        },

                        "answer":
                            "A",

                        "explanation":
                            "Gravity is the force that attracts objects toward Earth."
                    },

                    {
                        "type":
                            "true_false",

                        "difficulty":
                            "easy",

                        "question":
                            "Gravity acts on objects that have mass.",

                        "answer":
                            "A",

                        "explanation":
                            "Objects with mass experience gravitational attraction."
                    },

                    {
                        "type":
                            "short_answer",

                        "difficulty":
                            "medium",

                        "question":
                            "In simple terms, what is gravity?",

                        "answer":
                            "a force that attracts masses toward each other",

                        "accepted_answers": [
                            "a force that attracts masses",
                            "force that attracts masses",
                            "force pulling objects together",
                            "attraction between masses"
                        ],

                        "explanation":
                            "Gravity is an attractive force between objects with mass."
                    }
                ],

                "motion": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "easy",

                        "question":
                            "Which quantity describes how fast an object moves?",

                        "options": {
                            "A": "Mass",
                            "B": "Speed",
                            "C": "Temperature",
                            "D": "Density"
                        },

                        "answer":
                            "B",

                        "explanation":
                            "Speed describes how quickly an object changes position."
                    },

                    {
                        "type":
                            "true_false",

                        "difficulty":
                            "medium",

                        "question":
                            "Acceleration describes a change in velocity.",

                        "answer":
                            "A",

                        "explanation":
                            "Acceleration is the rate at which velocity changes."
                    }
                ],

                "newton": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "medium",

                        "question":
                            "According to Newton's second law, which equation relates force, mass and acceleration?",

                        "options": {
                            "A": "F = ma",
                            "B": "F = m/a",
                            "C": "F = a/m",
                            "D": "F = m + a"
                        },

                        "answer":
                            "A",

                        "explanation":
                            "Newton's second law is commonly written as F = ma."
                    },

                    {
                        "type":
                            "short_answer",

                        "difficulty":
                            "medium",

                        "question":
                            "What happens to the acceleration of an object if the net force increases while its mass stays constant?",

                        "answer":
                            "the acceleration increases",

                        "accepted_answers": [
                            "acceleration increases",
                            "it increases",
                            "the acceleration becomes greater"
                        ],

                        "explanation":
                            "From F = ma, with constant mass, increasing net force increases acceleration."
                    }
                ]
            },

            # ====================================================
            # BIOLOGY
            # ====================================================

            "biology": {

                "cell": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "easy",

                        "question":
                            "What is the basic structural unit of living organisms?",

                        "options": {
                            "A": "Cell",
                            "B": "Atom",
                            "C": "Organ",
                            "D": "Tissue"
                        },

                        "answer":
                            "A",

                        "explanation":
                            "The cell is the basic structural and functional unit of life."
                    },

                    {
                        "type":
                            "true_false",

                        "difficulty":
                            "easy",

                        "question":
                            "All cells contain genetic material.",

                        "answer":
                            "A",

                        "explanation":
                            "Cells contain genetic information, although it is organized differently in different organisms."
                    }
                ],

                "dna": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "easy",

                        "question":
                            "What molecule stores genetic information in most living organisms?",

                        "options": {
                            "A": "DNA",
                            "B": "Water",
                            "C": "Glucose",
                            "D": "Oxygen"
                        },

                        "answer":
                            "A",

                        "explanation":
                            "DNA stores hereditary genetic information in most living organisms."
                    },

                    {
                        "type":
                            "short_answer",

                        "difficulty":
                            "medium",

                        "question":
                            "What is one major role of DNA?",

                        "answer":
                            "to store genetic information",

                        "accepted_answers": [
                            "store genetic information",
                            "stores genetic information",
                            "carry genetic information",
                            "contains genetic information"
                        ],

                        "explanation":
                            "DNA stores the genetic instructions used by organisms."
                    }
                ],

                "photosynthesis": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "medium",

                        "question":
                            "What is the main purpose of photosynthesis?",

                        "options": {
                            "A": "To convert light energy into chemical energy",
                            "B": "To destroy oxygen",
                            "C": "To produce soil",
                            "D": "To remove all water from plants"
                        },

                        "answer":
                            "A",

                        "explanation":
                            "Photosynthesis converts light energy into chemical energy stored in organic molecules."
                    }
                ]
            },

            # ====================================================
            # CHEMISTRY
            # ====================================================

            "chemistry": {

                "atom": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "easy",

                        "question":
                            "What is the basic unit of an element?",

                        "options": {
                            "A": "Atom",
                            "B": "Cell",
                            "C": "Organ",
                            "D": "Tissue"
                        },

                        "answer":
                            "A",

                        "explanation":
                            "An atom is the smallest unit of an element that retains the element's chemical identity."
                    },

                    {
                        "type":
                            "true_false",

                        "difficulty":
                            "easy",

                        "question":
                            "Protons have a positive electric charge.",

                        "answer":
                            "A",

                        "explanation":
                            "Protons carry positive electric charge."
                    }
                ],

                "molecule": [

                    {
                        "type":
                            "short_answer",

                        "difficulty":
                            "easy",

                        "question":
                            "What is a molecule?",

                        "answer":
                            "two or more atoms chemically bonded together",

                        "accepted_answers": [
                            "two or more atoms bonded together",
                            "atoms chemically bonded together",
                            "two or more atoms chemically bonded"
                        ],

                        "explanation":
                            "A molecule consists of atoms held together by chemical bonds."
                    }
                ]
            },

            # ====================================================
            # MATHEMATICS
            # ====================================================

            "math": {

                "equation": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "easy",

                        "question":
                            "If x + 5 = 12, what is x?",

                        "options": {
                            "A": "5",
                            "B": "7",
                            "C": "12",
                            "D": "17"
                        },

                        "answer":
                            "B",

                        "explanation":
                            "Subtract 5 from both sides: x = 12 - 5 = 7."
                    },

                    {
                        "type":
                            "short_answer",

                        "difficulty":
                            "medium",

                        "question":
                            "Solve: 3x = 18.",

                        "answer":
                            "6",

                        "accepted_answers": [
                            "6",
                            "x = 6"
                        ],

                        "explanation":
                            "Divide both sides by 3, giving x = 6."
                    }
                ],

                "percentage": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "easy",

                        "question":
                            "What is 10% of 100?",

                        "options": {
                            "A": "1",
                            "B": "5",
                            "C": "10",
                            "D": "20"
                        },

                        "answer":
                            "C",

                        "explanation":
                            "10% means 10 out of 100, so 10% of 100 is 10."
                    }
                ],

                "triangle": [

                    {
                        "type":
                            "true_false",

                        "difficulty":
                            "easy",

                        "question":
                            "A triangle has three sides.",

                        "answer":
                            "A",

                        "explanation":
                            "A triangle is a polygon with three sides."
                    }
                ]
            },

            # ====================================================
            # HISTORY
            # ====================================================

            "history": {

                "revolution": [

                    {
                        "type":
                            "short_answer",

                        "difficulty":
                            "medium",

                        "question":
                            "In history, what is a revolution?",

                        "answer":
                            "a major and often rapid change in political or social systems",

                        "accepted_answers": [
                            "major political change",
                            "major social change",
                            "major change in political or social systems",
                            "rapid political change"
                        ],

                        "explanation":
                            "A revolution is a major transformation, often rapid, in a society's political or social structure."
                    }
                ],

                "empire": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "easy",

                        "question":
                            "What is an empire?",

                        "options": {
                            "A": "A state controlling multiple territories or peoples",
                            "B": "A single village",
                            "C": "A type of machine",
                            "D": "A natural phenomenon"
                        },

                        "answer":
                            "A",

                        "explanation":
                            "An empire is a political system in which a state or ruler controls multiple territories or peoples."
                    }
                ]
            },

            # ====================================================
            # GEOGRAPHY
            # ====================================================

            "geography": {

                "continent": [

                    {
                        "type":
                            "multiple_choice",

                        "difficulty":
                            "easy",

                        "question":
                            "Which of these is a continent?",

                        "options": {
                            "A": "Africa",
                            "B": "France",
                            "C": "Paris",
                            "D": "Amazon River"
                        },

                        "answer":
                            "A",

                        "explanation":
                            "Africa is one of Earth's continents."
                    }
                ],

                "climate": [

                    {
                        "type":
                            "true_false",

                        "difficulty":
                            "easy",

                        "question":
                            "Climate describes long-term patterns of weather in a region.",

                        "answer":
                            "A",

                        "explanation":
                            "Climate refers to long-term patterns and averages of atmospheric conditions."
                    }
                ]
            }
        }

    # ============================================================
    # FALLBACK QUESTIONS
    # ============================================================

    def _fallback_questions(
        self,
        subject: str,
        topic: str,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """
        Generate generic but structurally valid questions
        when the built-in bank does not contain the requested
        subject/topic.
        """

        return [

            {
                "type":
                    "short_answer",

                "difficulty":
                    difficulty
                    if difficulty != "adaptive"
                    else "medium",

                "question":
                    f"What is one important concept related to {topic} in {subject}?",

                "answer":
                    "",

                "accepted_answers":
                    [],

                "explanation":
                    "This is an open-ended question. Nova should evaluate the student's explanation based on relevance and accuracy."
            },

            {
                "type":
                    "short_answer",

                "difficulty":
                    difficulty
                    if difficulty != "adaptive"
                    else "medium",

                "question":
                    f"Give one real-life example related to {topic} in {subject}.",

                "answer":
                    "",

                "accepted_answers":
                    [],

                "explanation":
                    "A valid answer should give a relevant and reasonably accurate real-world example."
            },

            {
                "type":
                    "short_answer",

                "difficulty":
                    difficulty
                    if difficulty != "adaptive"
                    else "medium",

                "question":
                    f"Why is understanding {topic} useful when studying {subject}?",

                "answer":
                    "",

                "accepted_answers":
                    [],

                "explanation":
                    "The answer should connect the topic to a useful idea, application, or broader concept."
            }
        ]

    # ============================================================
    # GRADING
    # ============================================================

    def _grade_question(
        self,
        question: Dict[str, Any],
        user_answer: Any
    ) -> Dict[str, Any]:
        """
        Grade a single question.
        """

        question_type = question.get(
            "type",
            "short_answer"
        )

        normalized_user = (
            self._normalize_answer(
                user_answer
            )
        )

        correct_answer = question.get(
            "answer",
            ""
        )

        # --------------------------------------------------------
        # Multiple choice
        # --------------------------------------------------------

        if question_type == "multiple_choice":

            correct = (
                normalized_user.upper()
                == str(
                    correct_answer
                ).strip().upper()
            )

        # --------------------------------------------------------
        # True / false
        # --------------------------------------------------------

        elif question_type == "true_false":

            correct = (
                self._normalize_true_false(
                    user_answer
                )
                ==
                self._normalize_true_false(
                    correct_answer
                )
            )

        # --------------------------------------------------------
        # Short answer
        # --------------------------------------------------------

        else:

            correct = (
                self._match_short_answer(
                    question,
                    normalized_user
                )
            )

        return {
            "question_id":
                question.get(
                    "id"
                ),

            "question":
                question.get(
                    "question",
                    ""
                ),

            "user_answer":
                user_answer,

            "correct_answer":
                correct_answer,

            "correct":
                correct,

            "explanation":
                question.get(
                    "explanation",
                    ""
                )
        }

    # ============================================================

    def _match_short_answer(
        self,
        question: Dict[str, Any],
        user_answer: str
    ) -> bool:
        """
        Match short answers using normalized exact matching.

        This deliberately does not use fuzzy matching for now.

        Fuzzy matching can accidentally mark incorrect answers
        as correct, which is especially bad in an educational
        system.

        A future semantic evaluator can be added here.
        """

        if not user_answer:

            return False

        accepted = question.get(
            "accepted_answers",
            []
        )

        correct_answer = (
            question.get(
                "answer",
                ""
            )
        )

        accepted_values = []

        if correct_answer:

            accepted_values.append(
                correct_answer
            )

        if isinstance(
            accepted,
            list
        ):

            accepted_values.extend(
                accepted
            )

        normalized_options = [

            self._normalize_answer(
                value
            )

            for value in accepted_values

            if value is not None
        ]

        return (
            user_answer
            in normalized_options
        )

    # ============================================================
    # ANSWER NORMALIZATION
    # ============================================================

    def _normalize_answers(
        self,
        answers: Any,
        quiz: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Normalize different answer formats into:

            {
                question_id: answer
            }
        """

        questions = quiz.get(
            "questions",
            []
        )

        if isinstance(
            answers,
            dict
        ):

            # Direct question IDs
            direct = {}

            for question in questions:

                question_id = question.get(
                    "id"
                )

                if question_id in answers:

                    direct[
                        question_id
                    ] = answers[
                        question_id
                    ]

            if direct:

                return direct

            # Support q1, q2, q3 style answers
            indexed = {}

            for index, question in enumerate(
                questions,
                start=1
            ):

                question_id = question.get(
                    "id"
                )

                keys = [
                    f"q{index}",
                    str(index)
                ]

                for key in keys:

                    if key in answers:

                        indexed[
                            question_id
                        ] = answers[
                            key
                        ]

                        break

            return indexed

        if isinstance(
            answers,
            (list, tuple)
        ):

            result = {}

            for index, answer in enumerate(
                answers
            ):

                if index >= len(
                    questions
                ):

                    break

                question_id = questions[
                    index
                ].get(
                    "id"
                )

                result[
                    question_id
                ] = answer

            return result

        # A single answer is interpreted as the answer
        # to the first question.
        if questions:

            return {
                questions[0].get(
                    "id"
                ):
                    answers
            }

        return {}

    # ============================================================

    def _normalize_answer(
        self,
        answer: Any
    ) -> str:
        """
        Normalize answer text for reliable comparison.
        """

        if answer is None:

            return ""

        answer = str(
            answer
        ).strip().lower()

        answer = re.sub(
            r"\s+",
            " ",
            answer
        )

        answer = answer.rstrip(
            ".!?"
        )

        return answer.strip()

    # ============================================================

    def _normalize_true_false(
        self,
        answer: Any
    ) -> str:
        """
        Convert common true/false representations into
        a consistent value.
        """

        value = self._normalize_answer(
            answer
        )

        if value in {
            "a",
            "true",
            "t",
            "yes",
            "vrai"
        }:

            return "true"

        if value in {
            "b",
            "false",
            "f",
            "no",
            "faux"
        }:

            return "false"

        return value

    # ============================================================
    # NORMALIZATION HELPERS
    # ============================================================

    def _normalize_subject(
        self,
        subject: Optional[str]
    ) -> str:
        """
        Normalize subject names.
        """

        if not subject:

            return self.DEFAULT_SUBJECT

        subject = str(
            subject
        ).strip().lower()

        aliases = {

            "physics":
                "physics",

            "physique":
                "physics",

            "biology":
                "biology",

            "biologie":
                "biology",

            "chemistry":
                "chemistry",

            "chimie":
                "chemistry",

            "math":
                "math",

            "mathematics":
                "math",

            "maths":
                "math",

            "mathematics":
                "math",

            "history":
                "history",

            "histoire":
                "history",

            "geography":
                "geography",

            "géographie":
                "geography"
        }

        return aliases.get(
            subject,
            subject
        )

    # ============================================================

    def _normalize_topic(
        self,
        topic: Optional[str]
    ) -> str:
        """
        Normalize topic names.
        """

        if not topic:

            return self.DEFAULT_TOPIC

        topic = str(
            topic
        ).strip().lower()

        # Common aliases.
        aliases = {

            "newton's second law":
                "newton",

            "newtons second law":
                "newton",

            "newton second law":
                "newton",

            "gravity":
                "gravity",

            "gravitation":
                "gravity",

            "cells":
                "cell",

            "cellular biology":
                "cell",

            "photosynthesis":
                "photosynthesis",

            "atoms":
                "atom",

            "molecules":
                "molecule",

            "equations":
                "equation",

            "percentages":
                "percentage",

            "triangles":
                "triangle"
        }

        return aliases.get(
            topic,
            topic
        )

    # ============================================================

    def _normalize_difficulty(
        self,
        difficulty: Optional[str]
    ) -> str:
        """
        Normalize difficulty.
        """

        if not difficulty:

            return self.DEFAULT_DIFFICULTY

        difficulty = str(
            difficulty
        ).strip().lower()

        aliases = {

            "beginner":
                "easy",

            "basic":
                "easy",

            "easy":
                "easy",

            "normal":
                "medium",

            "intermediate":
                "medium",

            "medium":
                "medium",

            "advanced":
                "hard",

            "hard":
                "hard",

            "adaptive":
                "adaptive"
        }

        difficulty = aliases.get(
            difficulty,
            self.DEFAULT_DIFFICULTY
        )

        if difficulty not in self.VALID_DIFFICULTIES:

            return self.DEFAULT_DIFFICULTY

        return difficulty

    # ============================================================

    def _normalize_question_count(
        self,
        question_count: Any
    ) -> int:
        """
        Normalize question count and prevent absurd values.
        """

        try:

            question_count = int(
                question_count
            )

        except (
            TypeError,
            ValueError
        ):

            question_count = (
                self.DEFAULT_QUESTION_COUNT
            )

        return max(
            self.MIN_QUESTION_COUNT,
            min(
                question_count,
                self.MAX_QUESTION_COUNT
            )
        )

    # ============================================================

    def _normalize_question_types(
        self,
        question_types: Optional[List[str]]
    ) -> List[str]:
        """
        Normalize requested question types.
        """

        if not question_types:

            return [
                "multiple_choice",
                "true_false",
                "short_answer"
            ]

        if isinstance(
            question_types,
            str
        ):

            question_types = [
                question_types
            ]

        result = []

        for question_type in question_types:

            if not isinstance(
                question_type,
                str
            ):

                continue

            question_type = (
                question_type
                .strip()
                .lower()
            )

            if question_type in self.VALID_TYPES:

                if question_type not in result:

                    result.append(
                        question_type
                    )

        if not result:

            return [
                "multiple_choice",
                "true_false",
                "short_answer"
            ]

        return result

    # ============================================================
    # SCORE
    # ============================================================

    def _calculate_percentage(
        self,
        correct: int,
        total: int
    ) -> float:
        """
        Calculate percentage safely.
        """

        if total <= 0:

            return 0.0

        return round(
            (
                correct
                / total
            ) * 100,
            2
        )

    # ============================================================

    def _build_score(
        self,
        correct: int,
        total: int,
        percentage: float
    ) -> Dict[str, Any]:
        """
        Build structured score information.
        """

        return {

            "correct":
                correct,

            "incorrect":
                max(
                    total - correct,
                    0
                ),

            "total":
                total,

            "percentage":
                percentage,

            "grade":
                self._percentage_to_grade(
                    percentage
                )
        }

    # ============================================================

    def _percentage_to_grade(
        self,
        percentage: float
    ) -> str:
        """
        Convert percentage into a simple learning grade.
        """

        if percentage >= 90:

            return "excellent"

        if percentage >= 80:

            return "very_good"

        if percentage >= 70:

            return "good"

        if percentage >= 60:

            return "developing"

        if percentage >= 50:

            return "needs_practice"

        return "needs_review"

    # ============================================================

    def _build_score_message(
        self,
        percentage: float
    ) -> str:
        """
        Create a human-readable result message.
        """

        if percentage >= 90:

            return (
                "Excellent result. The student demonstrates strong understanding."
            )

        if percentage >= 75:

            return (
                "Good result. The student appears to understand most of the material."
            )

        if percentage >= 60:

            return (
                "The student is making progress but still has some areas to reinforce."
            )

        if percentage >= 40:

            return (
                "The student should review the main concepts and practice again."
            )

        return (
            "The student would benefit from reviewing the fundamentals before attempting a harder quiz."
        )

    # ============================================================
    # IDs AND TIME
    # ============================================================

    def _generate_quiz_id(
        self
    ) -> str:
        """
        Generate a unique quiz ID.
        """

        return (
            "quiz_"
            + uuid.uuid4().hex
        )

    # ============================================================

    def _generate_question_id(
        self
    ) -> str:
        """
        Generate a unique question ID.
        """

        return (
            "question_"
            + uuid.uuid4().hex
        )

    # ============================================================

    def _timestamp(
        self
    ) -> str:
        """
        Return an ISO timestamp.
        """

        return datetime.now().isoformat(
            timespec="seconds"
        )
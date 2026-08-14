from fastapi import APIRouter, HTTPException

from backend.learning_graph import LearningGraph
from backend.learning.progress_tracker import ProgressTracker
from backend.learning.understanding import (
    UnderstandingTracker,
    UnderstandingAnalyzer
)
from backend.student.knowledge_map import KnowledgeMap


router = APIRouter()


# ============================================================
# DASHBOARD
# ============================================================

@router.get("/dashboard/{email}")
def get_dashboard(email: str):

    email = email.strip().lower()

    if not email:
        raise HTTPException(
            status_code=400,
            detail="A valid email is required."
        )


    # ========================================================
    # LOAD NOVA LEARNING SYSTEMS
    # ========================================================

    learning_graph = LearningGraph()

    progress_tracker = ProgressTracker()

    understanding_tracker = UnderstandingTracker()

    understanding_analyzer = UnderstandingAnalyzer()

    knowledge_map = KnowledgeMap()


    # ========================================================
    # LEARNING GRAPH
    # ========================================================

    graph = learning_graph.get()

    subjects_data = graph.get(
        "subjects",
        {}
    )


    subjects = []

    total_attempts = 0

    total_correct = 0

    total_wrong = 0

    total_topics = 0


    for subject_name, subject_data in subjects_data.items():

        topics = []

        subject_attempts = 0

        subject_correct = 0

        subject_wrong = 0


        for topic_name, topic_data in subject_data.get(
            "topics",
            {}
        ).items():

            times_studied = topic_data.get(
                "times_studied",
                0
            )

            correct_answers = topic_data.get(
                "correct_answers",
                0
            )

            wrong_answers = topic_data.get(
                "wrong_answers",
                0
            )

            mastery = topic_data.get(
                "mastery",
                0
            )


            topics.append({
                "name": topic_name,

                "mastery": mastery,

                "attempts": times_studied,

                "correct_answers":
                    correct_answers,

                "wrong_answers":
                    wrong_answers,

                "last_review":
                    topic_data.get(
                        "last_review",
                        ""
                    )
            })


            subject_attempts += (
                times_studied
            )

            subject_correct += (
                correct_answers
            )

            subject_wrong += (
                wrong_answers
            )


            total_topics += 1


        # ----------------------------------------------------
        # Subject mastery
        # ----------------------------------------------------

        total_answers = (
            subject_correct
            + subject_wrong
        )


        if total_answers > 0:

            subject_mastery = round(
                subject_correct
                / total_answers
                * 100,
                1
            )

        else:

            subject_mastery = (
                subject_data.get(
                    "mastery",
                    0
                )
            )


        subjects.append({

            "name":
                subject_name,

            "mastery":
                subject_mastery,

            "attempts":
                subject_attempts,

            "correct_answers":
                subject_correct,

            "wrong_answers":
                subject_wrong,

            "topics":
                topics

        })


        total_attempts += (
            subject_attempts
        )

        total_correct += (
            subject_correct
        )

        total_wrong += (
            subject_wrong
        )


    # ========================================================
    # OVERALL MASTERY
    # ========================================================

    total_answers = (
        total_correct
        + total_wrong
    )


    if total_answers > 0:

        overall_mastery = round(
            total_correct
            / total_answers
            * 100,
            1
        )

    else:

        overall_mastery = 0


    # ========================================================
    # PROGRESS TRACKER
    # ========================================================

    progress = (
        progress_tracker.get()
    )


    progress_subjects = {}


    for subject, topics in progress.items():

        progress_subjects[
            subject
        ] = {}


        for topic, data in topics.items():

            progress_subjects[
                subject
            ][topic] = {

                "attempts":
                    data.get(
                        "attempts",
                        0
                    ),

                "confidence":
                    data.get(
                        "confidence",
                        50
                    ),

                "mastered":
                    data.get(
                        "mastered",
                        False
                    )

            }


    # ========================================================
    # UNDERSTANDING
    # ========================================================

    difficulty = (
        understanding_tracker.get()
    )


    difficulty_totals = {

        "easy": 0,

        "medium": 0,

        "hard": 0

    }


    for subject_data in difficulty.values():

        difficulty_totals["easy"] += (
            subject_data.get(
                "easy",
                0
            )
        )

        difficulty_totals["medium"] += (
            subject_data.get(
                "medium",
                0
            )
        )

        difficulty_totals["hard"] += (
            subject_data.get(
                "hard",
                0
            )
        )


    # ========================================================
    # UNDERSTANDING ANALYZER
    # ========================================================

    understanding = (
        understanding_analyzer.get()
    )


    confidence_by_subject = []


    for subject, data in understanding.items():

        confidence_by_subject.append({

            "subject":
                subject,

            "confidence":
                data.get(
                    "confidence",
                    50
                ),

            "attempts":
                data.get(
                    "attempts",
                    0
                ),

            "mistakes":
                len(
                    data.get(
                        "mistakes",
                        []
                    )
                )

        })


    # ========================================================
    # KNOWLEDGE MAP
    # ========================================================

    knowledge = (
        knowledge_map.get()
    )


    knowledge_subjects = {}


    for subject, topics in knowledge.items():

        knowledge_subjects[
            subject
        ] = {}


        for topic, data in topics.items():

            knowledge_subjects[
                subject
            ][topic] = {

                "confidence":
                    data.get(
                        "confidence",
                        50
                    ),

                "attempts":
                    data.get(
                        "attempts",
                        0
                    )

            }


    # ========================================================
    # STRENGTHS / WEAKNESSES
    #
    # Based on actual mastery rather than
    # simply how often something was mentioned.
    # ========================================================

    strengths = []

    weaknesses = []


    for subject in subjects:

        for topic in subject["topics"]:

            mastery = topic["mastery"]


            if mastery >= 80:

                strengths.append({
                    "subject":
                        subject["name"],

                    "topic":
                        topic["name"],

                    "mastery":
                        mastery
                })


            elif mastery < 50:

                weaknesses.append({
                    "subject":
                        subject["name"],

                    "topic":
                        topic["name"],

                    "mastery":
                        mastery
                })


    strengths.sort(
        key=lambda item:
            item["mastery"],
        reverse=True
    )


    weaknesses.sort(
        key=lambda item:
            item["mastery"]
    )


    # ========================================================
    # RECENT ACTIVITY
    # ========================================================

    recent_activity = []


    for subject in subjects:

        for topic in subject["topics"]:

            recent_activity.append({

                "subject":
                    subject["name"],

                "topic":
                    topic["name"],

                "mastery":
                    topic["mastery"],

                "attempts":
                    topic["attempts"],

                "last_review":
                    topic["last_review"]

            })


    recent_activity.sort(
        key=lambda item:
            item.get(
                "last_review",
                ""
            ),
        reverse=True
    )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "overall": {

            "mastery":
                overall_mastery,

            "attempts":
                total_attempts,

            "correct":
                total_correct,

            "wrong":
                total_wrong,

            "topics":
                total_topics

        },


        "subjects":
            subjects,


        "strengths":
            strengths[:10],


        "weaknesses":
            weaknesses[:10],


        "difficulty":
            difficulty_totals,


        "confidence":
            confidence_by_subject,


        "progress":
            progress_subjects,


        "knowledge_map":
            knowledge_subjects,


        "recent_activity":
            recent_activity[:10]

    }
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from backend.user_context import set_active_user
from backend.learning_graph import LearningGraph
from backend.learning.progress_tracker import ProgressTracker
from backend.student.knowledge_map import KnowledgeMap
from backend.memory_system.memory_manager import MemoryManager
from student_profile import StudentProfile


router = APIRouter()


def _normalize_email(email: str | None) -> str:
    return str(email or "").strip().lower()


def _session_email(request: Request) -> str | None:
    from backend import api
    session = api.get_auth_session(request)
    if not isinstance(session, dict):
        return None
    email = _normalize_email(session.get("email"))
    return email or None


def _authorized_email(request: Request, requested_email: str | None = None) -> str:
    requested = _normalize_email(requested_email)
    session_email = _session_email(request)
    if session_email:
        if requested and requested != session_email:
            raise HTTPException(status_code=403, detail="Dashboard access is limited to the authenticated student.")
        return session_email

    from os import getenv
    if getenv("NOVA_ENV", "development").lower() != "production" and requested:
        return requested
    raise HTTPException(status_code=401, detail="A valid Nova session is required.")


def _clamp(value: Any, low: float = 0.0, high: float = 100.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = low
    return round(max(low, min(high, number)), 1)


def _int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _merge_topic_stats(progress: dict, graph: dict) -> tuple[dict, int, int, int, int]:
    subjects: dict[str, dict] = {}
    total_attempts = total_correct = total_wrong = total_topics = 0
    graph_subjects = graph.get("subjects", {}) if isinstance(graph, dict) else {}
    graph_subjects = graph_subjects if isinstance(graph_subjects, dict) else {}
    all_subjects = set(progress.keys()) | set(graph_subjects.keys())

    for subject in sorted(all_subjects, key=str.casefold):
        progress_topics = progress.get(subject, {})
        graph_node = graph_subjects.get(subject, {})
        graph_topics = graph_node.get("topics", {}) if isinstance(graph_node, dict) else {}
        progress_topics = progress_topics if isinstance(progress_topics, dict) else {}
        graph_topics = graph_topics if isinstance(graph_topics, dict) else {}
        topic_names = set(progress_topics.keys()) | set(graph_topics.keys())
        topic_rows = {}
        subject_attempts = subject_correct = subject_wrong = 0
        weighted_mastery = weighted_count = 0.0
        last_seen = None

        for topic in sorted(topic_names, key=str.casefold):
            p = progress_topics.get(topic, {}) if isinstance(progress_topics.get(topic, {}), dict) else {}
            g = graph_topics.get(topic, {}) if isinstance(graph_topics.get(topic, {}), dict) else {}
            attempts = max(_int(p.get("attempts")), _int(g.get("times_studied")))
            correct = _int(g.get("correct_answers"))
            wrong = _int(g.get("wrong_answers"))
            answers = correct + wrong
            confidence = _clamp(p.get("confidence", g.get("mastery", 0)))
            mastery = confidence if attempts else _clamp(g.get("mastery", confidence))
            if answers >= 2:
                accuracy = correct / answers * 100.0
                mastery = round(0.7 * mastery + 0.3 * accuracy, 1)
            seen = p.get("last_seen") or g.get("last_review") or ""
            if seen and (last_seen is None or str(seen) > str(last_seen)):
                last_seen = str(seen)
            topic_rows[topic] = {
                "name": topic,
                "mastery": mastery,
                "confidence": confidence,
                "attempts": attempts,
                "questions": answers,
                "correct_answers": correct,
                "wrong_answers": wrong,
                "last_review": seen,
                "mastered": bool(p.get("mastered")) and attempts >= 5,
            }
            subject_attempts += attempts
            subject_correct += correct
            subject_wrong += wrong
            weight = max(1, attempts)
            weighted_mastery += mastery * weight
            weighted_count += weight
            total_topics += 1

        if not topic_rows:
            continue
        subject_mastery = round(weighted_mastery / weighted_count, 1) if weighted_count else 0.0
        subject_questions = subject_correct + subject_wrong
        subject_accuracy = round(subject_correct / subject_questions * 100, 1) if subject_questions else None
        denominator = sum(max(1, row["attempts"]) for row in topic_rows.values())
        subject_confidence = round(
            sum(row["confidence"] * max(1, row["attempts"]) for row in topic_rows.values()) / denominator,
            1,
        ) if denominator else 0.0
        subjects[subject] = {
            "name": subject,
            "mastery": subject_mastery,
            "confidence": subject_confidence,
            "accuracy": subject_accuracy,
            "topics_count": len(topic_rows),
            "attempts": subject_attempts,
            "questions": subject_questions,
            "correct_answers": subject_correct,
            "wrong_answers": subject_wrong,
            "last_activity": last_seen,
            "topics": list(topic_rows.values()),
        }
        total_attempts += subject_attempts
        total_correct += subject_correct
        total_wrong += subject_wrong

    return subjects, total_attempts, total_correct, total_wrong, total_topics


def _build_dashboard(email: str) -> dict:
    set_active_user(email)
    progress = ProgressTracker(email).get()
    graph = LearningGraph(email).get()
    knowledge = KnowledgeMap(email).get()
    profile = StudentProfile(email).get()
    subjects, total_attempts, total_correct, total_wrong, total_topics = _merge_topic_stats(progress, graph)
    total_answers = total_correct + total_wrong

    if subjects:
        denominator = sum(max(1, item["attempts"]) for item in subjects.values())
        overall_mastery = round(sum(item["mastery"] * max(1, item["attempts"]) for item in subjects.values()) / denominator, 1)
        average_confidence = round(sum(item["confidence"] * max(1, item["attempts"]) for item in subjects.values()) / denominator, 1)
    else:
        overall_mastery = 0.0
        average_confidence = 0.0
    accuracy = round(total_correct / total_answers * 100, 1) if total_answers else 0.0

    strengths = []
    weaknesses = []
    recent = []
    confidence = []
    knowledge_subjects = []
    for name, subject in subjects.items():
        knowledge_subjects.append({"id": name.casefold().replace(" ", "-"), "name": name, "confidence": subject["confidence"], "topics": subject["topics_count"], "attempts": subject["attempts"]})
        confidence.append({"subject": name, "confidence": subject["confidence"], "attempts": subject["attempts"], "mistakes": subject["wrong_answers"]})
        if subject["mastery"] >= 75 and subject["attempts"] >= 3:
            strengths.append(f"{name} ({subject['mastery']:.0f}%)")
        if subject["mastery"] < 50:
            weaknesses.append(f"{name} ({subject['mastery']:.0f}%)")
        for topic in subject["topics"]:
            recent.append({"subject": name, "topic": topic["name"], "mastery": topic["mastery"], "attempts": topic["attempts"], "last_review": topic["last_review"]})

    recent.sort(key=lambda item: item.get("last_review", ""), reverse=True)
    try:
        memory = MemoryManager().get_all(email)
    except Exception:
        memory = {"memories": [], "statistics": {}}
    memory_count = _int(memory.get("statistics", {}).get("total_memories"))
    conversation_count = _int(memory.get("statistics", {}).get("total_episodes"))
    episodes = [m for m in memory.get("memories", []) if m.get("type") == "episode"]
    recent_conversations = []
    for item in sorted(episodes, key=lambda m: m.get("created_at", ""), reverse=True)[:50]:
        text = str(item.get("text", ""))
        recent_conversations.append({
            "id": item.get("conversation_id") or item.get("id"),
            "title": text.splitlines()[0][:80] or "Conversation",
            "last_message": text[-160:],
            "message_count": 1,
            "updated_at": item.get("created_at"),
        })

    questions = _int(profile.get("questions_asked", profile.get("questions")))
    return {
        "stats": {
            "questions": questions,
            "total_subjects": len(subjects),
            "total_topics": total_topics,
            "overall_mastery": overall_mastery,
            "correct_answers": total_correct,
            "wrong_answers": total_wrong,
            "study_attempts": total_attempts,
            "average_confidence": average_confidence,
            "understanding_attempts": total_attempts,
            "memory_count": memory_count,
            "conversation_count": conversation_count,
            "accuracy": accuracy,
        },
        "subjects": subjects,
        "knowledge_subjects": knowledge_subjects,
        "strengths": strengths[:10],
        "weaknesses": weaknesses[:10],
        "strength_details": strengths[:10],
        "weakness_details": weaknesses[:10],
        "difficulty": {"easy": 0, "medium": 0, "hard": 0},
        "confidence": confidence,
        "progress": progress,
        "knowledge_map": knowledge,
        "recent_activity": recent[:20],
        "recent_conversations": recent_conversations,
        "session": {"subject": "None", "topic": "None", "mode": "None", "score": 0},
        "overall": {"mastery": overall_mastery, "attempts": total_attempts, "correct": total_correct, "wrong": total_wrong, "topics": total_topics},
    }


@router.get("/dashboard")
def get_dashboard_authenticated(request: Request):
    return _build_dashboard(_authorized_email(request))


@router.get("/dashboard/{email}")
def get_dashboard(request: Request, email: str):
    return _build_dashboard(_authorized_email(request, email))

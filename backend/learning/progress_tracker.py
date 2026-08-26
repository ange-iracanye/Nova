import json
import hashlib
import re
from pathlib import Path
from datetime import datetime

from backend.user_context import set_active_user

_SUBJECT_ALIASES = {
    "math": "Mathematics", "mathematics": "Mathematics", "maths": "Mathematics", "algebra": "Mathematics", "calculus": "Mathematics", "geometry": "Mathematics", "statistics": "Mathematics", "stats": "Mathematics", "physics": "Physics", "biology": "Biology", "chemistry": "Chemistry", "geography": "Geography", "history": "History", "tech": "Technology", "technology": "Technology", "computer science": "Technology", "programming": "Technology", "coding": "Technology", "economics": "Economics", "economy": "Economics", "business": "Business", "management": "Business", "entrepreneurship": "Business", "psychology": "Psychology", "sociology": "Sociology", "philosophy": "Philosophy", "phylosophy": "Philosophy", "literature": "Literature", "english literature": "Literature", "language": "Languages", "languages": "Languages", "linguistics": "Languages", "french": "Languages", "français": "Languages", "english": "Languages", "spanish": "Languages", "german": "Languages", "italian": "Languages", "arabic": "Languages", "japanese": "Languages", "chinese": "Languages", "law": "Law", "legal studies": "Law", "political science": "Political Science", "politics": "Political Science", "government": "Political Science", "civics": "Political Science", "art": "Art", "fine art": "Art", "visual arts": "Art", "music": "Music",
}

_DOMAIN_KEYWORDS = {
    "Technology": {"python", "javascript", "typescript", "java", "c++", "c#", "rust", "golang", "programming", "coding", "algorithm", "algorithms", "database", "api", "software", "cybersecurity", "cyber security", "firewall", "networking", "linux", "docker", "github", "git", "quantum computing", "quantum computer", "machine learning", "artificial intelligence", "neural network", "operating system"},
    "Mathematics": {"algebra", "calculus", "geometry", "statistics", "probability", "equation", "theorem"},
    "Physics": {"physics", "newton", "mechanics", "thermodynamics", "electromagnetism", "quantum mechanics"},
    "Biology": {"biology", "cell", "mitosis", "genetics", "evolution", "organism", "anatomy"},
    "Chemistry": {"chemistry", "molecule", "atom", "reaction", "stoichiometry", "organic chemistry"},
    "Economics": {"economics", "inflation", "gdp", "supply", "demand", "macroeconomics", "microeconomics"},
    "Business": {"business", "marketing", "startup", "revenue", "profit", "accounting", "management"},
    "Psychology": {"psychology", "cognition", "behavior", "emotion", "conditioning"},
    "Sociology": {"sociology", "society", "social class", "culture", "inequality"},
    "Philosophy": {"philosophy", "ethics", "epistemology", "metaphysics", "existentialism"},
    "Languages": {"grammar", "vocabulary", "conjugation", "translation", "pronunciation", "syntax"},
    "Law": {"law", "contract", "court", "statute", "legal", "legislation", "precedent"},
    "Political Science": {"politics", "democracy", "election", "government", "parliament", "voting"},
    "Art": {"painting", "drawing", "sculpture", "perspective", "composition", "color theory"},
    "Music": {"music", "chord", "scale", "harmony", "melody", "rhythm", "counterpoint"},
}


def canonical_subject(subject, topic=None):
    value = " ".join(str(subject or "").strip().split()) or " ".join(str(topic or "").strip().split())
    if not value: return ""
    lowered = value.casefold()
    if lowered in _SUBJECT_ALIASES: return _SUBJECT_ALIASES[lowered]
    for alias, canonical in _SUBJECT_ALIASES.items():
        if len(alias) >= 4 and re.search(rf"\b{re.escape(alias)}\b", lowered): return canonical
    corpus = f"{value} {topic or ''}".casefold()
    scores = {domain: sum(1 for keyword in keywords if keyword in corpus) for domain, keywords in _DOMAIN_KEYWORDS.items()}
    best_domain, best_score = max(scores.items(), key=lambda item: item[1])
    return best_domain if best_score > 0 else value.title()


class ProgressTracker:
    """Persistent, user-isolated learning progress tracker."""

    def __init__(self, user_email=None):
        self.base_path = Path("data/memory/progress")
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.user_email = user_email.strip().lower() if user_email else None
        if self.user_email: set_active_user(self.user_email)
        self.file = self._get_file()
        if self.file.exists():
            try: self.progress = json.loads(self.file.read_text(encoding="utf-8"))
            except Exception: self.progress = {}
        else:
            self.progress = {}; self._save()

    def _get_file(self):
        if not self.user_email: return self.base_path / "default.json"
        return self.base_path / f"{hashlib.sha256(self.user_email.encode('utf-8')).hexdigest()}.json"

    def _save(self):
        temporary = self.file.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.progress, indent=4, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.file)

    def _merge_subject_aliases(self):
        merged, changed = {}, False
        for subject, topics in self.progress.items():
            target = canonical_subject(subject)
            if target != subject: changed = True
            bucket = merged.setdefault(target, {})
            if not isinstance(topics, dict): continue
            for topic, data in topics.items():
                if topic not in bucket:
                    bucket[topic] = data; continue
                old, incoming = bucket[topic], data
                if not isinstance(old, dict) or not isinstance(incoming, dict): continue
                old_attempts, new_attempts = int(old.get("attempts", 0) or 0), int(incoming.get("attempts", 0) or 0)
                total = old_attempts + new_attempts
                if total:
                    old["confidence"] = round((float(old.get("confidence", 50) or 50) * old_attempts + float(incoming.get("confidence", 50) or 50) * new_attempts) / total, 1)
                old["attempts"] = total
                old["last_seen"] = max(str(old.get("last_seen") or ""), str(incoming.get("last_seen") or ""))
                old["mastered"] = bool(old.get("mastered")) or bool(incoming.get("mastered"))
                for key in ("difficulty_easy", "difficulty_medium", "difficulty_hard"):
                    old[key] = int(old.get(key, 0) or 0) + int(incoming.get(key, 0) or 0)
        if changed:
            self.progress = merged; self._save()

    def update(self, subject, topic, confidence, difficulty=None):
        subject = canonical_subject(subject, topic)
        topic = " ".join(str(topic or "").strip().split())
        if not subject or not topic: return
        self._merge_subject_aliases()
        try: confidence = max(0.0, min(100.0, float(confidence)))
        except (TypeError, ValueError): confidence = 50.0
        bucket = self.progress.setdefault(subject, {})
        if topic not in bucket:
            bucket[topic] = {"attempts": 0, "confidence": 50, "mastered": False, "first_seen": datetime.now().isoformat(), "last_seen": None, "difficulty_easy": 0, "difficulty_medium": 0, "difficulty_hard": 0}
        data = bucket[topic]
        data["attempts"] = int(data.get("attempts", 0) or 0) + 1
        previous = float(data.get("confidence", 50) or 50)
        attempts = int(data["attempts"])
        learning_rate = 0.30 if attempts <= 3 else 0.15
        data["confidence"] = round(previous + (confidence - previous) * learning_rate, 1)
        data["mastered"] = data["confidence"] >= 85 and attempts >= 5
        data["last_seen"] = datetime.now().isoformat()
        level = str(difficulty or "").strip().lower()
        if level in {"easy", "medium", "hard"}:
            key = f"difficulty_{level}"
            data[key] = int(data.get(key, 0) or 0) + 1
        self._save()

    def get(self):
        self._merge_subject_aliases()
        return self.progress

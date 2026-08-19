"""Extensible subject taxonomy for Nova.

The original detector only knew six school subjects. This extension adds common
academic/professional domains and, more importantly, allows an explicitly named
subject to pass through even when it is not in the built-in taxonomy.
"""

from __future__ import annotations

import re

from backend.subject_detector import SubjectDetector


EXTENDED_SUBJECTS = {
    "technology": {
        "aliases": ["technology", "tech", "computer science", "programming", "coding", "software", "software engineering", "cybersecurity", "cyber security", "information technology", "it"],
        "keywords": ["python", "javascript", "typescript", "java", "c++", "c#", "rust", "golang", "algorithm", "algorithms", "data structure", "database", "api", "web development", "machine learning", "artificial intelligence", "neural network", "encryption", "firewall", "networking", "operating system", "git", "github", "docker", "linux"],
    },
    "economics": {
        "aliases": ["economics", "economy", "économie"],
        "keywords": ["supply", "demand", "inflation", "gdp", "unemployment", "market", "fiscal policy", "monetary policy", "interest rate", "microeconomics", "macroeconomics"],
    },
    "business": {
        "aliases": ["business", "management", "entrepreneurship"],
        "keywords": ["marketing", "startup", "revenue", "profit", "strategy", "management", "business plan", "accounting", "finance"],
    },
    "psychology": {
        "aliases": ["psychology", "psychologie"],
        "keywords": ["cognition", "memory", "behavior", "behaviour", "personality", "emotion", "learning theory", "conditioning", "psychological"],
    },
    "sociology": {
        "aliases": ["sociology", "sociologie"],
        "keywords": ["society", "social class", "culture", "socialization", "inequality", "demographics", "institution"],
    },
    "philosophy": {
        "aliases": ["philosophy", "philosophie"],
        "keywords": ["ethics", "epistemology", "metaphysics", "logic", "existentialism", "philosopher", "philosophical"],
    },
    "literature": {
        "aliases": ["literature", "english literature", "literary studies", "littérature"],
        "keywords": ["novel", "poem", "poetry", "metaphor", "symbolism", "narrative", "character analysis", "literary"],
    },
    "languages": {
        "aliases": ["language", "languages", "linguistics", "french", "français", "english", "spanish", "español", "german", "deutsch", "italian", "arabic", "japanese", "chinese"],
        "keywords": ["grammar", "vocabulary", "conjugation", "translation", "pronunciation", "verb", "tense", "syntax", "linguistics"],
    },
    "law": {
        "aliases": ["law", "legal studies", "droit"],
        "keywords": ["contract", "tort", "constitution", "statute", "court", "legal", "legislation", "precedent", "criminal law"],
    },
    "political science": {
        "aliases": ["political science", "politics", "government", "civics", "science politique"],
        "keywords": ["democracy", "election", "government", "parliament", "president", "political party", "constitution", "voting"],
    },
    "art": {
        "aliases": ["art", "fine art", "visual arts", "arts"],
        "keywords": ["painting", "drawing", "sculpture", "perspective", "composition", "color theory", "art history"],
    },
    "music": {
        "aliases": ["music", "musique"],
        "keywords": ["chord", "scale", "harmony", "melody", "rhythm", "notation", "counterpoint", "music theory"],
    },
}


def _normalize(value):
    return " ".join(str(value or "").strip().casefold().split())


def install_subject_extension():
    SubjectDetector.SUBJECTS.update(EXTENDED_SUBJECTS)
    original_analyze = SubjectDetector.analyze

    if getattr(SubjectDetector, "_nova_v3_subject_extension", False):
        return

    def analyze(self, text, use_semantic=True):
        result = original_analyze(self, text, use_semantic=use_semantic)
        if result.get("subject"):
            return result

        normalized = _normalize(text)
        patterns = (
            r"^(?:i am|i'm|i am currently|i'm currently) studying (?P<subject>[^.!?]+)",
            r"^(?:i study|i learn|i'm learning|i am learning) (?P<subject>[^.!?]+)",
            r"\b(?:study|studying|learn|learning)\s+(?P<subject>[a-z][a-z0-9 +#.&/-]{1,70})",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized, flags=re.IGNORECASE)
            if not match:
                continue
            subject = " ".join(match.group("subject").split()).strip(" ,:;")
            if not subject:
                continue
            subject = subject.title()
            return {
                "subject": subject,
                "topic": None,
                "confidence": 0.72,
                "method": "explicit_dynamic",
                "matched_words": [subject],
            }

        return result

    SubjectDetector.analyze = analyze
    SubjectDetector._nova_v3_subject_extension = True


install_subject_extension()

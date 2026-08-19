from backend.subject_detector import SubjectDetector


def test_subject_detector_supports_technology():
    detector = SubjectDetector()
    result = detector.analyze("I'm studying Python programming and recursion.")
    assert result["subject"] in {"technology", "Technology", "python", "Python"}


def test_subject_detector_accepts_explicit_dynamic_subject():
    detector = SubjectDetector()
    result = detector.analyze("I'm studying quantum computing.")
    assert result["subject"]
    assert result["confidence"] >= 0.7

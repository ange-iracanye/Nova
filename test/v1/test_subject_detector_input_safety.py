from backend.subject_detector import SubjectDetector


def test_subject_detector_rejects_oversized_input():
    detector = SubjectDetector()

    result = detector.analyze("biology " + ("x" * 12001), use_semantic=False)

    assert result["subject"] is None
    assert result["method"] == "none"


def test_subject_detector_sanitizes_nonprinting_characters():
    detector = SubjectDetector()

    result = detector.analyze("bio\x00logy", use_semantic=False)

    assert result["subject"] == "biology"


def test_subject_detector_handles_non_string_values_without_raising():
    detector = SubjectDetector()

    for value in (None, 42, [], {}, object()):
        result = detector.analyze(value, use_semantic=False)
        assert result["subject"] is None
        assert result["confidence"] == 0.0


def test_subject_detector_keeps_valid_french_subject_detection():
    detector = SubjectDetector()

    result = detector.analyze("Je révise la photosynthèse.", use_semantic=False)

    assert result["subject"] == "biology"

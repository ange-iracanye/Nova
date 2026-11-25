from backend.intent_detector import (
    INTENT_INVALID,
    MAX_INTENT_MESSAGE_LENGTH,
    IntentDetector,
)


def test_intent_detector_normalizes_whitespace_and_nonbreaking_spaces():
    detector = IntentDetector()

    normalized = detector.normalize("  hello\u00a0\n   Nova  ")

    assert normalized == "hello Nova"


def test_intent_detector_rejects_oversized_input_before_classification():
    detector = IntentDetector()

    result = detector.analyze("hello " + ("x" * MAX_INTENT_MESSAGE_LENGTH))

    assert result["intent"] == INTENT_INVALID
    assert result["normalized_message"] == ""


def test_intent_detector_rejects_objects_with_failing_string_conversion():
    class BrokenString:
        def __str__(self):
            raise RuntimeError("cannot stringify")

    detector = IntentDetector()

    assert detector.normalize(BrokenString()) == ""
    assert detector.analyze(BrokenString())["intent"] == INTENT_INVALID


def test_intent_detector_removes_nonprinting_control_characters():
    detector = IntentDetector()

    assert detector.normalize("explain\x00 photosynthesis") == "explain photosynthesis"

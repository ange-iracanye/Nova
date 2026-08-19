import unittest

from backend.dashboard import _merge_topic_stats
from backend.learning.progress_tracker import canonical_subject


class DashboardV1ContractTests(unittest.TestCase):
    def test_subject_aliases_are_not_collapsed_into_math(self):
        self.assertEqual(canonical_subject("python"), "Technology")
        self.assertEqual(canonical_subject("tech"), "Technology")
        self.assertEqual(canonical_subject("french"), "Languages")
        self.assertEqual(canonical_subject("economics"), "Economics")
        self.assertEqual(canonical_subject("algebra"), "Mathematics")

    def test_unknown_subject_is_preserved(self):
        self.assertEqual(canonical_subject("Quantum Computing"), "Technology")
        self.assertEqual(canonical_subject("Astrophotography"), "Astrophotography")

    def test_dashboard_uses_progress_confidence_and_does_not_instantly_master(self):
        subjects, attempts, correct, wrong, topics = _merge_topic_stats(
            {
                "Technology": {
                    "Python": {
                        "attempts": 1,
                        "confidence": 65,
                        "mastered": False,
                    }
                }
            },
            {},
        )
        self.assertEqual(attempts, 1)
        self.assertEqual(correct, 0)
        self.assertEqual(wrong, 0)
        self.assertEqual(topics, 1)
        self.assertEqual(subjects["Technology"]["mastery"], 65)
        self.assertFalse(subjects["Technology"]["topics"][0]["mastered"])

    def test_dashboard_merges_answer_evidence_without_overwriting_user_state(self):
        subjects, attempts, correct, wrong, topics = _merge_topic_stats(
            {
                "Physics": {
                    "Newton's laws": {
                        "attempts": 5,
                        "confidence": 80,
                        "mastered": False,
                    }
                }
            },
            {
                "subjects": {
                    "Physics": {
                        "topics": {
                            "Newton's laws": {
                                "times_studied": 5,
                                "correct_answers": 4,
                                "wrong_answers": 1,
                                "mastery": 80,
                            }
                        }
                    }
                }
            },
        )
        self.assertEqual(attempts, 5)
        self.assertEqual(correct, 4)
        self.assertEqual(wrong, 1)
        self.assertEqual(topics, 1)
        self.assertGreater(subjects["Physics"]["mastery"], 0)
        self.assertLessEqual(subjects["Physics"]["mastery"], 100)


if __name__ == "__main__":
    unittest.main()

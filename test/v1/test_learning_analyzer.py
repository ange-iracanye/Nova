from backend.learning.analyzer import LearningAnalyzer


def test_learning_analyzer_counts_topics_case_insensitively_with_unicode():
    analyzer = LearningAnalyzer()

    result = analyzer.analyze({
        "topics_seen": ["Café", "CAFÉ", "café", "Physics"]
    })

    assert result["total_topics"] == 2
    assert result["topic_counts"] == {"Café": 3, "Physics": 1}
    assert result["strengths"] == ["Café"]
    assert result["new_topics"] == ["Physics"]


def test_learning_analyzer_handles_malformed_profiles_and_topic_lists():
    analyzer = LearningAnalyzer()

    assert analyzer.analyze(None)["total_topics"] == 0
    assert analyzer.analyze({"topics_seen": "broken"})["total_topic_attempts"] == 0
    assert analyzer.analyze({"topics_seen": [None, 4, "", "  "]})["new_topics"] == []


def test_learning_analyzer_topic_lookup_is_case_insensitive():
    analyzer = LearningAnalyzer()

    details = analyzer.get_topic_analysis(
        {"topics_seen": ["Algebra", "Algebra"]},
        " algebra ",
    )

    assert details is not None
    assert details["topic"] == "Algebra"
    assert details["count"] == 2

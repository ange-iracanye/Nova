from backend.learning.study_planner import StudyPlanner


def test_study_plan_prioritizes_weaknesses_then_due_reviews():
    planner = StudyPlanner()

    plan = planner.build_plan({
        "weaknesses": ["Algebra", "Fractions"],
        "due_topics": ["Algebra", "Geometry"],
        "strengths": ["Biology"],
    })

    assert [item["topic"] for item in plan] == [
        "Algebra", "Fractions", "Geometry", "Biology"
    ]
    assert plan[0]["action"] == "practice"
    assert plan[2]["action"] == "review"


def test_study_plan_normalizes_duplicates_and_limits_output():
    planner = StudyPlanner()

    plan = planner.build_plan({
        "weaknesses": [" Algebra ", "algebra", None, 3, "Geometry"],
        "due_topics": ["Physics"],
    }, limit=2)

    assert [item["topic"] for item in plan] == ["Algebra", "Geometry"]


def test_study_plan_handles_invalid_profile_and_limit():
    planner = StudyPlanner()

    assert planner.build_plan(None) == [{
        "topic": "Choose a new topic",
        "action": "explore",
        "reason": "No learning history is available yet",
    }]
    assert len(planner.build_plan({"weaknesses": ["A", "B"]}, limit=float("inf"))) == 2


def test_recommend_preserves_legacy_response_contract():
    planner = StudyPlanner()

    assert planner.recommend({"weaknesses": ["Algebra"]}) == (
        "Today's recommendation: practice Algebra"
    )
    assert planner.recommend("invalid") == (
        "Today's recommendation: learn a new topic."
    )



def test_study_plan_includes_new_topics_before_strength_maintenance():
    planner = StudyPlanner()

    plan = planner.build_plan({
        "new_topics": ["Chemistry"],
        "strengths": ["Biology"],
    })

    assert [item["topic"] for item in plan] == ["Chemistry", "Biology"]
    assert plan[0]["action"] == "learn"
    assert plan[1]["action"] == "reinforce"



def test_study_recommendation_prioritizes_due_reviews_before_strengths():
    planner = StudyPlanner()

    assert planner.recommend({
        "due_topics": ["Geometry"],
        "strengths": ["Biology"],
    }) == "Today's recommendation: review Geometry"


def test_study_recommendation_uses_new_topic_when_no_review_is_due():
    planner = StudyPlanner()

    assert planner.recommend({
        "new_topics": ["Astronomy"],
        "strengths": ["Biology"],
    }) == "Today's recommendation: explore Astronomy"


def test_study_recommendation_falls_back_to_reinforcing_strengths():
    planner = StudyPlanner()

    assert planner.recommend({"strengths": ["Biology"]}) == (
        "Today's recommendation: reinforce Biology"
    )


def test_study_planner_bounds_topic_count_and_topic_length():
    planner = StudyPlanner()
    topics = [f"Topic {index}" for index in range(150)]
    topics.append("X" * 500)

    plan = planner.build_plan({"weaknesses": topics}, limit=20)

    assert len(plan) == 20
    assert all(len(item["topic"]) <= 160 for item in plan)


def test_study_planner_normalizes_whitespace_and_control_characters():
    planner = StudyPlanner()

    plan = planner.build_plan({
        "weaknesses": ["  Algebra\\n\\t basics  ", "Algebra basics"]
    })

    assert plan[0]["topic"] == "Algebra basics"
    assert len(plan) == 1


def test_study_planner_ignores_non_list_topic_collections():
    planner = StudyPlanner()

    plan = planner.build_plan({
        "weaknesses": "Algebra",
        "due_topics": {"Geometry"},
        "new_topics": 42,
    })

    assert plan[0]["topic"] == "Choose a new topic"

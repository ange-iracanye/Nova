from backend.analytics import _canonical_route


def test_analytics_persists_route_categories_without_dynamic_segments():
    assert _canonical_route("/dashboard/student@example.com") == "/dashboard"
    assert _canonical_route("/conversation/abc123") == "/conversation"
    assert _canonical_route("/chat/session-42?debug=true") == "/chat"
    assert _canonical_route("/untracked/private-value") == "/other"


def test_analytics_route_normalization_handles_empty_and_nested_paths():
    assert _canonical_route("") == "/other"
    assert _canonical_route("/settings/security") == "/settings"
    assert _canonical_route("/study/Mathematics/Algebra") == "/study"



def test_analytics_route_canonicalization_handles_case_slashes_and_fragments():
    assert _canonical_route("//CHAT//session-42///?debug=true#private") == "/chat"
    assert _canonical_route("/DASHBOARD/student#profile") == "/dashboard"
    assert _canonical_route("chat/session") == "/chat"
    assert _canonical_route("/unknown/path#fragment") == "/other"

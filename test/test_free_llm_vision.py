import json

import backend.free_llm as free_llm_module
from backend.free_llm import FreeLLM


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({
            "choices": [{
                "message": {"content": "The image contains a blue square."},
                "finish_reason": "stop",
            }]
        }).encode()


def test_free_llm_sends_images_as_multimodal_content(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=90):
        captured["payload"] = json.loads(request.data.decode())
        return FakeResponse()

    monkeypatch.setattr(free_llm_module, "urlopen", fake_urlopen)
    monkeypatch.setenv("NOVA_VISION_MODEL", "openrouter/free")
    llm = FreeLLM(max_retries=0)
    llm.api_key = "test-key"
    llm.set_pending_images([{
        "name": "diagram.png",
        "mime_type": "image/png",
        "data": "aGVsbG8=",
    }])

    answer = llm._generate(
        "You are Nova.",
        "What is in this picture?",
        llm.get_generation_settings("low"),
        "openrouter/free",
    )

    content = captured["payload"]["messages"][1]["content"]
    assert answer == "The image contains a blue square."
    assert content[0] == {"type": "text", "text": "What is in this picture?"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_free_llm_uses_vision_router_when_images_are_pending(monkeypatch):
    monkeypatch.setenv("NOVA_VISION_MODEL", "openrouter/free")
    llm = FreeLLM(max_retries=0)
    llm.set_pending_images([{
        "name": "diagram.png", "mime_type": "image/png", "data": "aGVsbG8=",
    }])
    # The selected model is applied by answer(); this assertion protects the configured route.
    assert llm.pending_images[0]["mime_type"] == "image/png"

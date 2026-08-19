from __future__ import annotations


def test_fast_runtime_uses_configured_model(monkeypatch):
    monkeypatch.setenv("OLLAMA_MODEL", "test-model:latest")

    from backend.llm import LocalLLM
    from backend.fast_runtime import install_fast_runtime

    install_fast_runtime()
    assert LocalLLM.DEFAULT_MODEL == "test-model:latest"


def test_fast_response_cache_reuses_safe_answer():
    from backend.fast_response_pipeline import FastResponsePipeline

    pipeline = FastResponsePipeline()
    calls = {"count": 0}

    def generate(**_kwargs):
        calls["count"] += 1
        return "cached answer"

    first = pipeline.answer(
        generate,
        model="test-model",
        system="You are Nova.",
        user="Explain photosynthesis.",
        creativity="medium",
    )
    second = pipeline.answer(
        generate,
        model="test-model",
        system="You are Nova.",
        user="Explain photosynthesis.",
        creativity="medium",
    )

    assert first == second == "cached answer"
    assert calls["count"] == 1
    assert pipeline.stats()["cache_hits"] == 1

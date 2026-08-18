"""Quick local benchmark for Nova's latency layer.

Run from the repository root:
    python -m backend.bench_fast_pipeline
"""
from __future__ import annotations

import time

from backend.fast_response_pipeline import FastResponsePipeline


def main() -> None:
    pipeline = FastResponsePipeline()
    calls = {"count": 0}

    def fake_llm(**_kwargs: object) -> str:
        calls["count"] += 1
        time.sleep(0.05)
        return "benchmark answer"

    started = time.perf_counter()
    first = pipeline.answer(
        fake_llm,
        model="benchmark",
        system="You are Nova.",
        user="Explain why the sky appears blue.",
        creativity="medium",
    )
    first_ms = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    second = pipeline.answer(
        fake_llm,
        model="benchmark",
        system="You are Nova.",
        user="Explain why the sky appears blue.",
        creativity="medium",
    )
    second_ms = (time.perf_counter() - started) * 1000

    assert first == second == "benchmark answer"
    assert calls["count"] == 1, "Second identical request should be cached"
    assert second_ms < first_ms

    print("Nova fast pipeline benchmark: PASS")
    print(f"First request:  {first_ms:.2f} ms")
    print(f"Cached request: {second_ms:.2f} ms")
    print(f"LLM calls:      {calls['count']}")
    print(f"Stats:          {pipeline.stats()}")


if __name__ == "__main__":
    main()

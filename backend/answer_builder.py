class AnswerBuilder:

    def build(self, question, facts):

        if not facts:

            return "I couldn't find enough information."

        answer = facts[0]

        if len(facts) > 1:

            answer += "\n\nRelated information:\n"

            for fact in facts[1:]:

                answer += f"• {fact}\n"

        return answer


# Register lightweight analytics while the FastAPI app is being assembled.
try:
    import backend.analytics_bootstrap  # noqa: F401,E402
except Exception as exc:
    print(f"Nova analytics bootstrap unavailable: {type(exc).__name__}: {exc}", flush=True)

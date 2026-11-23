import re


class AnswerVerifier:
    """Correct a narrow set of deterministic answer claims."""

    MAX_FIBONACCI_INDEX = 1000

    def verify(self, question, answer):
        if not isinstance(question, str) or not isinstance(answer, str):
            return answer

        match = re.search(
            r"fibonacci\s*\(\s*(\d+)\s*\)",
            question.casefold(),
        )
        if not match:
            return answer

        raw_index = match.group(1)
        if len(raw_index) > len(str(self.MAX_FIBONACCI_INDEX)):
            return answer
        n = int(raw_index)
        if n > self.MAX_FIBONACCI_INDEX:
            return answer

        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b

        number_matches = re.findall(
            r"(?:is|equals|means)\s+(\d+)",
            answer.casefold(),
        )
        if number_matches:
            try:
                claimed = int(number_matches[0])
            except (ValueError, OverflowError):
                return answer
            if claimed != a:
                return f"Fibonacci({n}) = {a}."
        return answer

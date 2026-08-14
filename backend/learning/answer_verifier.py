import re


class AnswerVerifier:

    def verify(self, question, answer):

        question_lower = question.lower()

        # Fibonacci verification
        match = re.search(
            r"fibonacci\s*\(\s*(\d+)\s*\)",
            question_lower
        )

        if match:
            n = int(match.group(1))

            if n < 0:
                return answer

            a, b = 0, 1

            for _ in range(n):
                a, b = b, a + b

            expected = a

            # Look for a claim like "Fibonacci(8) is 21"
            number_matches = re.findall(
                r"(?:is|equals|means)\s+(\d+)",
                answer.lower()
            )

            if number_matches:
                claimed = int(number_matches[0])

                if claimed != expected:
                    return (
                        f"Fibonacci({n}) = {expected}."
                    )

        return answer
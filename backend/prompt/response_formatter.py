import re


LANGUAGES = {
    "python",
    "javascript",
    "typescript",
    "jsx",
    "tsx",
    "java",
    "cpp",
    "c",
    "csharp",
    "html",
    "css",
    "json",
    "sql",
    "bash",
    "shell",
}


CODE_START_PATTERN = re.compile(
    r"\b("
    + "|".join(re.escape(lang) for lang in LANGUAGES)
    + r")\s+",
    re.IGNORECASE,
)


def looks_like_code(line: str) -> bool:
    """
    Determines whether a line looks like programming code.
    """

    stripped = line.strip()

    if not stripped:
        return True

    code_patterns = [
        r"^def\s+\w+\(",
        r"^class\s+\w+",
        r"^import\s+",
        r"^from\s+\S+\s+import\s+",
        r"^if\s+.+:",
        r"^elif\s+.+:",
        r"^else\s*:",
        r"^for\s+.+:",
        r"^while\s+.+:",
        r"^return\s+",
        r"^print\s*\(",
        r"^\w+\s*=",
        r"^\w+\.\w+\(",
        r"^function\s+\w+",
        r"^const\s+\w+",
        r"^let\s+\w+",
        r"^var\s+\w+",
        r"^<\w+",
        r"^SELECT\s+",
        r"^INSERT\s+",
        r"^UPDATE\s+",
        r"^DELETE\s+",
    ]

    return any(
        re.search(pattern, stripped, re.IGNORECASE)
        for pattern in code_patterns
    )


def find_code_end(lines):
    """
    Finds where a malformed code section appears to end.
    """

    explanation_markers = [
        "this function",
        "this code",
        "let's break",
        "let's understand",
        "let us understand",
        "the function",
        "the code",
        "base cases:",
        "recursive step:",
        "example usage:",
        "running this function",
        "the output",
        "now let's",
        "now let’s",
        "this will",
        "it will",
    ]

    for index, line in enumerate(lines):

        stripped = line.strip().lower()

        if not stripped:
            continue

        for marker in explanation_markers:

            if stripped.startswith(marker):
                return index

    return len(lines)


def format_response(text: str) -> str:
    """
    Repairs programming code that the model outputs without
    Markdown fences.

    Example input:

        Here is the function:
        python def hello():
            return "Hello"

        This function returns a greeting.

    Becomes:

        Here is the function:

        ```python
        def hello():
            return "Hello"
        ```

        This function returns a greeting.
    """

    if not text:
        return text

    # If Nova already produced proper Markdown fences,
    # leave the response untouched.
    if "```" in text:
        return text

    lines = text.splitlines()

    result = []

    i = 0

    while i < len(lines):

        line = lines[i]

        match = CODE_START_PATTERN.search(line)

        if not match:
            result.append(line)
            i += 1
            continue

        language = match.group(1).lower()

        before = line[:match.start()].rstrip()
        first_code = line[match.end():].strip()

        if before:
            result.append(before)

        code_lines = []

        if first_code:
            code_lines.append(first_code)

        i += 1

        while i < len(lines):

            current = lines[i]
            stripped = current.strip()

            if not stripped:
                code_lines.append("")
                i += 1
                continue

            # Stop if another language marker begins.
            next_match = CODE_START_PATTERN.search(current)

            if next_match and not looks_like_code(current):
                break

            # Stop when obvious explanatory text begins.
            lowered = stripped.lower()

            explanation = False

            explanation_markers = [
                "in this function",
                "this function",
                "this code",
                "let's break",
                "let’s break",
                "let's understand",
                "let’s understand",
                "the function",
                "the code",
                "for example:",
                "example usage:",
                "running this function",
                "the output",
                "now let's",
                "now let’s",
            ]

            for marker in explanation_markers:

                if lowered.startswith(marker):
                    explanation = True
                    break

            if explanation:
                break

            code_lines.append(current)
            i += 1

        code = "\n".join(code_lines).strip()

        if code:
            result.append("")
            result.append(f"```{language}")
            result.append(code)
            result.append("```")
            result.append("")

    return "\n".join(result).strip()
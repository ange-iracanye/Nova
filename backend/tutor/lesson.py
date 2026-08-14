class LessonGenerator:

    def build(self, topic, explanation):

        lesson = []

        lesson.append(f"# {topic}")

        lesson.append("")

        lesson.append("Explanation")

        lesson.append(explanation)

        lesson.append("")

        lesson.append("Remember")

        lesson.append(
            "Understanding is more important than memorizing."
        )

        return "\n".join(lesson)
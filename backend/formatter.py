class Formatter:

    def title(
        self,
        text
    ):

        return text.title()

    def bullets(
        self,
        items
    ):

        return "\n".join(
            f"• {x}" for x in items
        )

    def separator(self):

        return "-" * 40
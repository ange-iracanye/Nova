import wikipedia

wikipedia.set_lang("en")


class WikipediaSearch:

    def search(

        self,

        question

    ):

        try:

            return wikipedia.summary(

                question,

                sentences=3

            )

        except Exception:

            return None
from ddgs import DDGS


class DuckDuckGo:

    def search(self, query):

        try:

            with DDGS() as ddgs:

                results = list(

                    ddgs.text(

                        query,

                        max_results=3

                    )

                )

            if not results:

                return None

            answer = ""

            for item in results:

                answer += item["body"] + "\n\n"

            return answer.strip()

        except:

            return None
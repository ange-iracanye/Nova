from backend.internet.duckduckgo import DuckDuckGo


class InternetManager:

    def __init__(self):

        self.ddg = DuckDuckGo()

    def search(self, query):

        result = self.ddg.search(query)

        if result:

            return result

        return None
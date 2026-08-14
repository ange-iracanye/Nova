class Router:

    def route(self, plan):

        if plan["use_memory"]:
            return "memory"

        if plan["use_knowledge"]:
            return "knowledge"

        if plan["use_internet"]:
            return "internet"

        return "chat"
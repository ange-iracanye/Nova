class Planner:

    def create_plan(self, intent):

        return {

            "intent": intent,

            "use_memory": True,

            "use_search": True,

            "use_reasoning": True

        }
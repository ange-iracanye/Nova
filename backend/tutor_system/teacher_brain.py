class TeacherBrain:


    def decide(self, knowledge_map, subject):

        if subject not in knowledge_map:
            return "normal"


        topics = knowledge_map[subject]


        total = 0
        count = 0


        for topic in topics:

            confidence = topics[topic]["confidence"]

            total += confidence
            count += 1


        if count == 0:
            return "normal"


        average = total / count


        if average < 40:
            return "simplify"


        if average < 70:
            return "practice"


        return "advanced"
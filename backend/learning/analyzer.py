class LearningAnalyzer:


    def analyze(self, profile):

        topics = profile.get("topics_seen", [])

        result = {
            "total_topics": len(topics),
            "strengths": [],
            "weaknesses": []
        }


        counts = {}


        for topic in topics:

            if topic in counts:
                counts[topic] += 1

            else:
                counts[topic] = 1


        for topic, amount in counts.items():

            if amount >= 3:
                result["strengths"].append(topic)

            elif amount <= 1:
                result["weaknesses"].append(topic)


        return result
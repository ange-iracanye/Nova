class QuizGenerator:

    def build(

        self,

        topic,

        explanation

    ):

        return f"""
Quiz

Topic:
{topic}

Question:

Explain {topic} using your own words.

Hint:

Think about the main idea before answering.

Reference:

{explanation}
"""
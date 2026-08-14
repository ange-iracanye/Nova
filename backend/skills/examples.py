class ExampleSkill:

    def build(

        self,

        topic

    ):

        examples={

            "gravity":

            "Example: A dropped phone falls because gravity pulls it toward Earth.",

            "triangle":

            "Example: A roof often forms a triangle.",

            "cell":

            "Example: Your skin is made of millions of cells."

        }

        return examples.get(

            topic.lower(),

            None

        )
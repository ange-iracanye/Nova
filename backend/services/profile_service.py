class ProfileService:

    def __init__(self):

        self.stats={

            "questions":0,

            "topics":{}

        }

    def asked(

        self,

        topic

    ):

        self.stats["questions"]+=1

        self.stats["topics"][topic]=(

            self.stats["topics"].get(

                topic,

                0

            )+1

        )

    def profile(self):

        return self.stats
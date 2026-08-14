class Progress:

    def __init__(self):

        self.subjects={}

    def studied(

        self,

        subject

    ):

        self.subjects[subject]=(

            self.subjects.get(subject,0)+1

        )

    def report(self):

        return self.subjects
class SubjectDetector:


    def __init__(self):

        self.subjects = {

            "physics": [
                "gravity",
                "force",
                "velocity",
                "speed",
                "energy",
                "motion",
                "acceleration",
                "mass",
                "newton"
            ],


            "biology": [
                "cell",
                "dna",
                "heart",
                "blood",
                "plant",
                "photosynthesis",
                "chlorophyll",
                "organism",
                "animal",
                "body",
                "gene"
            ],


            "chemistry": [
                "atom",
                "molecule",
                "acid",
                "reaction",
                "element",
                "compound",
                "chemical"
            ],


            "math": [
                "triangle",
                "equation",
                "area",
                "percentage",
                "algebra",
                "fraction",
                "number"
            ],


            "history": [
                "war",
                "king",
                "empire",
                "revolution",
                "civilization"
            ],


            "geography": [
                "country",
                "capital",
                "continent",
                "climate",
                "map"
            ]

        }



    def detect(self, text):

        t = text.lower()


        for subject, words in self.subjects.items():

            for word in words:

                if word in t:

                    return subject


        return None
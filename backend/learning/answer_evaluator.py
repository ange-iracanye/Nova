import re


class AnswerEvaluator:
    """A transparent keyword baseline, not a substitute for semantic grading."""

    KEYWORDS = {
        "physics": (
            "gravity", "force", "mass", "energy", "motion",
            "gravité", "force", "masse", "énergie", "mouvement",
        ),
        "biology": (
            "cell", "plant", "photosynthesis", "dna", "organism",
            "cellule", "plante", "photosynthèse", "adn", "organisme",
        ),
        "math": (
            "equation", "number", "solve", "variable", "formula",
            "algebra", "geometry", "fraction", "integer", "derivative",
            "équation", "nombre", "résoudre", "formule", "algèbre",
            "géométrie", "fraction", "entier", "dérivée",
        ),
        "chemistry": (
            "atom", "molecule", "element", "compound", "reaction",
            "electron", "proton", "periodic", "bond", "solution",
            "atome", "molécule", "élément", "composé", "réaction",
            "électron", "proton", "liaison",
        ),
        "computer science": (
            "algorithm", "variable", "function", "loop", "database",
            "program", "code", "input", "output", "data",
            "algorithme", "boucle", "base de données", "programme",
            "entrée", "sortie", "données",
        ),
        "history": (
            "empire", "revolution", "century", "historical", "civilization",
            "treaty", "war", "independence", "kingdom", "reform",
            "révolution", "siècle", "civilisation", "traité", "guerre",
            "indépendance", "royaume", "réforme",
        ),
        "geography": (
            "continent", "country", "climate", "population", "river",
            "mountain", "ocean", "capital", "latitude", "longitude",
            "pays", "climat", "rivière", "montagne", "océan", "capitale",
        ),
    }
    TOPIC_ALIASES = {
        "mathematics": "math",
        "mathématiques": "math",
        "mathematical": "math",
        "maths": "math",
        "algebra": "math",
        "geometry": "math",
        "arithmetic": "math",
        "calculus": "math",
        "statistics": "math",
        "chimie": "chemistry",
        "chemistry": "chemistry",
        "informatique": "computer science",
        "computer science": "computer science",
        "computer": "computer science",
        "histoire": "history",
        "geographie": "geography",
        "géographie": "geography",
        "physique": "physics",
        "biologie": "biology",
    }

    def evaluate(self, expected_topic, answer):
        if expected_topic is None:
            return 50
        try:
            topic = str(expected_topic).strip().casefold()
            raw_answer = "" if answer is None else str(answer)
        except Exception:
            return 0
        if len(topic) > 120 or len(raw_answer) > 12000:
            return 0

        topic = self.TOPIC_ALIASES.get(topic, topic)
        keywords = self.KEYWORDS.get(topic)
        if not keywords:
            return 0
        text = raw_answer.casefold()
        score = 0
        for word in dict.fromkeys(keywords):
            pattern = rf"(?<!\w){re.escape(word)}(?!\w)"
            if re.search(pattern, text, flags=re.UNICODE):
                score += 20
        return min(score, 100)

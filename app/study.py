import random



subjects = {

    "math": [
        "Mathematics studies numbers, patterns, equations, and structures.",
        "Algebra uses variables and equations to represent unknown values.",
        "Geometry studies shapes, angles, and measurements."
    ],


    "science": [
        "Science studies the natural world through observation and experiments.",
        "Physics studies forces, energy, and movement.",
        "Biology studies living organisms."
    ],


    "programming": [
        "Programming is writing instructions that computers can execute.",
        "Python is a programming language used for software and AI.",
        "Algorithms are step-by-step methods for solving problems."
    ]

}




def explain(subject):

    subject = subject.lower()


    if subject in subjects:

        return random.choice(
            subjects[subject]
        )


    return (
        "I do not have enough information "
        "about that subject yet."
    )




def quiz(subject):

    questions = {


        "math":
        [
            "What is the purpose of an equation?",
            "What does geometry study?"
        ],


        "science":
        [
            "What force attracts objects toward Earth?",
            "What does biology study?"
        ],


        "programming":
        [
            "What is an algorithm?",
            "What is Python used for?"
        ]

    }


    if subject in questions:

        return random.choice(
            questions[subject]
        )


    return "Choose a subject I know."
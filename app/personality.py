from settings import get_name, get_personality



def introduce():


    name = get_name()

    personality = get_personality()


    return (
        "I am "
        + name
        + ". My personality is "
        + personality
        + "."
    )



def format_answer(answer):


    name = get_name()


    return (
        name
        + ": "
        + answer
    )
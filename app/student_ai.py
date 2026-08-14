from student_profile import (
    update_name,
    update_level,
    add_subject,
    add_weak_subject,
    add_goal
)



def process(message):

    text = message.lower()



    if text.startswith("my name is "):

        name = message[11:].strip()

        update_name(name)

        return (
            True,
            "Nice to meet you, " + name + ". I will remember your name."
        )



    if text.startswith("i am in "):

        level = message[8:].strip()

        update_level(level)

        return (
            True,
            "I saved your school level."
        )



    if text.startswith("my favorite subject is "):

        subject = message[23:].strip()

        add_subject(subject)

        return (
            True,
            "Great! I'll remember that you like " + subject + "."
        )



    if text.startswith("i struggle with "):

        subject = message[16:].strip()

        add_weak_subject(subject)

        return (
            True,
            "I'll give you extra help in " + subject + "."
        )



    if text.startswith("my goal is "):

        goal = message[11:].strip()

        add_goal(goal)

        return (
            True,
            "Goal saved."
        )



    return (
        False,
        ""
    )
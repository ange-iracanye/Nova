import json


FILE = "student_profile.json"


def load_profile():

    with open(
        FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)



def save_profile(profile):

    with open(
        FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            profile,
            file,
            indent=4
        )



def update_name(name):

    profile = load_profile()

    profile["name"] = name

    save_profile(profile)



def update_level(level):

    profile = load_profile()

    profile["level"] = level

    save_profile(profile)



def add_subject(subject):

    profile = load_profile()

    if subject not in profile["subjects"]:

        profile["subjects"].append(subject)

    save_profile(profile)



def add_weak_subject(subject):

    profile = load_profile()

    if subject not in profile["weak_subjects"]:

        profile["weak_subjects"].append(subject)

    save_profile(profile)



def add_goal(goal):

    profile = load_profile()

    if goal not in profile["goals"]:

        profile["goals"].append(goal)

    save_profile(profile)



def get_profile():

    return load_profile()
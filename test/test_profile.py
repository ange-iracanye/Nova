from student_profile import update_profile, get_profile


update_profile(
    "name",
    "Alex"
)


update_profile(
    "level",
    "First year of high school"
)



profile = get_profile()


print(profile)
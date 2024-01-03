criteria = {
    "Very Skilled": [91, 100],
    "Skilled": [85, 90],
    "Fairly Skilled": [75, 84],
    "Less Skilled": [60, 74],
    "Not Skilled": [59],
}


def get_score_criteria_via_percentage(percentage_score: int):
    for key, value in criteria.items():
        if len(value) == 1:
            if percentage_score <= value[0]:
                return key
        else:
            if percentage_score in range(value[0], value[1] + 1):
                return key


def filter_courses_by_skill_level(courses, skill_level, course_type):
    return courses[
        (courses["SKILL LEVEL"].apply(lambda x: f"{skill_level}" in x.split(", ")))
        & (courses["TYPE"] == course_type)
    ]

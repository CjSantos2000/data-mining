import pandas as pd
import random
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer
from flask import Flask, request, jsonify
from utils import filter_courses_by_skill_level, get_score_criteria_via_percentage

app = Flask(__name__)

MAX_SCORE = 5

listening_questions = ["7", "8"]
writing_questions = ["2", "3", "6", "9", "10", "14"]
speaking_questions = ["1", "4", "5", "11", "12", "13", "16"]
reading_questions = ["15"]

# Criteria for skill level
criteria = {
    "Very Skilled": [91, 100],
    "Skilled": [85, 90],
    "Fairly Skilled": [75, 84],
    "Less Skilled": [60, 74],
    "Not Skilled": [59],
}


@app.route("/")
def hello():
    return "Hello"


@app.route("/recommend-course", methods=["POST"])
def recommend_course(*args, **kwargs):
    answers = request.json.get("answers")

    if len(answers) != 16:
        raise ValueError("Number of answers must be 16")

    if sum(answers) == 80:
        raise ValueError("You've got perfect score! Nothing to Recommend!")

    if max(answers) > 5:
        raise ValueError("Answer must be between 1 to 5")

    # Convert answers to dataframe
    question_results = pd.DataFrame(
        {str(index + 1): [answers[index]] for index in range(0, len(answers))}
    )

    # Read course data from Excel file
    courses = pd.read_excel("assets/Learning-Tools.xlsx")

    # Calculate total score and derive skill level
    question_results["Listening_total_percent"] = (
        question_results[listening_questions].sum(axis=1)
        / (len(listening_questions) * MAX_SCORE)
    ) * 100
    question_results["Writing_total_percent"] = (
        question_results[writing_questions].sum(axis=1)
        / (len(writing_questions) * MAX_SCORE)
    ) * 100
    question_results["Speaking_total_percent"] = (
        question_results[speaking_questions].sum(axis=1)
        / (len(speaking_questions) * MAX_SCORE)
    ) * 100
    question_results["Reading_total_percent"] = (
        question_results[reading_questions].sum(axis=1)
        / (len(reading_questions) * MAX_SCORE)
    ) * 100

    print(question_results)
    print("-" * 100)

    question_results["Writing_Level"] = get_score_criteria_via_percentage(
        int(question_results["Writing_total_percent"][0])
    )
    question_results["Listening_Level"] = get_score_criteria_via_percentage(
        int(question_results["Listening_total_percent"][0])
    )
    question_results["Speaking_Level"] = get_score_criteria_via_percentage(
        int(question_results["Speaking_total_percent"][0])
    )
    question_results["Reading_Level"] = get_score_criteria_via_percentage(
        int(question_results["Reading_total_percent"][0])
    )

    print("-" * 100)
    print(question_results)

    types = ["Writing", "Listening", "Speaking", "Reading"]

    lowest_types = sorted(
        types, key=lambda x: question_results[f"{x}_total_percent"][0]
    )[:2]
    filtered_courses = courses[courses["TYPE"].isin(lowest_types)]
    # filtered_courses = courses[courses["TYPE"].isin(lowest_types)].drop(
    #     ["Unnamed: 4", "Unnamed: 5"], axis=1
    # )

    print("-" * 100)
    print(filtered_courses)

    filtered_courses_1 = filter_courses_by_skill_level(
        filtered_courses,
        question_results[f"{lowest_types[0]}_Level"][0],
        lowest_types[0],
    )

    filtered_courses_2 = filter_courses_by_skill_level(
        filtered_courses,
        question_results[f"{lowest_types[1]}_Level"][0],
        lowest_types[1],
    )

    # filtered_courses_combine = pd.concat([filtered_courses_1, filtered_courses_2])

    # Recommend Courses 1 ---------------------------------------------------------------------------------------------

    # Convert skill levels to numeric representation for cosine similarity
    mlb = MultiLabelBinarizer()
    courses_encoded_1 = pd.DataFrame(
        mlb.fit_transform(
            filtered_courses_1["SKILL LEVEL"].apply(lambda x: x.split(", "))
        ),
        columns=mlb.classes_,
    )
    question_result_encoded_1 = pd.DataFrame(
        mlb.fit_transform(
            question_results[
                [
                    f"{lowest_types[0]}_Level",
                ]
            ].values.reshape(1, -1)
        ),
        columns=mlb.classes_,
    )
    courses_encoded_subset_1 = courses_encoded_1[question_result_encoded_1.columns]

    print(courses_encoded_subset_1)
    # Calculate cosine similarity
    cosine_similarity_result_1 = cosine_similarity(
        question_result_encoded_1, courses_encoded_subset_1
    )

    # Find the indices of the most similar records
    all_similar_indices_1 = cosine_similarity_result_1[0].argsort()[::-1].tolist()

    # Get 2 random indices from the list of all similar records
    random_indices_1 = random.sample(all_similar_indices_1, 2)

    # Recommend the top 2 courses
    recommended_courses_1 = filtered_courses_1.iloc[random_indices_1]

    print("Recommended Courses 1:")
    print(recommended_courses_1)
    # ------------------------------------------------------------------------------------------------------------------------

    # Recommend Courses 2 ----------------------------------------------------------------------------------------------------

    # Convert skill levels to numeric representation for cosine similarity
    courses_encoded_2 = pd.DataFrame(
        mlb.fit_transform(
            filtered_courses_2["SKILL LEVEL"].apply(lambda x: x.split(", "))
        ),
        columns=mlb.classes_,
    )

    question_result_encoded_2 = pd.DataFrame(
        mlb.fit_transform(
            question_results[
                [
                    f"{lowest_types[1]}_Level",
                ]
            ].values.reshape(1, -1)
        ),
        columns=mlb.classes_,
    )
    courses_encoded_subset_2 = courses_encoded_2[question_result_encoded_2.columns]

    # Calculate cosine similarity
    cosine_similarity_result_2 = cosine_similarity(
        question_result_encoded_1, courses_encoded_subset_2
    )

    # Find the indices of the top 2 most similar records
    all_similar_indices_2 = cosine_similarity_result_2[0].argsort()[::-1].tolist()

    # Get 2 random indices from the list of all similar records
    random_indices_2 = random.sample(all_similar_indices_2, 2)

    # Recommend the top 2 courses
    recommended_courses_2 = filtered_courses_2.iloc[random_indices_2]

    print("Recommended Courses 2:")
    print(recommended_courses_2)

    # ------------------------------------------------------------------------------------------------------------------------

    return jsonify(
        {
            "courses": {
                1: recommended_courses_1.to_dict(orient="records"),
                2: recommended_courses_2.to_dict(orient="records"),
            },
        }
    )


if __name__ == "__main__":
    app.run(debug=True)

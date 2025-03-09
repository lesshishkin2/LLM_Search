from dotenv import load_dotenv
import time
import logging
from logging_config import setup_logging
from datetime import datetime
from pathlib import Path
from question_and_answer_classes import Question
from config import (
    SUBSET_JSON_PATH,
    QUESTIONS_JSON_PATH,
    META_INFO_JSON_PATH
)
from data_tools import (
    Dataset,
    load_questions,
    save_to_pickle,
)
from pipeline import Pipeline
from question_and_answer_classes import AnswerSubmission, Answer, SourceReference
import requests


def create_answer_submission(questions: list[Question], team_email, submission_name):
    answers = []
    for q in questions:
        refs = []
        if q.references:
            for page_index, pdf_sha1 in q.references:
                refs.append(SourceReference(
                    pdf_sha1=pdf_sha1, page_index=page_index))

        answer_value = q.answer
        answers.append(
            Answer(
                question_text=q.text,
                kind=q.kind,
                value=answer_value,
                references=refs
            )
        )

    return AnswerSubmission(answers=answers, team_email=team_email, submission_name=submission_name)


def submit(path: Path):
    url = "https://rag.timetoact.at/submit"
    headers = {"accept": "application/json"}
    files = {
        "file": ("submission.json", open(path, "rb"), "application/json")
    }
    response = requests.post(url, headers=headers, files=files).json()
    print(response["status"])
    print(response["message"])

    return response


def main():
    start_time = time.time()

    RUN_ID = datetime.now().strftime('%Y%m%d_%H%M%S')
    RUN_DIR = Path("runs") / RUN_ID
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    load_dotenv()

    setup_logging(RUN_DIR, RUN_ID)
    logger = logging.getLogger(__name__)

    questions: list[Question] = load_questions(QUESTIONS_JSON_PATH)
    subset = Dataset(SUBSET_JSON_PATH, META_INFO_JSON_PATH)
    pipeline = Pipeline(questions, subset)

    # Step 1
    # Expand queries. Determine which companies are required.
    pipeline.recognize_and_expand()

    # Step 2
    # Searching for pages in documents that will help answer additional questions.
    start_find_pages_time = time.time()
    pipeline.find_pages()
    end_find_pages_time = time.time()
    logger.info(
        f"Time to find pages: {end_find_pages_time-start_find_pages_time:.1f}")

    # Step 3
    # Answer the auxiliary questions using the content from the found pages.
    pipeline.answer_helper_questions()

    # Step 4
    # Get final answer for the original question
    questions_with_final_answers = pipeline.get_final_answers()
    # Save for analysis
    save_to_pickle(questions_with_final_answers, RUN_DIR /
                   "questions_with_final_answers.pkl")

    # Create the AnswerSubmission object using the questions with final answers.
    submission = create_answer_submission(
        questions_with_final_answers,
        team_email="lesshishkin@gmail.com",
        submission_name=f"Submission_{RUN_ID}"
    )

    submission_file = RUN_DIR / "submission.json"
    with submission_file.open("w", encoding="utf-8") as f:
        f.write(submission.model_dump_json(indent=2))
    logger.info(f"Submission saved to {submission_file}")

    # TODO DO NOT FORGET TO UNCOMMENT!!!
    response = submit(submission_file)
    logger.debug(f"Submission response: {response}")

    end_time = time.time()
    logger.info(f"Execution time: {end_time-start_time:.1f} seconds")


if __name__ == "__main__":
    main()

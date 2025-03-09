import re
from pathlib import Path
import json
from typing import List
import pickle
import logging


logger = logging.getLogger(__name__)


class Dataset():
    def __init__(self, dataset_path: Path, metadata_path: Path) -> None:
        self.path = dataset_path
        self.metadata_path = metadata_path
        self.sha1_to_company = {}
        self.company_to_sha1 = {}

        try:
            with open(self.path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)
                for entry in data:
                    sha1_val = entry.get('sha1')
                    company = entry.get('company_name')
                    if sha1_val and company:
                        self.sha1_to_company[sha1_val] = company
                        self.company_to_sha1[company] = sha1_val
        except Exception as e:
            logger.error(f"Error reading JSON file {self.path}: {e}")
            raise e

        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as json_file:
                self.meta_data = json.load(json_file)
        except Exception as e:
            logger.error(f"Error reading JSON file {self.metadata_path}: {e}")
            raise e

    def get_company(self, sha1_value: str) -> str:
        """
        Retrieve the company name corresponding to the given SHA1 hash.

        Args:
            sha1_value (str): The SHA1 hash to look up.

        Returns:
            str: The company name corresponding to the provided SHA1.

        Raises:
            KeyError: If the SHA1 is not found.
        """
        company = self.sha1_to_company.get(sha1_value)
        if company is None:
            raise KeyError(f"SHA1 {sha1_value} not found.")
        return company

    def get_sha1(self, company_name: str) -> str:
        """
        Retrieve the SHA1 hash corresponding to the given company name.

        Args:
            company_name (str): The company name to look up.

        Returns:
            str: The SHA1 hash corresponding to the provided company name.

        Raises:
            KeyError: If the company name is not found.
        """
        sha1_val = self.company_to_sha1.get(company_name)
        if sha1_val is None:
            raise KeyError(f"Company {company_name} not found.")
        return sha1_val

    def get_company_list(self) -> List[str]:
        """
        Returns a list of all company names available in Dataset.
        """
        return list(self.company_to_sha1.keys())

    def get_period_end(self, sha1) -> str:
        year = self.meta_data[sha1]["end_of_period"]["year"]
        month = self.meta_data[sha1]["end_of_period"]["month"]
        return f"Year: {year}. Month: {month}"

    def get_currency(self, sha1) -> str:
        return self.meta_data[sha1]["currency_of_financial_statements"]


def save_to_pickle(data, file_path):
    """
    Save the given data to a pickle file.

    :param data: The data to be saved.
    :param file_path: The path where the pickle file will be saved.
    """
    try:
        with open(file_path, 'wb') as file:
            pickle.dump(data, file)
        logger.info(f"Data successfully saved to {file_path}")
    except Exception as e:
        logger.error(f"An error occurred while saving to pickle: {e}")


def extract_pages(page_numbers: List[int], file_path: str) -> List[str]:
    """
    Extracts and returns the texts of the specified pages from an md file,
    where each page is separated by the pattern:
    {page_number}------------------------------------------------

    Only existing pages are returned. If a given page number does not exist
    in the file, it is skipped.

    :param page_numbers: a list of requested page numbers (List[int])
    :param file_path: path to the file (str)
    :return: a list of page contents (List[str]) for found pages only.
    """
    # Read the entire file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'\{(\d+)\}------------------------------------------------(.*?)(?=\{\d+\}------------------------------------------------|$)'
    matches = re.findall(pattern, content, flags=re.DOTALL)

    # Build a dictionary mapping page numbers to their full content, including the header line
    pages_dict = {
        int(page_num): f"<page page_number={page_num}>{page_text}</page>"
        for page_num, page_text in matches
    }

    # Collect only the pages that exist in the file, sorting page_numbers in ascending order
    result = []
    for num in sorted(page_numbers):
        if num in pages_dict:
            # Add the page content to the result list
            result.append(pages_dict[num].strip())

    return result


def get_all_pages(file_path: str) -> List[str]:
    """
    Extracts and returns a list of all pages from a markdown file,
    where each page is separated by the pattern:
    {page_number}------------------------------------------------

    Each page's content includes its header with the page number.

    :param file_path: Path to the file (str).
    :return: A list of page contents (List[str]) for all pages found in the file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'\{(\d+)\}------------------------------------------------(.*?)(?=\{\d+\}------------------------------------------------|$)'
    matches = re.findall(pattern, content, flags=re.DOTALL)

    pages_list = [
        f"<page page_number={page_num}>\n\n{page_text.strip()}\n\n</page>" for page_num, page_text in matches]
    return pages_list


def load_questions(path: Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON file {path}: {e}")
        raise

    from question_and_answer_classes import Question
    questions = []
    for q in questions_data:
        try:
            question = Question(
                text=q["text"],
                kind=q["kind"],
            )
            questions.append(question)
        except Exception as e:
            logger.error(f"Failed to create Question object from {q}: {e}")
            raise
    return questions


def load_from_pickle(path):
    try:
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading pickle file {path}: {e}")
        raise

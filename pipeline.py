from question_and_answer_classes import (
    Question,
    HelperQuestion
)
from data_tools import (
    Dataset,
    get_all_pages,
    extract_pages
)
from prompt_templates import (
    query_expansion_prompt,
    find_pages_prompt,
    answer_question_using_pages_prompt,
    final_answer_prompt
)
from config import (
    MD_FILES_PATH,
    MODEL_BIG,
    MODEL_MINI,
    MODEL_REASONING,
    NUM_QUERY_EXPANSION_WORKERS,
    NUM_SEARCH_WORKERS,
    NUM_ANSWER_WORKERS
)
from llm_tools import ask_gpt
from response_formats import (
    ExpandedQuery,
    PageFinderAnswer,
    AnswerUsingContext,
    FinalAnswerBoolean,
    FinalAnswerName,
    FinalAnswerNames,
    FinalAnswerNumeric,
)
from concurrent.futures import ThreadPoolExecutor
import logging


logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, questions: list[Question], dataset: Dataset) -> None:
        self.questions = questions
        self.dataset = dataset

    def recognize_and_expand(self):
        def process_question(question: Question):
            prompt = query_expansion_prompt.format(user_question=question.text)
            gpt_response: ExpandedQuery = ask_gpt(
                model=MODEL_BIG,
                prompt=prompt,
                response_format=ExpandedQuery,
                timeout=30
            )

            if len(gpt_response.reformulated_questions) > 1:
                question.single_question = False

            helper_questions = []
            for reformulated_question in gpt_response.reformulated_questions:
                if reformulated_question.company_name not in self.dataset.get_company_list():
                    raise ValueError(
                        f"Wrong company: {reformulated_question.company_name}"
                    )
                helper_q = HelperQuestion(
                    text=reformulated_question.reformulated_question_text,
                    company=reformulated_question.company_name,
                )
                helper_questions.append(helper_q)

            question.helper_questions = helper_questions
            question.qe_reasoning = gpt_response.chain_of_thought

        logger.info(
            "Step 1. Expand queries. Determine which companies are required.")
        with ThreadPoolExecutor(max_workers=NUM_QUERY_EXPANSION_WORKERS) as executor:
            futures = [executor.submit(process_question, question)
                       for question in self.questions]
            for future in futures:
                future.result()

        # TODO наверное убрать потом
        for question in self.questions:
            for helper_question in question.helper_questions:
                sha1 = self.dataset.get_sha1(helper_question.company)
                file_path = MD_FILES_PATH / f"{sha1}.md"
                if not file_path.exists():
                    question.continue_processing = False
                    question.answer = "N/A"
                    break

        return self.questions

    def find_pages(self):
        logger.info(
            "Step 2. Searching for pages in documents that will help answer additional questions.")
        for idx, question in enumerate(self.questions):
            logger.info(f'Working with question {idx+1}')

            if question.continue_processing:
                for helper_q in question.helper_questions:
                    sha1 = self.dataset.get_sha1(helper_q.company)
                    pages_list = get_all_pages(MD_FILES_PATH / f"{sha1}.md")
                    period_end = self.dataset.get_period_end(sha1)
                    currency = self.dataset.get_currency(sha1)

                    references = []

                    def process_page(item):
                        page_number, page = item
                        prompt = find_pages_prompt.format(
                            question=helper_q.text, context=page, period_end=period_end, currency=currency)
                        gpt_response: PageFinderAnswer = ask_gpt(
                            model=MODEL_MINI,
                            prompt=prompt,
                            response_format=PageFinderAnswer,
                            timeout=30
                        )
                        return page_number, gpt_response

                    with ThreadPoolExecutor(max_workers=NUM_SEARCH_WORKERS) as executor:
                        results = list(executor.map(
                            process_page, enumerate(pages_list)))

                    for page_number, gpt_response in results:
                        helper_q.document_analysis[page_number] = gpt_response
                        if gpt_response.page_contains_the_answer:
                            references.append((page_number, sha1))
                    helper_q.found_references = references

        return self.questions

    @staticmethod
    def _create_auxiliary_q_and_a_str(question: Question) -> str:
        """
        This function takes a Question object and extracts data from its HelperQuestion objects.
        It then formats the extracted data into a string with a specific structure:

        Args:
            question (Question): The main question object containing helper questions.

        Returns:
            str: The formatted string containing all helper questions and their answers.
        """

        output = []

        for helper in question.helper_questions:
            output.append("\n<auxiliary_question>\n")
            output.append("## Auxiliary question:\n")
            output.append(f"{helper.text}\n\n")
            output.append(
                "## Answers to the auxiliary question found by our system:\n")

            if helper.answer:
                output.append(f"{helper.answer}\n")
            else:
                output.append("No answers provided\n")

            output.append("</auxiliary_question>\n")

        return "".join(output)

    def answer_helper_questions(self):
        def process_helper_questions(question: Question):
            for helper_q in question.helper_questions:
                page_numbers = [
                    ref[0] for ref in helper_q.found_references] if helper_q.found_references else []
                if not page_numbers:
                    helper_q.answer = "Information on this question was not found"
                else:
                    sha1 = self.dataset.get_sha1(helper_q.company)
                    period_end = self.dataset.get_period_end(sha1)
                    currency = self.dataset.get_currency(sha1)
                    pages = extract_pages(
                        page_numbers, MD_FILES_PATH / f"{sha1}.md")

                    prompt = answer_question_using_pages_prompt.format(
                        question=helper_q.text, pages=pages, period_end=period_end, currency=currency)
                    gpt_response: AnswerUsingContext = ask_gpt(
                        model=MODEL_REASONING,
                        prompt=prompt,
                        response_format=AnswerUsingContext,
                        reasoning=True,
                        timeout=120
                    )
                    helper_q.answer = gpt_response.answer
                    helper_q.repeated_question = gpt_response.question
                    helper_q.reasoning = gpt_response.chain_of_thought
                    helper_q.format_check = gpt_response.format_check
                    helper_q.timeframe_check = gpt_response.timeframe_check
                    helper_q.confirmed_references = [
                        (p_num, sha1) for p_num in gpt_response.reference_pages] if gpt_response.reference_pages else []

        logger.info(
            "Step 3. Answering auxiliary questions using the found pages.")
        with ThreadPoolExecutor(max_workers=NUM_ANSWER_WORKERS) as executor:
            futures = [executor.submit(process_helper_questions, question)
                       for question in self.questions if question.continue_processing]
            for future in futures:
                future.result()

        return self.questions

    def get_final_answers(self):
        def process_final_answer(question: Question):
            auxiliary_q_and_a = self._create_auxiliary_q_and_a_str(question)

            prompt = final_answer_prompt.format(
                original_question=question.text, auxiliary_q_and_a=auxiliary_q_and_a
            )
            question.final_prompt = prompt

            match question.kind:
                case "boolean":
                    response_format = FinalAnswerBoolean
                case "name":
                    response_format = FinalAnswerName
                case "names":
                    response_format = FinalAnswerNames
                case "number":
                    response_format = FinalAnswerNumeric
                case _:
                    raise

            gpt_response = ask_gpt(
                model=MODEL_REASONING,
                prompt=prompt,
                response_format=response_format,
                reasoning=True,
                timeout=40
            )

            question.answer = gpt_response.answer
            question.final_reasoning = gpt_response.chain_of_thought

            question.references = []
            for helper_q in question.helper_questions:
                if helper_q.confirmed_references:
                    question.references.extend(helper_q.confirmed_references)

            return question

        logger.info("Step 4. Getting final answers.")
        with ThreadPoolExecutor(max_workers=NUM_ANSWER_WORKERS) as executor:
            futures = [executor.submit(process_final_answer, question)
                       for question in self.questions if question.continue_processing]
            for future in futures:
                future.result()

        return self.questions

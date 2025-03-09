from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union


class ReformulatedQuestion(BaseModel):
    company_name: str = Field(
        ...,
        description="The name of the company extracted from the user's question."
    )
    reformulated_question_text: str = Field(
        ...,
        description="The reformulated question specific to this company."
    )


class ExpandedQuery(BaseModel):
    chain_of_thought: str = Field(
        ...,
        description="Your chain of reasoning preceding your precise answer."
    )
    reformulated_questions: list[ReformulatedQuestion] = Field(
        ...,
        description="A list of reformulated questions about companies mentioned in the user's question, including company name."
    )


class PageFinderAnswer(BaseModel):
    chain_of_thought: str = Field(
        ...,
        description="Your reasoning chain regarding the presence or absence of answer to the question in the provided excerpt from the annual report."
    )
    page_contains_the_answer: bool = Field(
        ...,
        description="Does the page contain an answer to the user's question or contain information necessary for the answer?"
    )


class FinalAnswerNumeric(BaseModel):
    chain_of_thought: str = Field(
        ...,
        description="The chain of reasoning preceding your precise answer."
    )
    answer: Union[float, Literal["N/A"]
                  ] = Field(..., description="Your final answer")


class FinalAnswerName(BaseModel):
    chain_of_thought: str = Field(
        ...,
        description="The chain of reasoning preceding your precise answer."
    )
    answer: Union[str, Literal["N/A"]
                  ] = Field(..., description="Your final answer")


class FinalAnswerNames(BaseModel):
    chain_of_thought: str = Field(
        ...,
        description="The chain of reasoning preceding your precise answer."
    )
    answer: Union[List[str], Literal["N/A"]] = Field(
        ..., description="List all answers separately as a list of strings")


class FinalAnswerBoolean(BaseModel):
    chain_of_thought: str = Field(
        ...,
        description="The chain of reasoning preceding your precise answer."
    )
    answer: bool = Field(..., description="Your final answer")


class AnswerUsingContext(BaseModel):
    question: str = Field(
        ...,
        description="Repeat the user's question"
    )
    chain_of_thought: str = Field(
        ...,
        description="The chain of reasoning and calculations preceding your precise answer."
    )
    timeframe_check: Optional[str] = Field(
        ...,
        description="Check that the provided pages contain data for the timeframe specified in the user's query."
    )
    format_check: Optional[str] = Field(
        ...,
        description="Check the format of the output answer. Additionally, check if you have confused millions with thousands."
    )
    answer: str = Field(..., description="Your final answer.")
    reference_pages: Optional[List[int]] = Field(
        ...,
        description="List only the numbers of pages that contain the answer"
    )


class EndOfPeriod(BaseModel):
    year: int
    month: int


class MetaDocumentInfo(BaseModel):
    chain_of_thought: str = Field(
        ...,
        description="How exactly did you obtain the answers."
    )
    end_of_period: EndOfPeriod = Field(
        ...,
        description="Year and month of the end of the last reporting period"
    )
    currency_of_financial_statements: str = Field(
        ...,
        description="Determine in which currency the financial statememts are presented this report. (US dollars, Japanese yens, etc)"
    )

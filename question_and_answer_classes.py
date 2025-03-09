from pydantic import BaseModel, RootModel, Field
from typing import Literal, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class HelperQuestion:
    text: str
    company: str
    document_analysis: dict[int, str] = field(default_factory=dict)
    found_references: Optional[list[tuple[int, str]]] = None
    confirmed_references: Optional[list[tuple[int, str]]] = None
    reasoning: Optional[str] = None
    format_check: Optional[str] = None
    timeframe_check: Optional[str] = None
    repeated_question: Optional[str] = None
    answer: Optional[str] = None


@dataclass
class Question():
    text: str
    kind: Literal["number", "name", "boolean", "names"]
    qe_reasoning: Optional[str] = None
    single_question: bool = True
    continue_processing: bool = True
    helper_questions: List[HelperQuestion] = field(default_factory=list)
    final_prompt: Optional[str] = None
    final_reasoning: Optional[str] = None
    answer: Optional[Union[str, float, bool, List[str]]] = None
    references: Optional[list[tuple[int, str]]] = None


class SourceReference(BaseModel):
    pdf_sha1: str = Field(..., description="SHA1 hash of the PDF file")
    page_index: int = Field(...,
                            description="Zero-based physical page number in the PDF file")


class Answer(BaseModel):
    question_text: str = Field(..., description="Text of the question")
    kind: Literal["number", "name", "boolean",
                  "names"] = Field(..., description="Kind of the question")
    value: Union[float, str, bool, List[str], Literal["N/A"]
                 ] = Field(..., description="Answer to the question, according to the question schema")
    references: List[SourceReference] = Field(
        [], description="References to the source material in the PDF file")


class AnswerSubmission(BaseModel):
    answers: List[Answer] = Field(...,
                                  description="List of answers to the questions")
    team_email: str = Field(
        ..., description="Email that your team used to register for the challenge")
    submission_name: str = Field(
        ..., description="Unique name of the submission (e.g. experiment name)")

from pydantic import BaseModel, Field, field_validator
from typing import Dict

class MCQItem(BaseModel):
    """Schema for a single MCQ"""
    question: str = Field(description="MCQ question")
    options: Dict[str, str] = Field(description="Answer options A, B, C, D")
    correct_answer: str = Field(description="Correct option (A, B, C, or D)")
    explanation: str = Field(description="Explanation for correct answer")
    source: str = Field(description="Source of the MCQ (PDF or Predefined)")
    difficulty: str = Field(description="Difficulty level (Easy, Moderate, Hard)")

    @field_validator('correct_answer')
    @classmethod
    def validate_correct_answer(cls, v):
        if v not in ['A', 'B', 'C', 'D']:
            raise ValueError("Correct answer must be A, B, C, or D")
        return v

    @field_validator('options')
    @classmethod
    def validate_options(cls, v):
        if not all(key in v for key in ['A', 'B', 'C', 'D']):
            raise ValueError("Options must contain keys A, B, C, and D")
        return v

    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v):
        if v not in ['Easy', 'Moderate', 'Hard']:
            raise ValueError("Difficulty must be Easy, Moderate, or Hard")
        return v

    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        if v not in ['PDF', 'Predefined']:
            raise ValueError("Source must be PDF or Predefined")
        return v
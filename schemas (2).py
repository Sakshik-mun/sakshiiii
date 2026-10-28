import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def valid_email(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def strong_password(cls, v):
        if not (re.search(r"[A-Za-z]", v) and re.search(r"\d", v)):
            raise ValueError("Password must contain letters and numbers")
        return v


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str


class ProfileIn(BaseModel):
    cibil_score: int = Field(ge=300, le=900)
    monthly_income: float = Field(ge=0)
    monthly_expenses: float = Field(ge=0)
    monthly_debt_payments: float = Field(ge=0)
    credit_limit: float = Field(ge=0)
    credit_used: float = Field(ge=0)
    active_loans: int = Field(ge=0)
    missed_payments: int = Field(ge=0)
    savings: float = Field(ge=0)
    financial_goal: str = Field(default="", max_length=255)

    @field_validator("credit_used")
    @classmethod
    def used_within_limit(cls, v, info):
        limit = info.data.get("credit_limit", 0)
        if limit and v > limit * 1.5:
            raise ValueError("credit_used is unrealistically higher than credit_limit")
        return v


class ScoreIn(BaseModel):
    score: int = Field(ge=300, le=900)


class ChatIn(BaseModel):
    message: str = Field(min_length=2, max_length=1000)


class RecOut(BaseModel):
    id: int
    kind: str
    prompt: str
    content: str
    created_at: datetime
    model_config = {"from_attributes": True}

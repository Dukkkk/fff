from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field


IncomeFrequency = Literal["weekly", "biweekly", "monthly", "irregular"]
TxnType = Literal["income", "expense"]


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    income_frequency: IncomeFrequency = "monthly"
    monthly_income_estimate: float = Field(default=0.0, ge=0.0)
    starting_balance: float = Field(default=0.0)


class UserOut(BaseModel):
    id: str
    name: str
    email: str | None
    income_frequency: IncomeFrequency
    monthly_income_estimate: float
    starting_balance: float
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class TransactionCreate(BaseModel):
    user_id: str
    date: dt.date
    amount: float = Field(gt=0)
    type: TxnType
    category: str
    merchant: str | None = None
    note: str | None = None
    tags: list[str] | None = None


class TransactionUpdate(BaseModel):
    date: dt.date | None = None
    amount: float | None = Field(default=None, gt=0)
    type: TxnType | None = None
    category: str | None = None
    merchant: str | None = None
    note: str | None = None
    tags: list[str] | None = None


class TransactionOut(BaseModel):
    id: str
    user_id: str
    date: dt.date
    amount: float
    type: TxnType
    category: str
    merchant: str | None
    note: str | None
    tags: list[str] | None = None
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class GoalCreate(BaseModel):
    user_id: str
    title: str
    target_amount: float = Field(gt=0)
    target_date: dt.date
    current_amount: float = Field(default=0.0, ge=0.0)
    category: str = "other"


class GoalUpdate(BaseModel):
    title: str | None = None
    target_amount: float | None = Field(default=None, gt=0)
    target_date: dt.date | None = None
    current_amount: float | None = Field(default=None, ge=0.0)
    category: str | None = None


class GoalOut(BaseModel):
    id: str
    user_id: str
    title: str
    target_amount: float
    target_date: dt.date
    current_amount: float
    category: str
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class ForecastPoint(BaseModel):
    date: dt.date
    projected_balance: float


class ForecastOut(BaseModel):
    user_id: str
    as_of: dt.date
    current_balance: float
    horizons_days: list[int]
    curve: list[ForecastPoint]
    days_until_broke: int | None
    safety_status: Literal["safe", "tight", "at_risk"]
    summary: str


class InsightOut(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    description: str
    severity: Literal["low", "medium", "high"]
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class NudgeOut(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    action_label: str | None
    created_at: dt.datetime

    model_config = {"from_attributes": True}


class StressScoreOut(BaseModel):
    user_id: str
    score: int = Field(ge=0, le=100)
    label: Literal["low", "moderate", "high"]
    explanation: str
    drivers: dict[str, float]


class RiskProfileOut(BaseModel):
    user_id: str
    profile: Literal["cautious", "balanced", "growth-ready"]
    explanation: str
    signals: dict[str, float]
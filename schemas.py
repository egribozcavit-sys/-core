import re
from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class TransactionCreate(BaseModel):
    sender_account_id: str
    receiver_account_id: str
    amount_cents: int = Field(..., gt=0)
    currency: str = "USD"
    transaction_type: str = "transfer"
    description: Optional[str] = None
    metadata: Optional[Dict] = None
    idempotency_key: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    sender_account_id: str
    receiver_account_id: str
    amount_cents: int
    currency: str
    status: str
    transaction_type: str
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    failed_at: Optional[datetime]
    failure_reason: Optional[str]


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    created_at: datetime


class AccountCreate(BaseModel):
    currency: str = "USD"


class BalanceResponse(BaseModel):
    account_id: str
    balance_cents: int
    currency: str


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    username: str
    password: str

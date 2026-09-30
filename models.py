import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_number = Column(String, unique=True, nullable=False, index=True)
    balance_cents = Column(Integer, default=0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_account_id = Column(
        String, ForeignKey("accounts.id"), nullable=False, index=True
    )
    receiver_account_id = Column(
        String, ForeignKey("accounts.id"), nullable=False, index=True
    )
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    status = Column(String, default="pending", nullable=False, index=True)
    transaction_type = Column(String, default="transfer", nullable=False)
    description = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_sender_created", "sender_account_id", "created_at"),
        Index("idx_receiver_created", "receiver_account_id", "created_at"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(
        String, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True
    )
    user_id = Column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action = Column(String, nullable=False)
    details_json = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

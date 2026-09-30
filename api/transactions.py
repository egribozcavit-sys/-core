import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Transaction, User
from app.schemas import TransactionCreate, TransactionResponse
from app.auth import get_current_user
from app.engine.core import TransactionTask, engine

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if transaction.idempotency_key:
        existing = (
            db.query(Transaction)
            .filter(Transaction.idempotency_key == transaction.idempotency_key)
            .first()
        )
        if existing:
            return TransactionResponse(
                id=existing.id,
                sender_account_id=existing.sender_account_id,
                receiver_account_id=existing.receiver_account_id,
                amount_cents=existing.amount_cents,
                currency=existing.currency,
                status=existing.status,
                transaction_type=existing.transaction_type,
                description=existing.description,
                created_at=existing.created_at,
                completed_at=existing.completed_at,
                failed_at=existing.failed_at,
                failure_reason=existing.failure_reason,
            )

    sender = db.query(Account).filter(
        Account.id == transaction.sender_account_id
    ).first()
    receiver = db.query(Account).filter(
        Account.id == transaction.receiver_account_id
    ).first()

    if not sender or not receiver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,

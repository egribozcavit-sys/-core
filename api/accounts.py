import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, User
from app.schemas import AccountCreate, BalanceResponse
from app.auth import get_current_user

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Hesap her zaman giriş yapan kullanıcıya ait olur.
    new_account = Account(
        user_id=current_user.id,
        account_number=str(uuid.uuid4()),
        currency=account.currency,
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return {
        "account_id": new_account.id,
        "account_number": new_account.account_number,
        "user_id": new_account.user_id,
        "balance_cents": new_account.balance_cents,
        "currency": new_account.currency,
    }


@router.get("/{account_id}/balance", response_model=BalanceResponse)
async def get_balance(
    account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == current_user.id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account not found"
        )
    return BalanceResponse(
        account_id=account.id,
        balance_cents=account.balance_cents,
        currency=account.currency,
    )

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List

import redis.asyncio as redis
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Account, AuditLog, Transaction
from app.config import settings

logger = logging.getLogger("paycore.engine")


@dataclass
class TransactionTask:
    sender_account_id: str
    receiver_account_id: str
    amount_cents: int
    currency: str
    transaction_type: str
    description: str
    metadata: Dict
    idempotency_key: str
    created_at: str


class TransactionEngine:
    def __init__(self):
        self.redis: redis.Redis = None
        self.running = False

    async def connect(self):
        self.redis = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=settings.REDIS_POOL_SIZE,
        )
        await self._ensure_consumer_group()
        logger.info("Transaction engine connected to Redis")

    async def _ensure_consumer_group(self):
        try:
            await self.redis.xgroup_create(
                settings.REDIS_STREAM_NAME,
                settings.REDIS_CONSUMER_GROUP,
                id="0",
                mkstream=True,
            )
        except Exception:
            # Group zaten varsa hata verir, görmezden geliyoruz.
            pass

    async def disconnect(self):
        if self.redis:
            await self.redis.close()
        self.running = False
        logger.info("Transaction engine disconnected")

    async def submit_transaction(self, task: TransactionTask) -> str:
        transaction_id = task.idempotency_key or str(time.time_ns())
        payload = {"transaction_id": transaction_id, **asdict(task)}
        await self.redis.xadd(settings.REDIS_STREAM_NAME, payload)
        logger.info(f"Transaction {transaction_id} queued")
        return transaction_id

    async def start_processing(self):
        self.running = True
        logger.info("Transaction engine started")
        while self.running:
            try:
                messages = await self.redis.xreadgroup(
                    groupname=settings.REDIS_CONSUMER_GROUP,
                    consumername="worker-1",
                    streams={settings.REDIS_STREAM_NAME: ">"},
                    count=settings.BATCH_SIZE,
                    block=1000,
                )
                if not messages:
                    continue
                stream_name, entries = messages[0]
                batch = [(entry_id, fields) for entry_id, fields in entries]
                if batch:
                    await self._process_batch(batch)
            except Exception as e:
                logger.error(f"Engine error: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _process_batch(self, batch: List[tuple]):
        db: Session = SessionLocal()
        try:
            for entry_id, fields in batch:
                await self._process_single(db, fields, entry_id)
            db.commit()
            logger.info(f"Batch processed: {len(batch)} transactions")
        except Exception as e:
            db.rollback()
            logger.error(f"Batch failed: {e}", exc_info=True)
            # Hata durumunda mesajı tekrar eklemiyoruz; manuel inceleme için
            # stream'de kalması daha güvenli.
        finally:
            db.close()

    async def _process_single(
        self, db: Session, fields: Dict, entry_id: str
    ) -> None:
        transaction_id = fields["transaction_id"]

        existing = db.query(Transaction).filter(
            Transaction.idempotency_key == fields.get("idempotency_key")
        ).first()
        if existing:
            logger.info(f"Duplicate transaction: {transaction_id}")
            await self.redis.xack(
                settings.REDIS_STREAM_NAME,
                settings.REDIS_CONSUMER_GROUP,
                entry_id,
            )
            return

        transaction = Transaction(
            id=transaction_id,
            sender_account_id=fields["sender_account_id"],
            receiver_account_id=fields["receiver_account_id"],
            amount_cents=int(fields["amount_cents"]),
            currency=fields["currency"],
            status="processing",
            transaction_type=fields["transaction_type"],
            description=fields.get("description"),
            metadata_json=json.dumps(fields.get("metadata", {})),
            idempotency_key=fields.get("idempotency_key"),
        )
        db.add(transaction)
        db.flush()

        sender = (
            db.query(Account)
            .filter(Account.id == fields["sender_account_id"])
            .with_for_update()
            .first()
        )
        receiver = (
            db.query(Account)
            .filter(Account.id == fields["receiver_account_id"])
            .with_for_update()
            .first()
        )

        if not sender or not receiver:
            transaction.status = "failed"
            transaction.failure_reason = "Account not found"
            transaction.failed_at = datetime.now(timezone.utc)
            await self.redis.xack(
                settings.REDIS_STREAM_NAME,
                settings.REDIS_CONSUMER_GROUP,
                entry_id,
            )
            return

        if sender.balance_cents < int(fields["amount_cents"]):
            transaction.status = "failed"
            transaction.failure_reason = "Insufficient balance"
            transaction.failed_at = datetime.now(timezone.utc)
            await self.redis.xack(
                settings.REDIS_STREAM_NAME,
                settings.REDIS_CONSUMER_GROUP,
                entry_id,
            )
            return

        sender.balance_cents -= int(fields["amount_cents"])
        receiver.balance_cents += int(fields["amount_cents"])
        receiver.updated_at = datetime.now(timezone.utc)

        transaction.status = "completed"
        transaction.completed_at = datetime.now(timezone.utc)

        audit = AuditLog(
            transaction_id=transaction.id,
            user_id=sender.user_id,
            action="transaction_completed",
            details_json=json.dumps(
                {
                    "amount_cents": int(fields["amount_cents"]),
                    "sender": fields["sender_account_id"],
                    "receiver": fields["receiver_account_id"],
                }
            ),
        )
        db.add(audit)

        await self.redis.xack(
            settings.REDIS_STREAM_NAME,
            settings.REDIS_CONSUMER_GROUP,
            entry_id,
        )
        logger.info(f"Transaction {transaction_id} completed")


engine = TransactionEngine()

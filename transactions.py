from datetime import datetime
from enum import Enum, IntEnum
from uuid import uuid4

from account import InvalidOperationError
from currency import Currency
from validators import ensure_number, ensure_text


class TransactionStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    EXTERNAL_TRANSFER = "external_transfer"


class Transaction:
    NEEDS_SENDER = (
        TransactionType.WITHDRAWAL,
        TransactionType.TRANSFER,
        TransactionType.EXTERNAL_TRANSFER,
    )

    NEEDS_RECEIVER = (
        TransactionType.DEPOSIT,
        TransactionType.TRANSFER,
        TransactionType.EXTERNAL_TRANSFER,
    )

    ALLOWED_FROM = {
        TransactionStatus.PROCESSING: (
            TransactionStatus.PENDING,
            TransactionStatus.FAILED,
        ),
        TransactionStatus.FAILED: (TransactionStatus.PROCESSING,),
        TransactionStatus.COMPLETED: (TransactionStatus.PROCESSING,),
        TransactionStatus.CANCELLED: (
            TransactionStatus.PENDING,
            TransactionStatus.FAILED,
        ),
    }

    def __init__(
        self,
        amount,
        currency,
        transaction_type,
        sender_id=None,
        receiver_id=None,
        transaction_id=None,
        fee=0,
    ):
        if transaction_id is None:
            self._transaction_id = uuid4().hex
        else:
            self._transaction_id = ensure_text(transaction_id, "transaction_id")

        ensure_number(amount, "amount")
        if amount <= 0:
            raise ValueError(f"amount must be positive, got {amount}")
        self._amount = amount

        if not isinstance(currency, Currency):
            raise TypeError(
                f"currency must be a Currency member, got {currency!r}; try Currency({currency!r})"
            )
        self._currency = currency

        ensure_number(fee, "fee")
        if fee < 0:
            raise ValueError(f"fee cannot be negative, got {fee}")
        self._fee = fee

        if sender_id is not None:
            self._sender_id = ensure_text(sender_id, "sender_id")
        else:
            self._sender_id = sender_id

        if receiver_id is not None:
            self._receiver_id = ensure_text(receiver_id, "receiver_id")
        else:
            self._receiver_id = receiver_id

        if not isinstance(transaction_type, TransactionType):
            raise TypeError(
                f"transaction_type must be a TransactionType member, got "
                f"{transaction_type!r}; try TransactionType({transaction_type!r})"
            )

        self._transaction_type = transaction_type
        self._validate_parties()
        self._status = TransactionStatus.PENDING
        self._created_at = datetime.now()
        self._updated_at = None
        self._failure_reason = None
        self._attempts = 0

    def __str__(self):
        result = (
            f"{self._transaction_type.value} | {self._transaction_id} | "
            f"{self._amount} {self._currency.value} | fee {self._fee} | "
            f"{self._sender_id} -> {self._receiver_id} | {self._status.value}"
        )
        if self._failure_reason is not None:
            result += f" | reason {self._failure_reason}"

        return result

    def _validate_parties(self):
        self._check_party(
            "sender_id", self._sender_id, self._transaction_type in self.NEEDS_SENDER
        )
        self._check_party(
            "receiver_id",
            self._receiver_id,
            self._transaction_type in self.NEEDS_RECEIVER,
        )

    def _check_party(self, label, value, required):
        if required and value is None:
            raise ValueError(f"{label} is required but None")
        if not required and value is not None:
            raise ValueError(f"{label} is not required but present")

    @property
    def transaction_id(self):
        return self._transaction_id

    @property
    def status(self):
        return self._status

    @property
    def fee(self):
        return self._fee

    @property
    def amount(self):
        return self._amount

    @property
    def currency(self):
        return self._currency

    @property
    def transaction_type(self):
        return self._transaction_type

    @property
    def sender_id(self):
        return self._sender_id

    @property
    def receiver_id(self):
        return self._receiver_id

    @property
    def attempts(self):
        return self._attempts

    def _transition(self, new_status):
        if not isinstance(new_status, TransactionStatus):
            raise TypeError(
                f"new_status must be a TransactionStatus member, got {new_status!r}; "
                f"try TransactionStatus({new_status!r})"
            )
        allowed = self.ALLOWED_FROM[new_status]
        if self._status not in allowed:
            raise InvalidOperationError(
                f"cannot mark {new_status.value}: transaction is {self._status.value}"
            )
        self._status = new_status
        self._updated_at = datetime.now()

    def mark_processing(self):
        self._attempts += 1
        self._transition(TransactionStatus.PROCESSING)
        self._failure_reason = None

    def mark_failed(self, reason):
        reason = ensure_text(reason, "reason")
        self._transition(TransactionStatus.FAILED)
        self._failure_reason = reason

    def mark_completed(self):
        self._transition(TransactionStatus.COMPLETED)

    def mark_cancelled(self):
        self._transition(TransactionStatus.CANCELLED)


class Priority(IntEnum):
    HIGH = 1
    NORMAL = 5
    LOW = 9


class QueueEntry:
    def __init__(self, transaction, priority=Priority.NORMAL, run_at=None):
        if not isinstance(transaction, Transaction):
            raise TypeError(
                f"transaction must be a Transaction, got {type(transaction).__name__}"
            )
        self._transaction = transaction

        if not isinstance(priority, Priority):
            raise TypeError(
                f"priority must be a Priority member, got {priority!r}; try Priority({priority!r})"
            )
        self._priority = priority

        if run_at is not None and not isinstance(run_at, datetime):
            raise TypeError(f"run_at must be a datetime, got {type(run_at).__name__}")
        self._run_at = run_at

    def __repr__(self):
        entry = f"{self._transaction} | {self._priority} | {self._run_at}"

        return f"QueueEntry({entry})"

    @property
    def transaction(self) -> Transaction:
        return self._transaction

    @property
    def priority(self):
        return self._priority

    @property
    def run_at(self):
        return self._run_at

    def is_due(self, now):
        return self._run_at is None or self._run_at <= now


class TransactionQueue:
    def __init__(self):
        self._entries = []

    def add(
        self, transaction, priority=Priority.NORMAL, run_at: datetime | None = None
    ):
        if not isinstance(transaction, Transaction):
            raise TypeError(
                f"transaction must be a Transaction, got {type(transaction).__name__}"
            )

        for entry in self._entries:
            if entry.transaction.transaction_id == transaction.transaction_id:
                raise InvalidOperationError(
                    f"transaction {transaction.transaction_id} already in the queue"
                )

        entry = QueueEntry(transaction, priority, run_at)
        self._entries.append(entry)

    def _next_entry(self, now=None):
        if now is not None and not isinstance(now, datetime):
            raise TypeError(f"now must be a datetime, got {type(now).__name__}")

        now = now or datetime.now()
        due = [
            e
            for e in self._entries
            if e.is_due(now)
            and e.transaction.status
            in (TransactionStatus.PENDING, TransactionStatus.FAILED)
        ]
        if not due:
            return None
        return min(due, key=lambda e: e.priority)

    def pop_next(self, now=None) -> "QueueEntry | None":
        entry = self._next_entry(now)
        if entry is None:
            return None
        self._entries.remove(entry)
        return entry

    def cancel(self, transaction_id):
        transaction_id = ensure_text(transaction_id, "transaction_id")

        for entry in self._entries:
            if entry.transaction.transaction_id == transaction_id:
                entry.transaction.mark_cancelled()
                return

        raise InvalidOperationError(f"transaction {transaction_id} is not in the queue")

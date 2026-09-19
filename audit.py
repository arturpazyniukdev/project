from datetime import datetime
from enum import Enum
from currency import Currency
from risk import RiskLevel
from transactions import TransactionType
from validators import ensure_number, ensure_text
import json


class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AuditLogEntry:
    def __init__(
        self,
        operation,
        sender_id,
        receiver_id,
        amount,
        currency,
        level,
        risk_level,
        risk_reason,
    ) -> None:
        if not isinstance(operation, TransactionType):
            raise TypeError()
        self._operation = operation

        if sender_id is not None:
            self._sender_id = ensure_text(sender_id, "sender_id")
        else:
            self._sender_id = None

        if receiver_id is not None:
            self._receiver_id = ensure_text(receiver_id, "receiver_id")
        else:
            self._receiver_id = None

        self._amount = ensure_number(amount, "amount")

        if not isinstance(currency, Currency):
            raise TypeError()

        self._currency = currency

        if not isinstance(level, AuditLevel):
            raise TypeError()

        self._level = level

        if not isinstance(risk_level, RiskLevel):
            raise TypeError()
        self._risk_level = risk_level

        if not isinstance(risk_reason, str):
            raise TypeError()

        self._risk_reason = risk_reason

        self._at = datetime.now()

    def __repr__(self):
        return f"AuditLogEntry({self.get_info()})"

    def get_info(self):
        return {
            "operation": self._operation.value,
            "sender_id": self._sender_id,
            "receiver_id": self._receiver_id,
            "amount": self._amount,
            "currency": self._currency.value,
            "level": self._level.value,
            "risk_level": self._risk_level.value,
            "risk_reason": self._risk_reason,
            "at": self._at.isoformat(),
        }

    @property
    def risk_level(self):
        return self._risk_level

    @property
    def sender_id(self):
        return self._sender_id

    @property
    def receiver_id(self):
        return self._receiver_id

    @property
    def operation(self):
        return self._operation

    @property
    def level(self):
        return self._level


class AuditLog:
    def __init__(self, path) -> None:
        self._entries: list[AuditLogEntry] = []
        self._path = ensure_text(path, "path")

    def write(
        self,
        operation,
        sender_id,
        receiver_id,
        amount,
        currency,
        level,
        risk_level,
        risk_reason,
    ):
        entry = AuditLogEntry(
            operation,
            sender_id,
            receiver_id,
            amount,
            currency,
            level,
            risk_level,
            risk_reason,
        )
        self._entries.append(entry)

        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.get_info()) + "\n")

    def get_entries(self, risk_level=None, account_id=None, level=None):
        res = []

        if isinstance(risk_level, RiskLevel):
            risk_level = [risk_level]

        if isinstance(account_id, str):
            account_id = [account_id]

        if risk_level is not None and not isinstance(risk_level, list):
            raise TypeError()

        if account_id is not None and not isinstance(account_id, list):
            raise TypeError()

        if level is not None and not isinstance(level, AuditLevel):
            raise TypeError()

        for el in self._entries:
            if risk_level is not None and el.risk_level not in risk_level:
                continue

            if (
                account_id is not None
                and el.sender_id not in account_id
                and el.receiver_id not in account_id
            ):
                continue

            if level is not None and el.level is not level:
                continue

            res.append(el)

        return res

    def get_suspicious_operations(self):
        return [e for e in self._entries if e.risk_level is not RiskLevel.LOW]

    def get_error_stats(self):
        total = 0
        by_operation: dict[TransactionType, int] = {}

        for el in self._entries:
            if el.level is AuditLevel.ERROR:
                total += 1

                if el.operation not in by_operation:
                    by_operation[el.operation] = 1
                else:
                    by_operation[el.operation] += 1

        return {"total": total, "by_operation": by_operation}

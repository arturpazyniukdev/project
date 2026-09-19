from datetime import datetime, timedelta
from enum import Enum

from account import InvalidOperationError
from currency import Currency, convert
from validators import ensure_number, ensure_text


class RiskLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskAnalyzer:
    MAX_AMOUNT = 1000
    MAX_AMOUNT_CURRENCY = Currency.USD
    OPERATIONS_WINDOW = timedelta(minutes=10)
    OPERATIONS_COUNT = 3
    WEIGHT_HIGH = 3
    WEIGHT_MEDIUM = 2
    WEIGHT_LOW = 1
    NIGHT_START_HOUR = 0
    NIGHT_END_HOUR = 5

    def __init__(self) -> None:
        self._assessments = []
        self._interractions: dict[str, set[str]] = {}

    def assess(self, sender_id, receiver_id, amount, currency) -> tuple[RiskLevel, str]:
        if sender_id is None and receiver_id is None:
            raise InvalidOperationError()
        subject_id = ensure_text(sender_id or receiver_id, "subject_id")
        ensure_number(amount, "amount")

        self._assessments.append(
            {"subject_id": subject_id, "amount": amount, "at": datetime.now()}
        )
        is_new_interaction = self._add_interaction(sender_id, receiver_id)

        risk_weight = 0
        reasons = []

        if convert(amount, currency, self.MAX_AMOUNT_CURRENCY) > self.MAX_AMOUNT:
            reasons.append("amount exceeds max amount")
            risk_weight += self.WEIGHT_HIGH
        if self._is_frequent_operations(subject_id):
            reasons.append("frequent operations exceeded")
            risk_weight += self.WEIGHT_HIGH
        if is_new_interaction:
            reasons.append("interaction with new account")
            risk_weight += self.WEIGHT_LOW
        if self.NIGHT_START_HOUR <= datetime.now().hour < self.NIGHT_END_HOUR:
            reasons.append("outside operating hours")
            risk_weight += self.WEIGHT_MEDIUM

        if risk_weight >= self.WEIGHT_HIGH:
            risk = RiskLevel.HIGH
        elif risk_weight >= self.WEIGHT_MEDIUM:
            risk = RiskLevel.MEDIUM
        else:
            risk = RiskLevel.LOW

        return (risk, "; ".join(reasons))

    def _is_frequent_operations(self, account_id):
        cutoff = datetime.now() - self.OPERATIONS_WINDOW

        kept = [
            a
            for a in self._assessments
            if a["subject_id"] == account_id and a["at"] >= cutoff
        ]

        return len(kept) > self.OPERATIONS_COUNT

    def _add_interaction(self, sender_id, receiver_id):
        new_interaction = False
        if sender_id is not None and receiver_id is not None:
            if sender_id not in self._interractions:
                self._interractions[sender_id] = set()

            if receiver_id not in self._interractions[sender_id]:
                new_interaction = True
            self._interractions[sender_id].add(receiver_id)

            if receiver_id not in self._interractions:
                self._interractions[receiver_id] = set()

            if sender_id not in self._interractions[receiver_id]:
                new_interaction = True

            self._interractions[receiver_id].add(sender_id)

        return new_interaction

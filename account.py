from abc import ABC, abstractmethod
from enum import Enum
from uuid import uuid4


class AccountStatus(Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class Currency(Enum):
    USD = "USD"
    RUB = "RUB"
    EUR = "EUR"
    KZT = "KZT"
    CNY = "CNY"


class BankError(Exception):
    pass


class AccountFrozenError(BankError):
    pass


class AccountClosedError(BankError):
    pass


class InvalidOperationError(BankError):
    pass


class InsufficientFundsError(BankError):
    pass


class AbstractAccount(ABC):
    def __init__(
        self,
        owner,
        balance=0,
        currency=Currency.USD,
        status=AccountStatus.ACTIVE,
        account_id=None,
    ):
        if not isinstance(owner, str):
            raise TypeError(f"owner must be a string, got {type(owner).__name__}")

        owner = owner.strip()

        if len(owner) == 0:
            raise ValueError("owner should not be empty")

        self._owner = owner

        if not isinstance(balance, (int, float)) or isinstance(balance, bool):
            raise TypeError(
                f"balance must be an int or float, got {type(balance).__name__}"
            )

        if balance < 0:
            raise ValueError(f"balance cannot be negative, got {balance}")

        self._balance = balance

        if not isinstance(currency, Currency):
            raise TypeError(
                f"currency must be a Currency member, got {currency!r}; try Currency({currency!r})"
            )

        self._currency = currency

        if not isinstance(status, AccountStatus):
            raise TypeError(
                f"status must be a AccountStatus member, got {status!r}; try AccountStatus({status!r})"
            )

        self._status = status

        self._account_id = account_id if account_id is not None else uuid4().hex

    def __str__(self):
        return f"{type(self).__name__} | {self._owner} | {self.short_account_id} | {self._status.value} | {self._balance} {self._currency.value}"

    @property
    def account_id(self):
        return self._account_id

    @property
    def short_account_id(self):
        return self._account_id[-4:]

    @property
    def owner(self):
        return self._owner

    @property
    def balance(self):
        return self._balance

    @property
    def currency(self):
        return self._currency

    @property
    def status(self):
        return self._status

    @abstractmethod
    def get_account_info(self):
        pass

    @abstractmethod
    def deposit(self, amount):
        pass

    @abstractmethod
    def withdraw(self, amount):
        pass

    def _ensure_active(self, operation):
        if self._status is AccountStatus.ACTIVE:
            return
        if self._status is AccountStatus.FROZEN:
            raise AccountFrozenError(
                f"cannot {operation}: account is {self._status.value}"
            )
        raise AccountClosedError(f"cannot {operation}: account is {self._status.value}")

    def _validate_amount(self, amount):
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError(
                f"amount must be an int or float, got {type(amount).__name__}"
            )

        if amount <= 0:
            raise InvalidOperationError(f"amount must be positive, got {amount}")


class BankAccount(AbstractAccount):
    def get_account_info(self):
        info = {
            "account_id": self.account_id,
            "owner": self.owner,
            "balance": self.balance,
            "currency": self.currency.value,
            "status": self.status.value,
        }

        return info

    def deposit(self, amount):
        self._ensure_active("deposit")
        self._validate_amount(amount)
        self._balance += amount

    def withdraw(self, amount):
        self._ensure_active("withdraw")
        self._validate_amount(amount)

        if self._balance < amount:
            raise InsufficientFundsError(
                f"cannot withdraw {amount}, balance is only {self._balance}"
            )

        self._balance -= amount


class SavingsAccount(BankAccount):
    def __init__(
        self,
        owner,
        balance=0,
        currency=Currency.USD,
        status=AccountStatus.ACTIVE,
        account_id=None,
        min_balance=0,
        monthly_rate=0.01,
    ):
        super().__init__(owner, balance, currency, status, account_id)

        if not isinstance(min_balance, (int, float)) or isinstance(min_balance, bool):
            raise TypeError(
                f"min_balance must be an int or float, got {type(min_balance).__name__}"
            )

        if min_balance < 0:
            raise ValueError(f"min_balance cannot be negative, got {min_balance}")

        self._min_balance = min_balance

        if not isinstance(monthly_rate, (int, float)) or isinstance(monthly_rate, bool):
            raise TypeError(
                f"monthly_rate must be an int or float, got {type(monthly_rate).__name__}"
            )

        if monthly_rate < 0:
            raise ValueError(f"monthly_rate cannot be negative, got {monthly_rate}")

        self._monthly_rate = monthly_rate

    def __str__(self):
        return (
            f"{super().__str__()} | min {self._min_balance} | rate {self._monthly_rate}"
        )

    def get_account_info(self):
        return {
            **super().get_account_info(),
            "min_balance": self._min_balance,
            "monthly_rate": self._monthly_rate,
        }

    def withdraw(self, amount):
        self._ensure_active("withdraw")
        self._validate_amount(amount)

        if self._balance - amount < self._min_balance:
            raise InsufficientFundsError(
                f"cannot withdraw {amount}: balance {self._balance} would drop below min {self._min_balance}"
            )

        return super().withdraw(amount)

    def apply_monthly_interest(self):
        interest = round(self._balance * self._monthly_rate, 2)
        self._balance = self._balance + interest
        return interest


class PremiumAccount(BankAccount):
    def __init__(
        self,
        owner,
        balance=0,
        currency=Currency.USD,
        status=AccountStatus.ACTIVE,
        account_id=None,
        max_withdrawal=None,
        overdraft_limit=0,
        withdrawal_fee=0,
    ):
        super().__init__(owner, balance, currency, status, account_id)

        if max_withdrawal is not None:
            if not isinstance(max_withdrawal, (int, float)) or isinstance(
                max_withdrawal, bool
            ):
                raise TypeError(
                    f"max_withdrawal must be an int or float, got {type(max_withdrawal).__name__}"
                )
            if max_withdrawal <= 0:
                raise ValueError(
                    f"max_withdrawal should be positive, got {max_withdrawal}"
                )

        self._max_withdrawal = max_withdrawal

        if not isinstance(overdraft_limit, (int, float)) or isinstance(
            overdraft_limit, bool
        ):
            raise TypeError(
                f"overdraft_limit must be an int or float, got {type(overdraft_limit).__name__}"
            )

        if overdraft_limit < 0:
            raise ValueError(
                f"overdraft_limit cannot be negative, got {overdraft_limit}"
            )

        self._overdraft_limit = overdraft_limit

        if not isinstance(withdrawal_fee, (int, float)) or isinstance(
            withdrawal_fee, bool
        ):
            raise TypeError(
                f"withdrawal_fee must be an int or float, got {type(withdrawal_fee).__name__}"
            )

        if withdrawal_fee < 0:
            raise ValueError(f"withdrawal_fee cannot be negative, got {withdrawal_fee}")

        self._withdrawal_fee = withdrawal_fee

    def withdraw(self, amount):
        self._validate_amount(amount)
        self._ensure_active("withdraw")

        if self._max_withdrawal is not None and amount > self._max_withdrawal:
            raise InvalidOperationError(
                f"cannot withdraw more than max_withdrawal {self._max_withdrawal}"
            )

        corrected_amount = amount + self._withdrawal_fee

        if self._balance - corrected_amount < -self._overdraft_limit:
            raise InsufficientFundsError(
                f"cannot withdraw {amount}: balance {self._balance} would drop below overdraft_limit {self._overdraft_limit}"
            )

        self._balance -= corrected_amount

    def get_account_info(self):
        return {
            **super().get_account_info(),
            "withdrawal_fee": self._withdrawal_fee,
            "overdraft_limit": self._overdraft_limit,
            "max_withdrawal": self._max_withdrawal
        }

    def __str__(self):
        return f"{super().__str__()} | withdrawal_fee {self._withdrawal_fee} | overdraft_limit {self._overdraft_limit} | max_withdrawal {self._max_withdrawal}"


class InvestmentAccount(BankAccount):
    ASSET_TYPES = ("stocks", "bonds", "etf")

    def __init__(
        self,
        owner,
        balance=0,
        currency=Currency.USD,
        status=AccountStatus.ACTIVE,
        account_id=None,
    ):
        super().__init__(owner, balance, currency, status, account_id)

        self._portfolio = {asset: 0 for asset in self.ASSET_TYPES}

    def invest(self, amount, asset_type):
        self._ensure_active("invest")
        self._validate_amount(amount)

        if asset_type not in self.ASSET_TYPES:
            raise InvalidOperationError(
                f"asset_type must be {self.ASSET_TYPES}, got {asset_type}"
            )

        if amount > self._balance:
            raise InsufficientFundsError(
                f"amount {amount} is more than balance {self._balance}"
            )

        self._portfolio[asset_type] += amount
        self._balance -= amount

    def project_yearly_growth(self, growth_rates):
        if not isinstance(growth_rates, dict):
            raise TypeError(
                f"growth_rates must be dict, got {type(growth_rates).__name__}"
            )

        for key, rate in growth_rates.items():
            if key not in self.ASSET_TYPES:
                raise InvalidOperationError(
                    f"asset_type must be {self.ASSET_TYPES}, got {key}"
                )

            if not isinstance(rate, (int, float)) or isinstance(rate, bool):
                raise TypeError(
                    f"value should be int or float, got {type(rate).__name__}"
                )

        by_asset = {}
        total = 0

        for key in growth_rates.keys():
            growth = round(self._portfolio[key] * growth_rates[key],2 )
            by_asset[key] = growth
            total += growth

        return {"by_asset": by_asset, "total": round(total,2)}

    def withdraw(self, amount):
        super().withdraw(amount)

    def get_account_info(self):
        return {**super().get_account_info(), "portfolio": dict(self._portfolio)}

    def __str__(self):
        return f"{super().__str__()} | portfolio {self._portfolio}"
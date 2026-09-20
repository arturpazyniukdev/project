from uuid import uuid4
from enum import Enum

from datetime import date

from account import (
    AbstractAccount,
    AccountStatus,
    AuthenticationError,
    BankAccount,
    InvalidOperationError,
    RiskBlockedError,
)
from audit import AuditLevel, AuditLog
from currency import Currency, convert
from risk import RiskAnalyzer, RiskLevel
from transactions import TransactionType
from validators import ensure_number, ensure_text


class ClientStatus(Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"


class Client:
    def __init__(
        self,
        full_name,
        birth_date,
        pin,
        status=ClientStatus.ACTIVE,
        client_id=None,
        phone=None,
        email=None,
    ):
        if not isinstance(full_name, str):
            raise TypeError(
                f"full_name must be a string, got {type(full_name).__name__}"
            )

        full_name = full_name.strip()

        if len(full_name) == 0:
            raise ValueError("full_name should not be empty")

        self._full_name = full_name

        if client_id is None:
            self._client_id = uuid4().hex
        else:
            if not isinstance(client_id, str):
                raise TypeError(
                    f"client_id must be a string, got {type(client_id).__name__}"
                )

            client_id = client_id.strip()

            if len(client_id) == 0:
                raise ValueError("client_id should not be empty")

            self._client_id = client_id

        if not isinstance(status, ClientStatus):
            raise TypeError(
                f"status must be a ClientStatus member, got {status!r}; try ClientStatus({status!r})"
            )

        self._status = status
        self._account_ids = []

        if phone is not None:
            if not isinstance(phone, str):
                raise TypeError(f"phone must be a string, got {type(phone).__name__}")

            phone = phone.strip()

            if len(phone) == 0:
                raise ValueError("phone should not be empty")

        self._phone = phone

        if email is not None:
            if not isinstance(email, str):
                raise TypeError(f"email must be a string, got {type(email).__name__}")

            email = email.strip()

            if "@" not in email:
                raise ValueError(f"@ sign must be present in email, got {email}")

        self._email = email

        if not isinstance(birth_date, date):
            raise TypeError(
                f"birth_date must be a date, got {type(birth_date).__name__}"
            )

        self._birth_date = birth_date

        if self.age < 18:
            raise ValueError(f"client must be at least 18, got {self.age}")

        if not isinstance(pin, str):
            raise TypeError(f"pin must be a string, got {type(pin).__name__}")

        if not len(pin) == 4 or not pin.isdigit():
            raise ValueError("pin must be 4 digits")

        self._pin = pin

        self._failed_attempts = 0

    @property
    def age(self):
        today = date.today()
        bd = self._birth_date
        years = today.year - bd.year
        if (today.month, today.day) < (bd.month, bd.day):
            years -= 1
        return years

    @property
    def client_id(self):
        return self._client_id

    @property
    def full_name(self):
        return self._full_name

    @property
    def status(self):
        return self._status

    @property
    def phone(self):
        return self._phone

    @property
    def email(self):
        return self._email

    @property
    def birth_date(self):
        return self._birth_date

    @property
    def account_ids(self):
        return list(self._account_ids)

    def add_account(self, account_id):
        if not isinstance(account_id, str):
            raise TypeError(
                f"account_id must be a string, got {type(account_id).__name__}"
            )

        self._account_ids.append(account_id)

    def check_pin(self, pin):
        if not isinstance(pin, str):
            raise TypeError(f"pin must be a string, got {type(pin).__name__}")

        return self._pin == pin

    def register_failed_attempt(self):
        self._failed_attempts += 1
        if self._failed_attempts >= 3:
            self.block()

    def reset_failed_attempts(self):
        self._failed_attempts = 0

    def block(self):
        self._status = ClientStatus.BLOCKED

    def is_active(self):
        return self._status is ClientStatus.ACTIVE


class Bank:
    LARGE_WITHDRAWAL = 10000
    AUDIT_LEVEL_BY_RISK = {
        RiskLevel.HIGH: AuditLevel.ERROR,
        RiskLevel.MEDIUM: AuditLevel.WARNING,
        RiskLevel.LOW: AuditLevel.INFO,
    }

    def __init__(self, risk_analyzer, audit_log):
        if not isinstance(risk_analyzer, RiskAnalyzer):
            raise TypeError(
                f"risk_analyzer must be a RiskAnalyzer, got {type(risk_analyzer).__name__}"
            )

        self._risk_analyzer = risk_analyzer

        if not isinstance(audit_log, AuditLog):
            raise TypeError(
                f"audit_log must be an AuditLog, got {type(audit_log).__name__}"
            )

        self._audit_log = audit_log

        self._clients: dict[str, Client] = {}
        self._accounts: dict[str, BankAccount] = {}

    def add_client(self, client):
        if not isinstance(client, Client):
            raise TypeError(f"client must be a Client, got {type(client).__name__}")

        if client.client_id in self._clients:
            raise InvalidOperationError(
                f"client {client.client_id} already exists in the bank"
            )

        self._clients[client.client_id] = client

    def open_account(self, client_id, account):
        client = self.get_client(client_id)

        if not isinstance(account, AbstractAccount):
            raise TypeError(
                f"account must be an AbstractAccount, got {type(account).__name__}"
            )

        if account.account_id in self._accounts:
            raise InvalidOperationError(
                f"account {account.account_id} already exists in the bank"
            )

        if account.client_id != client_id:
            raise InvalidOperationError("account does not belong to client")

        self._accounts[account.account_id] = account

        client.add_account(account.account_id)

    def close_account(self, account_id):
        account = self._get_account(account_id)
        account.close()

    def freeze_account(self, account_id):
        account = self._get_account(account_id)
        account.freeze()

    def unfreeze_account(self, account_id):
        account = self._get_account(account_id)
        account.unfreeze()

    def _get_account(self, account_id) -> BankAccount:
        if account_id not in self._accounts:
            raise InvalidOperationError(f"account {account_id} does not exist")

        return self._accounts[account_id]

    def get_client(self, client_id) -> Client:
        if client_id not in self._clients:
            raise InvalidOperationError(
                f"client {client_id} does not exist in the bank"
            )

        return self._clients[client_id]

    def ensure_can_deposit(self, account_id, amount):
        ensure_number(amount, "amount")
        account = self._get_account(account_id)
        account.ensure_can_deposit(amount)

    def ensure_can_withdraw(self, account_id, amount):
        ensure_number(amount, "amount")
        account = self._get_account(account_id)
        account.ensure_can_withdraw(amount)

    def _do_deposit(self, account_id, amount):
        self.ensure_can_deposit(account_id, amount)
        account = self._get_account(account_id)
        account.deposit(amount)

    def deposit(self, account_id, amount):
        account = self._get_account(account_id)
        risk_level, risk_reason = self._risk_analyzer.assess(
            None, account_id, amount, account.currency
        )

        self._audit_log.write(
            TransactionType.DEPOSIT,
            None,
            account_id,
            amount,
            account.currency,
            self.AUDIT_LEVEL_BY_RISK[risk_level],
            risk_level,
            risk_reason,
        )

        if risk_level is RiskLevel.HIGH:
            raise RiskBlockedError(f"cannot deposit: blocked by risk ({risk_reason})")

        self._do_deposit(account_id, amount)

    def _do_withdraw(self, account_id, amount):
        self.ensure_can_withdraw(account_id, amount)
        account = self._get_account(account_id)
        account.withdraw(amount)

    def withdraw(self, account_id, amount):
        account = self._get_account(account_id)

        risk_level, risk_reason = self._risk_analyzer.assess(
            account_id, None, amount, account.currency
        )

        self._audit_log.write(
            TransactionType.WITHDRAWAL,
            account_id,
            None,
            amount,
            account.currency,
            self.AUDIT_LEVEL_BY_RISK[risk_level],
            risk_level,
            risk_reason,
        )

        if risk_level is RiskLevel.HIGH:
            raise RiskBlockedError(f"cannot withdraw: blocked by risk ({risk_reason})")

        self._do_withdraw(account_id, amount)

    def transfer(self, sender_id, receiver_id, withdrawn_amount, deposited_amount):
        currency = self._get_account(sender_id).currency
        risk_level, risk_reason = self._risk_analyzer.assess(
            sender_id, receiver_id, withdrawn_amount, currency
        )

        self._audit_log.write(
            TransactionType.TRANSFER,
            sender_id,
            receiver_id,
            withdrawn_amount,
            currency,
            self.AUDIT_LEVEL_BY_RISK[risk_level],
            risk_level,
            risk_reason,
        )

        if risk_level is RiskLevel.HIGH:
            raise RiskBlockedError(f"cannot transfer: blocked by risk ({risk_reason})")

        self.ensure_can_withdraw(sender_id, withdrawn_amount)
        self.ensure_can_deposit(receiver_id, deposited_amount)
        self._do_withdraw(sender_id, withdrawn_amount)
        self._do_deposit(receiver_id, deposited_amount)

    def authenticate_client(self, client_id, pin):
        client = self.get_client(client_id)

        if not client.is_active():
            raise AuthenticationError("non active clients cannot login")

        pin_ok = client.check_pin(pin)

        if pin_ok:
            client.reset_failed_attempts()
            return
        else:
            client.register_failed_attempt()
            raise AuthenticationError(f"wrong pin for client {client_id}")

    def search_accounts(self, query=None, status=None, account_type=None):
        if query is not None:
            if not isinstance(query, str):
                raise TypeError(f"query must be a string, got {type(query).__name__}")

        if status is not None:
            if not isinstance(status, AccountStatus):
                raise TypeError(
                    f"status must be a AccountStatus member, got {status!r}; try AccountStatus({status!r})"
                )

        if account_type is not None:
            if not isinstance(account_type, type) or not issubclass(
                account_type, AbstractAccount
            ):
                raise TypeError(
                    f"account_type must be an AbstractAccount subclass, got {account_type!r}"
                )

        result = []
        for account in self._accounts.values():
            if query is not None:
                q = query.lower()
                if (
                    q not in account.account_id.lower()
                    and q not in account.client_id.lower()
                ):
                    continue

            if status is not None and account.status is not status:
                continue

            if account_type is not None and not isinstance(account, account_type):
                continue

            result.append(account.get_account_info())

        return result

    def get_accounts(self):
        return list(self._accounts.values())

    def get_clients(self):
        return list(self._clients.values())

    def get_client_account_ids(self, client_id):
        client_id = ensure_text(client_id, "client_id")
        client = self.get_client(client_id)
        return client.account_ids

    def get_client_risk_profile(self, client_id):
        client_id = ensure_text(client_id, "client_id")

        return self._audit_log.get_entries(
            [RiskLevel.HIGH, RiskLevel.MEDIUM], self.get_client_account_ids(client_id)
        )

    def get_total_balance(self, currency=Currency.USD):
        if not isinstance(currency, Currency):
            raise TypeError(
                f"currency must be a Currency member, got {currency!r}; try Currency({currency!r})"
            )
        result = sum(
            convert(account.balance, account.currency, currency)
            for account in self._accounts.values()
            if account.status is not AccountStatus.CLOSED
        )
        return round(result, 2)

    def get_clients_ranking(self, currency=Currency.USD):
        res = []

        for client in self._clients.values():
            s = 0
            for account_id in client.account_ids:
                account = self._get_account(account_id)
                if account.status is not AccountStatus.CLOSED:
                    s += round(convert(account.balance, account.currency, currency), 2)
            res.append((client.full_name, s))

        return sorted(res, key=lambda pair: pair[1], reverse=True)

    def get_account(self, account_id):
        return self._get_account(account_id)

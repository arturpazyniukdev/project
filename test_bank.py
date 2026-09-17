from datetime import date, datetime
from bank import Bank, Client
from helpers import expect_error
from account import (
    AccountClosedError,
    AccountFrozenError,
    AuthenticationError,
    BankAccount,
    InsufficientFundsError,
    InvalidOperationError,
    InvestmentAccount,
    SavingsAccount,
    PremiumAccount,
)
from unittest.mock import patch
import bank as bank_module


class NightClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 1, 1, 2, 30)

bank = Bank()


# wrong args
expect_error("empty name", lambda: Client("", date(2005, 2, 22), "1234"), ValueError)
expect_error(
    "younger than 18", lambda: Client("Ivan", date(2015, 2, 22), "1234"), ValueError
)
expect_error(
    "pin too short", lambda: Client("Ivan", date(2005, 2, 22), "12"), ValueError
)
expect_error(
    "wrong pin type", lambda: Client("Ivan", date(2005, 2, 22), "a"), ValueError
)
expect_error(
    "wrong status", lambda: Client("Ivan", date(2005, 2, 22), "1234", "sss"), TypeError
)
expect_error(
    "wrong phone",
    lambda: Client("Ivan", date(2005, 2, 22), "1234", phone=123),
    TypeError,
)
expect_error(
    "wrong email",
    lambda: Client("Ivan", date(2005, 2, 22), "1234", email="123"),
    ValueError,
)

artur = Client("Artur", date(1997, 9, 16), "1234")
maria = Client("Maria", date(1997, 9, 16), "1234")
ivan = Client("Ivan", date(1997, 9, 16), "1234")

bank.add_client(artur)
expect_error("already exists", lambda: bank.add_client(artur))
expect_error("not a client", lambda: bank.add_client("artur"), TypeError)
artur_bank_account = BankAccount(artur.full_name, 900)
bank.open_account(artur.client_id, artur_bank_account)
expect_error(
    "client not in bank",
    lambda: bank.open_account(maria.client_id, BankAccount(maria.full_name, 0)),
    InvalidOperationError,
)

bank.deposit(artur_bank_account.account_id, 50)
print(artur_bank_account.balance)

bank.add_client(maria)
maria_saving_account = SavingsAccount(maria.full_name, 500)
bank.open_account(maria.client_id, maria_saving_account)
expect_error(
    "same account open twice",
    lambda: bank.open_account(maria.client_id, maria_saving_account),
    InvalidOperationError,
)
expect_error(
    "wrong account", lambda: bank.open_account(maria.client_id, "nope"), TypeError
)

bank.add_client(ivan)
ivan_investment_account = InvestmentAccount(ivan.full_name, 300)
bank.open_account(ivan.client_id, ivan_investment_account)

print("total: ", bank.get_total_balance())

expect_error(
    "wrong pin",
    lambda: bank.authenticate_client(artur.client_id, "123"),
    AuthenticationError,
)
expect_error(
    "wrong pin",
    lambda: bank.authenticate_client(artur.client_id, "123"),
    AuthenticationError,
)
print(artur.is_active())
bank.authenticate_client(artur.client_id, "1234")
expect_error(
    "wrong pin",
    lambda: bank.authenticate_client(artur.client_id, "123"),
    AuthenticationError,
)
expect_error(
    "wrong pin",
    lambda: bank.authenticate_client(artur.client_id, "123"),
    AuthenticationError,
)
print(artur.is_active())
expect_error(
    "third fail blocks",
    lambda: bank.authenticate_client(artur.client_id, "123"),
    AuthenticationError,
)
print(artur.is_active())   
expect_error(
    "non active clients cannot login",
    lambda: bank.authenticate_client(artur.client_id, "123"),
    AuthenticationError,
)

bank.authenticate_client(maria.client_id, "1234")
bank.freeze_account(maria_saving_account.account_id)
expect_error(
    "deposit to frozen",
    lambda: bank.deposit(maria_saving_account.account_id, 20),
    AccountFrozenError,
)
expect_error(
    "already frozen",
    lambda: bank.freeze_account(maria_saving_account.account_id),
    InvalidOperationError,
)
bank.unfreeze_account(maria_saving_account.account_id)
bank.deposit(maria_saving_account.account_id, 20)
expect_error(
    "unfreeze active",
    lambda: bank.unfreeze_account(maria_saving_account.account_id),
    InvalidOperationError,
)
bank.close_account(maria_saving_account.account_id)
expect_error(
    "already closed",
    lambda: bank.close_account(maria_saving_account.account_id),
    AccountClosedError,
)
expect_error(
    "cannot freeze closed",
    lambda: bank.freeze_account(maria_saving_account.account_id),
    AccountClosedError,
)

print(bank.search_accounts(query="art"))
print(bank.get_clients_ranking())
expect_error(
    "insufficient funds",
    lambda: bank.withdraw(ivan_investment_account.account_id, 10000),
    InsufficientFundsError,
)
print(bank.get_suspicious_events())

maria_premium_account = PremiumAccount(maria.full_name, 200)
bank.open_account(maria.client_id, maria_premium_account)

with patch.object(bank_module, "datetime", NightClock):
    expect_error("deposit at night", lambda: bank.deposit(artur_bank_account.account_id, 10), InvalidOperationError)
    expect_error("withdraw at night", lambda: bank.withdraw(artur_bank_account.account_id, 10), InvalidOperationError)

print(artur_bank_account.balance)
bank.deposit(artur_bank_account.account_id, 10)
print(bank.get_suspicious_events())
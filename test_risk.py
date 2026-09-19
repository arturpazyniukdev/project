from datetime import date, datetime
from unittest.mock import patch
from account import BankAccount
from audit import AuditLevel, AuditLog
from bank import Bank, Client
import risk as risk_module
from helpers import expect_error
from risk import RiskAnalyzer, RiskLevel


class NightClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 1, 1, 2, 30)


risk_analyzer = RiskAnalyzer()
audit_log = AuditLog("audit.jsonl")
bank = Bank(risk_analyzer, audit_log)
print(bank.get_total_balance())

artur = Client("Artur", date(1997, 2, 1), "1234")
artur_account = BankAccount(artur.client_id, 100)
bank.add_client(artur)
bank.open_account(artur.client_id, artur_account)

maria = Client("Artur", date(1997, 2, 1), "1234")
maria_account = BankAccount(maria.client_id, 100)
bank.add_client(maria)
bank.open_account(maria.client_id, maria_account)

with patch.object(risk_module, "datetime", NightClock):
    bank.deposit(maria_account.account_id, 250)
    expect_error(
        "new interraction and outside working hours",
        lambda: bank.transfer(maria_account.account_id, artur_account.account_id, 100, 100),
    )
    
expect_error("high risk deposit", lambda: bank.deposit(artur_account.account_id, 1001))
expect_error("high risk deposit", lambda: bank.deposit(artur_account.account_id, 1001))
bank.deposit(artur_account.account_id, 1000)
expect_error(
    "frequent operations exceeeded",
    lambda: bank.deposit(artur_account.account_id, 1000),
)




print("---suspicious ops---")
print(audit_log.get_suspicious_operations())
print("---client risk profile---")
print(bank.get_client_risk_profile(artur.client_id))
print("---errors---")
print(audit_log.get_error_stats())

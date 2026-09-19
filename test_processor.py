from datetime import date, datetime, timedelta
from time import sleep
from account import BankAccount, PremiumAccount
from audit import AuditLog
from bank import Bank, Client
from currency import Currency
from processor import TransactionProcessor
from risk import RiskAnalyzer
from transactions import Priority, Transaction, TransactionQueue, TransactionType

queue = TransactionQueue()
bank = Bank(RiskAnalyzer(), AuditLog("audit.jsonl"))
processor = TransactionProcessor(bank)

artur = Client("Artur", date(1997, 3, 1), "1234")
arturs_account = BankAccount(artur.client_id, 100, Currency.USD)
artur.add_account(arturs_account.account_id)
bank.add_client(artur)
bank.open_account(artur.client_id, arturs_account)

maria = Client("Maria", date(1992, 2, 6), "1234")
marias_account = PremiumAccount(
    maria.client_id, 100, Currency.USD, overdraft_limit=1000
)
bank.add_client(maria)
bank.open_account(maria.client_id, marias_account)


t1 = Transaction(
    100, Currency.USD, TransactionType.DEPOSIT, None, arturs_account.account_id
)
t2 = Transaction(
    100, Currency.USD, TransactionType.WITHDRAWAL, arturs_account.account_id
)
t3 = Transaction(
    50,
    Currency.USD,
    TransactionType.TRANSFER,
    arturs_account.account_id,
    marias_account.account_id,
)
t4 = Transaction(
    100,
    Currency.KZT,
    TransactionType.EXTERNAL_TRANSFER,
    arturs_account.account_id,
    "external_account",
    fee=1,
)
t5 = Transaction(
    100, Currency.USD, TransactionType.WITHDRAWAL, arturs_account.account_id
)
t6 = Transaction(
    100, Currency.USD, TransactionType.DEPOSIT, None, arturs_account.account_id
)
t7 = Transaction(
    200, Currency.USD, TransactionType.WITHDRAWAL, arturs_account.account_id
)
t8 = Transaction(
    100, Currency.EUR, TransactionType.DEPOSIT, None, arturs_account.account_id
)
t9 = Transaction(
    600, Currency.USD, TransactionType.WITHDRAWAL, marias_account.account_id
)
t10 = Transaction(
    100, Currency.USD, TransactionType.DEPOSIT, None, arturs_account.account_id
)

queue.add(t1)
queue.add(t2)
queue.add(t3, run_at=datetime.now() + timedelta(seconds=1))
queue.add(t4, Priority.LOW)
queue.add(t5, Priority.HIGH)
queue.add(t6)
queue.add(t7)
queue.add(t8, run_at=datetime.now() + timedelta(seconds=2))
queue.cancel(t8.transaction_id)
queue.add(t9)
queue.add(t10)

processor.process_all(queue)
sleep(3)
processor.process_all(queue)
print("errors: ", processor.get_errors())

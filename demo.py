from datetime import date, timedelta, datetime
from account import BankAccount, SavingsAccount
from audit import AuditLog
from bank import Bank, Client
from currency import Currency
from processor import TransactionProcessor
from risk import RiskAnalyzer, RiskLevel
from transactions import Priority, Transaction, TransactionQueue, TransactionType

audit_log = AuditLog("log.json")
bank = Bank(RiskAnalyzer(), audit_log)
queue = TransactionQueue()
processor = TransactionProcessor(bank)

artur = Client("Artur", date(1997, 1, 16), "1234")
artur_account = BankAccount(artur.client_id, 100)
artur_account_2 = SavingsAccount(artur.client_id, 100)
bank.add_client(artur)
bank.open_account(artur.client_id, artur_account)
bank.open_account(artur.client_id, artur_account_2)

ivan = Client("Ivan", date(1997, 1, 16), "1234")
ivan_account = BankAccount(ivan.client_id, 100)
ivan_account_2 = SavingsAccount(ivan.client_id, 100)
bank.add_client(ivan)
bank.open_account(ivan.client_id, ivan_account)
bank.open_account(ivan.client_id, ivan_account_2)

maria = Client("Maria", date(1997, 1, 16), "1234")
maria_account = BankAccount(maria.client_id, 100)
maria_account_2 = SavingsAccount(maria.client_id, 100)
bank.add_client(maria)
bank.open_account(maria.client_id, maria_account)
bank.open_account(maria.client_id, maria_account_2)

stas = Client("Stas", date(1997, 1, 16), "1234")
stas_account = BankAccount(stas.client_id, 100)
stas_account_2 = SavingsAccount(stas.client_id, 100)
bank.add_client(stas)
bank.open_account(stas.client_id, stas_account)
bank.open_account(stas.client_id, stas_account_2)

nastya = Client("nastya", date(1997, 1, 16), "1234")
nastya_account = BankAccount(nastya.client_id, 100)
nastya_account_2 = SavingsAccount(nastya.client_id, 100)
bank.add_client(nastya)
bank.open_account(nastya.client_id, nastya_account)
bank.open_account(nastya.client_id, nastya_account_2)

oleg = Client("Oleg", date(1997, 1, 16), "1234")
oleg_account = BankAccount(oleg.client_id, 100)
oleg_account_2 = BankAccount(oleg.client_id, 100)
bank.add_client(oleg)
bank.open_account(oleg.client_id, oleg_account)
bank.open_account(oleg.client_id, oleg_account_2)
bank.freeze_account(oleg_account.account_id)
bank.close_account(oleg_account_2.account_id)

transactions = [
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": artur_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": artur_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 50,
            "currency": Currency.USD,
            "transaction_type": TransactionType.TRANSFER,
            "sender_id": artur_account.account_id,
            "receiver_id": maria_account.account_id,
        },
        "run_at": datetime.now() + timedelta(seconds=1),
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.KZT,
            "transaction_type": TransactionType.EXTERNAL_TRANSFER,
            "sender_id": artur_account.account_id,
            "receiver_id": "external_account",
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": artur_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": artur_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 200,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": artur_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.EUR,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": artur_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 600,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": maria_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": artur_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 200,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": ivan_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 50,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": ivan_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.TRANSFER,
            "sender_id": ivan_account.account_id,
            "receiver_id": ivan_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 300,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": ivan_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": ivan_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 500,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": stas_account.account_id,
        },
        "priority": Priority.HIGH,
    },
    {
        "tx": {
            "amount": 200,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": stas_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.TRANSFER,
            "sender_id": stas_account.account_id,
            "receiver_id": stas_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 400,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": nastya_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 150,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": nastya_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 250,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": nastya_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 300,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": maria_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": maria_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 50,
            "currency": Currency.USD,
            "transaction_type": TransactionType.TRANSFER,
            "sender_id": maria_account_2.account_id,
            "receiver_id": nastya_account_2.account_id,
        },
        "run_at": datetime.now() + timedelta(seconds=1),
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": "ghost_account_1",
        }
    },
    {
        "tx": {
            "amount": 50,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": "ghost_account_2",
        }
    },
    {
        "tx": {
            "amount": 50,
            "currency": Currency.USD,
            "transaction_type": TransactionType.TRANSFER,
            "sender_id": stas_account_2.account_id,
            "receiver_id": "ghost_account_3",
        }
    },
    {
        "tx": {
            "amount": 5000,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": artur_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 100,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": oleg_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 50,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": oleg_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 1500,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": ivan_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 2000,
            "currency": Currency.USD,
            "transaction_type": TransactionType.WITHDRAWAL,
            "sender_id": stas_account.account_id,
        }
    },
    {
        "tx": {
            "amount": 1200,
            "currency": Currency.USD,
            "transaction_type": TransactionType.TRANSFER,
            "sender_id": nastya_account.account_id,
            "receiver_id": stas_account_2.account_id,
        },
        "priority": Priority.HIGH,
    },
    {
        "tx": {
            "amount": 60,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": nastya_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 60,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": nastya_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 60,
            "currency": Currency.USD,
            "transaction_type": TransactionType.DEPOSIT,
            "receiver_id": nastya_account_2.account_id,
        }
    },
    {
        "tx": {
            "amount": 80,
            "currency": Currency.USD,
            "transaction_type": TransactionType.TRANSFER,
            "sender_id": ivan_account.account_id,
            "receiver_id": nastya_account.account_id,
        }
    },
]

for el in transactions:
    t = Transaction(**el["tx"])
    priority = el.get("priority", Priority.NORMAL)
    run_at = el.get("run_at")
    queue.add(
        t,
        priority,
        run_at,
    )
    print("queue entry added: ", t, priority, run_at)

processor.process_all(queue)


print("---accounts---")
for account_id in artur.account_ids:
    print(bank.get_account(account_id))
print("---history---")
print(audit_log.get_entries(account_id=artur.account_ids))
print("---suspicious---")
print(
    audit_log.get_entries(
        risk_level=[RiskLevel.HIGH, RiskLevel.MEDIUM], account_id=artur.account_ids
    )
)
print("---top 3 clients---")
print(bank.get_clients_ranking()[:3])
print("---statistics---")
print(processor.get_stats())
print("---total balance---")
print(bank.get_total_balance())

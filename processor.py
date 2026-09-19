from datetime import datetime, timedelta
from account import BankError, InvalidOperationError
from bank import Bank
from currency import Currency, convert
from transactions import QueueEntry, Transaction, TransactionQueue, TransactionType
from validators import ensure_text


class TransactionProcessor:
    FEE_RATES = {TransactionType.EXTERNAL_TRANSFER: 0.02}
    MAX_ATTEMPTS = 3

    def __init__(self, bank):
        if not isinstance(bank, Bank):
            raise TypeError(f"bank must be a Bank, got {type(bank).__name__}")

        self._bank = bank
        self._errors = []
        self._processed: list[Transaction] = []

    def _calculate_fee(self, transaction):
        if not isinstance(transaction, Transaction):
            raise TypeError(
                f"transaction must be a Transaction, got {type(transaction).__name__}"
            )

        rate = self.FEE_RATES.get(transaction.transaction_type, 0)
        return round(transaction.fee + transaction.amount * rate, 2)

    def _log_error(self, transaction, reason):
        if not isinstance(transaction, Transaction):
            raise TypeError(
                f"transaction must be a Transaction, got {type(transaction).__name__}"
            )

        reason = ensure_text(reason, "reason")

        self._errors.append(
            {
                "transaction_id": transaction.transaction_id,
                "reason": reason,
                "at": datetime.now(),
            }
        )

    def get_errors(self):
        return list(self._errors)

    def get_stats(self, currency=Currency.USD):
        if not isinstance(currency, Currency):
            raise TypeError(
                f"currency must be a Currency member, got {currency!r}; try Currency({currency!r})"
            )

        total = 0
        by_type = {}
        by_status = {}
        volume = 0

        for el in self._processed:
            total += 1
            volume += convert(el.amount, el.currency, currency)
            if el.transaction_type in by_type:
                by_type[el.transaction_type] += 1
            else:
                by_type[el.transaction_type] = 1

            if el.status in by_status:
                by_status[el.status] += 1
            else:
                by_status[el.status] = 1

        return {
            "total": total,
            "by_type": by_type,
            "by_status": by_status,
            "volume": round(volume, 2),
        }

    def process_all(self, queue):
        if not isinstance(queue, TransactionQueue):
            raise TypeError(
                f"queue must be a TransactionQueue, got {type(queue).__name__}"
            )

        entry = queue.pop_next()
        while entry is not None:
            success = self._process_entry(entry)
            attempts = entry.transaction.attempts
            if not success and attempts < self.MAX_ATTEMPTS:
                queue.add(
                    entry.transaction,
                    entry.priority,
                    datetime.now() + timedelta(milliseconds=500 * attempts),
                )
            entry = queue.pop_next()

    def _process_entry(self, entry: QueueEntry | None):
        if entry is None:
            return None

        tx = entry.transaction
        transaction_type = tx.transaction_type
        tx.mark_processing()
        if tx.attempts == 1:
            self._processed.append(tx)

        try:
            if transaction_type is TransactionType.DEPOSIT:
                receiver_id = tx.receiver_id
                receiver = self._bank.get_account(receiver_id)
                amount = convert(tx.amount, tx.currency, receiver.currency)
                self._bank.deposit(receiver_id, amount)
            elif transaction_type is TransactionType.WITHDRAWAL:
                sender_id = tx.sender_id
                sender = self._bank.get_account(sender_id)
                amount = convert(tx.amount, tx.currency, sender.currency)
                self._bank.withdraw(sender_id, amount)
            elif transaction_type is TransactionType.TRANSFER:
                sender_id = tx.sender_id
                receiver_id = tx.receiver_id
                sender = self._bank.get_account(sender_id)
                receiver = self._bank.get_account(receiver_id)
                withdrawn_amount = convert(tx.amount, tx.currency, sender.currency)
                deposited_amount = convert(tx.amount, tx.currency, receiver.currency)
                self._bank.transfer(
                    sender_id, receiver_id, withdrawn_amount, deposited_amount
                )
            elif transaction_type is TransactionType.EXTERNAL_TRANSFER:
                sender_id = tx.sender_id
                sender = self._bank.get_account(sender_id)
                amount = convert(tx.amount, tx.currency, sender.currency)
                fee = self._calculate_fee(tx)
                amount += convert(fee, tx.currency, sender.currency)
                self._bank.withdraw(sender_id, amount)
            else:
                raise InvalidOperationError(
                    f"cannot process: unsupported transaction_type {transaction_type!r}"
                )
            tx.mark_completed()
            print(tx)
            return True
        except BankError as e:
            tx.mark_failed(str(e))
            self._log_error(tx, str(e))
            print(tx)
            return False

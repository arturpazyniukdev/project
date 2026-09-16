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
    def __init__(self, owner, balance=0, currency=Currency.USD, status=AccountStatus.ACTIVE, account_id=None):
        if not isinstance(owner, str):
            raise TypeError(f"owner must be a string, got {type(owner).__name__}")
        
        owner = owner.strip()
        
        if len(owner) == 0:
            raise ValueError("owner should not be empty")
        
        self._owner = owner
        
        if not isinstance(balance, (int, float)) or isinstance(balance, bool):
            raise TypeError(f"balance must be an int or float, got {type(balance).__name__}")
        
        if balance < 0:
            raise ValueError(f"balance cannot be negative, got {balance}")
        
        self._balance = balance
        
        if not isinstance(currency, Currency):
            raise TypeError(f"currency must be a Currency member, got {currency!r}; try Currency({currency!r})")
            
        self._currency = currency
        
        if not isinstance(status, AccountStatus):
            raise TypeError(f"status must be a AccountStatus member, got {status!r}; try AccountStatus({status!r})")

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
            raise AccountFrozenError(f"cannot {operation}: account is {self._status.value}")
        raise AccountClosedError(f"cannot {operation}: account is {self._status.value}")
        
    def _validate_amount(self, amount):
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise TypeError(f"amount must be an int or float, got {type(amount).__name__}")
        
        if amount <= 0:
            raise InvalidOperationError(f"amount must be positive, got {amount}")
        

    
class BankAccount(AbstractAccount):
    def get_account_info(self):
        info = {
            "account_id": self.account_id,
            "owner": self.owner,
            "balance": self.balance,
            "currency": self.currency.value,
            "status": self.status.value
        }
        
        return info
    
    def deposit(self, amount):
        self._ensure_active('deposit')
        self._validate_amount(amount)
        self._balance += amount
        
    def withdraw(self, amount):
        self._ensure_active('withdraw')
        self._validate_amount(amount)
        
        if self._balance < amount:
            raise InsufficientFundsError(f"cannot withdraw {amount}, balance is only {self._balance}")

        self._balance -= amount

a = BankAccount('A',100, Currency.USD)
print(a)
b = BankAccount('B',100,Currency.USD,AccountStatus.FROZEN)
print(b)

try:
    b.deposit(50)
except BankError as e:
    print(e)
    
a.deposit(50)
a.withdraw(51)
print(a)



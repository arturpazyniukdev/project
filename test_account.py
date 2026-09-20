from account import (
    AccountStatus,
    Currency,
    BankAccount,
    SavingsAccount,
    PremiumAccount,
    InvestmentAccount,
)
from helpers import expect_error


basic = BankAccount("Basic", 100, Currency.USD)
basic_frozen = BankAccount("Basic Frozen", 100, Currency.USD, AccountStatus.FROZEN)
basic_closed = BankAccount("Basic Closed", 100, Currency.USD, AccountStatus.CLOSED)

print("--- Basic ---")
print(basic)
print("before:", basic.balance)
basic.deposit(50)
basic.withdraw(20)
print("after: ", basic.balance)
print(basic.get_account_info())


print("--- Basic Frozen ---")
print(basic_frozen)
expect_error("frozen deposit", lambda: basic_frozen.deposit(50))

print("--- Basic Closed ---")
print(basic_closed)
expect_error("closed deposit", lambda: basic_closed.deposit(50))

savings = SavingsAccount(
    "Savings", 100, Currency.USD, AccountStatus.ACTIVE, None, 10, 0.02
)
savings2 = SavingsAccount(
    "Savings2", 150, Currency.USD, AccountStatus.ACTIVE, None, 11, 0.05
)

print("--- Savings ---")
print(savings)
print("before:", savings.balance)
expect_error("savings below min", lambda: savings.withdraw(91))
print(savings.apply_monthly_interest())
print("after: ", savings.balance)
print(savings.get_account_info())

print(savings2)

premium = PremiumAccount(
    "Premium", 100, Currency.USD, AccountStatus.ACTIVE, None, None, 10, 1
)
premium2 = PremiumAccount(
    "Premium2", 100, Currency.USD, AccountStatus.ACTIVE, None, 23, 10, 1
)

print("--- Premium ---")
print(premium)
print("before:", premium.balance)
premium.withdraw(109)
print("after: ", premium.balance)
expect_error("premium past overdraft", lambda: premium.withdraw(1))
print(premium.get_account_info())

print(premium2)
expect_error("premium over max", lambda: premium2.withdraw(24))

investment = InvestmentAccount(
    "Investment", 130, Currency.USD, AccountStatus.ACTIVE, None
)
investment2 = InvestmentAccount(
    "Investment2", 120, Currency.USD, AccountStatus.ACTIVE, None
)

print("--- Investment ---")
investment.invest(10, "stocks")
expect_error("bad asset type", lambda: investment.invest(10, "socks"))
expect_error("invest over balance", lambda: investment.invest(150, "stocks"))
expect_error("zero/negative amount", lambda: investment.invest(-2, "stocks"))
investment.invest(10, "bonds")
investment.invest(10, "etf")
print(investment)
print(investment.get_account_info())
print(investment.project_yearly_growth({"stocks": 0.1, "bonds": 0.04, "etf": 0.07}))
print(investment2)

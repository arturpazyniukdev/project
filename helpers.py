from account import BankError


def expect_error(label, operation, error_type=BankError):
    try:
        operation()
    except error_type as e:
        print(label, "raised", type(e).__name__, e)
    else:
        print(label, "nothing raised")

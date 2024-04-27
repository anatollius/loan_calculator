from datetime import date
from typing import NamedTuple
from enum import Enum
import json


class Input(NamedTuple):
    start_date: date
    end_date: date
    loan_amount: float
    loan_currency: str
    base_interest_rate: float
    margin: float


class Output(NamedTuple):
    daily_base_interest: float
    daily_total_interest: float
    accrual_date: date
    days_since_start: int
    total_interest: float
    loan_currency: str

    def __str__(self):
        return f"""
    Daily Interest Amount without margin: {self.loan_currency} {self.daily_base_interest:.2f}
    Daily Interest Amount Accrued: {self.loan_currency} {self.daily_total_interest:.2f}
    Accrual Date: {self.accrual_date.isoformat()}
    Number of Days elapsed since the start date of the loan: {self.days_since_start}
    Total Interest: {self.loan_currency} {self.total_interest:.2f}
"""


class Commmad(Enum):
    NEW_INPUT = 1
    EDIT_EXISTING = 2
    EXIT = 3
    BAD_INPUT = 4


CURRENCIES = ["USD", "EUR", "GBP"]


in_mem_store: dict[int, tuple[Input, Output]] = {}


def main():
    command = None
    while command != Commmad.EXIT:
        if command is None:
            print("Welcome to the loan calculator!")

        command = _parse_command()

        match command:
            case Commmad.NEW_INPUT:
                _handle_new_input()
            case Commmad.EDIT_EXISTING:
                _handle_edit_existing_input()
            case Commmad.EXIT:
                _handle_exit()

    print("Goodbye!")


def _parse_command():
    commands = {
        "new": Commmad.NEW_INPUT,
        "edit": Commmad.EDIT_EXISTING,
        "exit": Commmad.EXIT,
    }

    while True:
        command = input("What would you like to do? [new, edit, exit]: ")
        command = command.strip().lower()

        if command in commands:
            return commands[command]
        else:
            print("Invalid command. Please try again.")


def _handle_new_input():
    start_date = _get_user_value(
        lambda: date.fromisoformat(input("Start date [YYYY-MM-DD]: "))
    )
    end_date = _get_user_value(
        lambda: date.fromisoformat(input("End date [YYYY-MM-DD]: "))
    )
    loan_amount = _get_user_value(lambda: float(input("Loan amount: ")))
    loan_currency = _get_user_value(lambda: _get_user_currency())
    base_interest_rate = _get_user_value(lambda: float(input("Base interest rate: ")))
    margin = _get_user_value(lambda: float(input("Margin: ")))

    input_data = Input(
        start_date=start_date,
        end_date=end_date,
        loan_amount=loan_amount,
        loan_currency=loan_currency,
        base_interest_rate=base_interest_rate,
        margin=margin,
    )

    output_data = _calculate_output(input_data)

    id = len(in_mem_store) + 1
    in_mem_store[id] = (input_data, output_data)

    print(f"\n    Request ID: {id}")
    print(output_data)

    return


def _handle_edit_existing_input():
    id = _get_user_value(lambda: _get_request_id_from_user())

    input_data, output_data = in_mem_store[id]

    start_date = _get_user_value(
        lambda: date.fromisoformat(input("Start date [YYYY-MM-DD]: "))
    )
    end_date = _get_user_value(
        lambda: date.fromisoformat(input("End date [YYYY-MM-DD]: "))
    )
    loan_amount = _get_user_value(lambda: float(input("Loan amount: ")))
    loan_currency = _get_user_value(lambda: _get_user_currency())
    base_interest_rate = _get_user_value(lambda: float(input("Base interest rate: ")))
    margin = _get_user_value(lambda: float(input("Margin: ")))

    input_data = Input(
        start_date=start_date,
        end_date=end_date,
        loan_amount=loan_amount,
        loan_currency=loan_currency,
        base_interest_rate=base_interest_rate,
        margin=margin,
    )

    output_data = _calculate_output(input_data)

    in_mem_store[id] = (input_data, output_data)

    print(output_data)


def _handle_exit() -> None:
    response = None
    valid_responses = ["y", "n"]

    while response not in valid_responses:
        response = input("Would you like to save your requests? [y, n]: ")
        response = response.strip().lower()

        if response not in valid_responses:
            print("Invalid response. Please try again.")

    if response == "y":
        _save_to_file()
    elif response == "n":
        return


def _get_user_value(callback) -> date | float | str:
    while True:
        try:
            return callback()
        except ValueError as e:
            print(f"Invalid input. {e}")


def _get_user_currency() -> str:
    if (currency := input("Loan currency: ")) in CURRENCIES:
        return currency
    else:
        raise ValueError(
            f"Invalid currency. Valid options are: {', '.join(CURRENCIES)}"
        )


def _get_request_id_from_user() -> int:
    id = int(input("Please enter the request ID: "))

    if id not in in_mem_store:
        raise ValueError(
            f"Invalid request ID. Valid IDs: {', '.join((str(k) for k in in_mem_store))}"
        )

    return id


def _calculate_output(input_data: Input) -> Output:
    daily_base_interest = _get_daily_base_interest(input_data)
    daily_total_interest = _get_daily_total_interest(input_data)
    days_since_start = _get_days_since_start(input_data)
    total_days = _get_total_loan_days(input_data)
    total_interest = _get_total_interest(input_data)

    return Output(
        daily_base_interest=daily_base_interest,
        daily_total_interest=daily_total_interest,
        accrual_date=input_data.start_date,
        days_since_start=days_since_start,
        total_interest=total_interest,
        loan_currency=input_data.loan_currency,
    )


def _get_interest_rate(input_data: Input) -> float:
    return (input_data.base_interest_rate + input_data.margin) / 100


def _get_daily_base_interest(input_data: Input) -> float:
    return (input_data.loan_amount * input_data.base_interest_rate / 100) / 365


def _get_daily_total_interest(input_data: Input) -> float:
    return (input_data.loan_amount * _get_interest_rate(input_data)) / 356


def _get_days_since_start(input_data: Input) -> int:
    return (date.today() - input_data.start_date).days


def _get_total_loan_days(input_data: Input) -> int:
    return (input_data.end_date - input_data.start_date).days


def _get_total_interest(input_data: Input) -> float:
    return (
        input_data.loan_amount
        * _get_interest_rate(input_data)
        * (_get_total_loan_days(input_data) / 365)
    )


def _save_to_file():
    with open("loan_requests.json", "w") as f:
        json.dump(in_mem_store, f)


if __name__ == "__main__":
    main()

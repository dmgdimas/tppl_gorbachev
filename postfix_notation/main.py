"""Стековая машина для вычисления выражений в постфиксной нотации."""

import math
import os
import sys
from typing import List, Optional, Union

Number = Union[int, float]

OPERATORS = {"+", "-", "*", "/", "~"}

USAGE = (
    "Использование: python main.py <выражение в постфиксной нотации>\n"
    'Пример: python main.py "3 0 4 ~ 2 ~"'
)


class StackMachineError(ValueError):
    """Ошибка вычисления выражения."""


def ensure_finite(value: Number) -> Number:
    """Проверяет, что результат является конечным числом."""
    if isinstance(value, float) and not math.isfinite(value):
        raise StackMachineError("Результат операции не является конечным числом")
    return value


def normalize_number(value: Number) -> Number:
    """Приводит целочисленные вещественные значения к типу int."""
    if isinstance(value, float):
        if math.isfinite(value) and value.is_integer():
            return int(value)
    return value


def parse_token(token: str) -> Union[str, Number]:
    """Разбирает токен: оператор или число."""
    if token in OPERATORS:
        return token

    try:
        value: Number = int(token)
    except ValueError:
        try:
            value = float(token)
        except ValueError as exc:
            raise StackMachineError(f"Неизвестный токен: {token!r}") from exc

    if isinstance(value, float) and not math.isfinite(value):
        raise StackMachineError(f"Недопустимое число: {token!r}")

    return normalize_number(value)


def format_number(value: Number) -> str:
    """Форматирует число для вывода."""
    return str(normalize_number(value))


def format_stack(stack: List[Number]) -> str:
    """Форматирует стек для вывода."""
    return "[" + ", ".join(format_number(item) for item in stack) + "]"


def apply_operator(stack: List[Number], operator: str) -> None:
    """Применяет операцию к стеку."""
    if len(stack) < 2:
        raise StackMachineError(
            f"Недостаточно операндов для операции {operator!r}"
        )

    right = stack.pop()
    left = stack.pop()

    collapse_stack = False

    try:
        if operator == "+":
            result = left + right
        elif operator == "-":
            result = left - right
        elif operator == "*":
            result = left * right
        elif operator == "/":
            if right == 0:
                raise StackMachineError("Деление на ноль")
            result = left / right
        elif operator == "~":
            if left != 0 and right != 0:
                result = abs(left - right)
            else:
                # Суммируем все значения, которые были в стеке,
                # включая два извлечённых операнда.
                total = sum(stack) + left + right
                result = total * total
                collapse_stack = True
        else:
            raise StackMachineError(f"Неизвестная операция: {operator!r}")
    except OverflowError as exc:
        raise StackMachineError("Результат операции слишком большой") from exc

    result = normalize_number(ensure_finite(result))

    if collapse_stack:
        stack.clear()

    stack.append(result)


def evaluate(tokens: List[str], verbose: bool = False) -> Number:
    """Вычисляет постфиксное выражение."""
    stack: List[Number] = []

    if not tokens:
        raise StackMachineError("Пустое выражение")

    for index, token in enumerate(tokens, start=1):
        parsed = parse_token(token)

        if isinstance(parsed, str):
            apply_operator(stack, parsed)
        else:
            stack.append(parsed)

        if verbose:
            print(f"Шаг {index}: токен {token!r} -> стек: {format_stack(stack)}")

    if len(stack) != 1:
        raise StackMachineError(
            "После вычисления в стеке должно остаться одно значение, "
            f"получено: {format_stack(stack)}"
        )

    return normalize_number(stack[0])


def main(argv: Optional[List[str]] = None) -> int:
    """Точка входа командной строки."""
    if argv is None:
        argv = sys.argv[1:]
    # Если оболочка раскрыла ~ как домашнюю директорию:
    try:
        home_dir = os.path.expanduser("~")
    except Exception:
        home_dir = None
        
    if home_dir and home_dir != "~":
        argv = ["~" if arg == home_dir else arg for arg in argv]

    if not argv:
        print(USAGE, file=sys.stderr)
        return 1

    tokens = " ".join(argv).split()
    expression = " ".join(tokens)

    try:
        result = evaluate(tokens, verbose=True)
    except StackMachineError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    print(f"{expression} = {format_number(result)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import (
    OPERATORS,
    StackMachineError,
    apply_operator,
    ensure_finite,
    evaluate,
    format_number,
    format_stack,
    main,
    normalize_number,
    parse_token,
)


def test_ensure_finite_ok():
    assert ensure_finite(10) == 10
    assert ensure_finite(10.5) == 10.5


def test_ensure_finite_raises():
    with pytest.raises(StackMachineError, match="конечным"):
        ensure_finite(float("inf"))


def test_normalize_number():
    assert normalize_number(3) == 3
    assert normalize_number(3.0) == 3
    assert normalize_number(3.25) == 3.25
    assert normalize_number(-0.0) == 0
    assert math.isinf(normalize_number(float("inf")))


@pytest.mark.parametrize("token", sorted(OPERATORS))
def test_parse_token_operator(token):
    assert parse_token(token) == token


@pytest.mark.parametrize(
    "token,expected",
    [
        ("5", 5),
        ("-7", -7),
        ("+3", 3),
        ("2.0", 2),
    ],
)
def test_parse_token_int(token, expected):
    parsed = parse_token(token)
    assert parsed == expected
    assert isinstance(parsed, int)


@pytest.mark.parametrize(
    "token,expected",
    [
        ("2.5", 2.5),
        ("-0.5", -0.5),
    ],
)
def test_parse_token_float(token, expected):
    parsed = parse_token(token)
    assert parsed == expected
    assert isinstance(parsed, float)


@pytest.mark.parametrize(
    "token",
    ["abc", "", "1.2.3", "nan", "inf", "-inf"],
)
def test_parse_token_invalid(token):
    with pytest.raises(StackMachineError):
        parse_token(token)


def test_format_number():
    assert format_number(2) == "2"
    assert format_number(2.0) == "2"
    assert format_number(2.5) == "2.5"


def test_format_stack():
    assert format_stack([]) == "[]"
    assert format_stack([1, 2.0, 3.5]) == "[1, 2, 3.5]"


@pytest.mark.parametrize(
    "operator,before,after",
    [
        ("+", [2, 3], [5]),
        ("-", [5, 2], [3]),
        ("*", [4, 2], [8]),
        ("/", [6, 2], [3]),
        ("/", [5, 2], [2.5]),
    ],
)
def test_apply_binary(operator, before, after):
    stack = before[:]
    apply_operator(stack, operator)
    assert stack == after


def test_apply_division_by_zero():
    with pytest.raises(StackMachineError, match="Деление на ноль"):
        apply_operator([1, 0], "/")

    with pytest.raises(StackMachineError, match="Деление на ноль"):
        apply_operator([1, 0.0], "/")


@pytest.mark.parametrize("operator", sorted(OPERATORS))
def test_apply_insufficient_operands(operator):
    with pytest.raises(StackMachineError, match="Недостаточно операндов"):
        apply_operator([1], operator)


def test_apply_unknown_operator():
    with pytest.raises(StackMachineError, match="Неизвестная операция"):
        apply_operator([1, 2], "%")


@pytest.mark.parametrize(
    "before,after",
    [
        ([10, 3], [7]),
        ([-2, 5], [7]),
        ([5, 5], [0]),
        ([2.5, 1.0], [1.5]),
    ],
)
def test_tilde_both_nonzero(before, after):
    stack = before[:]
    apply_operator(stack, "~")
    assert stack == after


@pytest.mark.parametrize(
    "before,after",
    [
        ([3, 0, 4], [49]),
        ([0, 4], [16]),
        ([4, 0], [16]),
        ([0, 0], [0]),
        ([1, 2, 5, 0], [64]),
        ([1.5, 0.0], [2.25]),
    ],
)
def test_tilde_zero_operand(before, after):
    stack = before[:]
    apply_operator(stack, "~")
    assert stack == after


def test_apply_operator_nonfinite_result():
    with pytest.raises(StackMachineError, match="конечным"):
        apply_operator([float("inf"), 1.0], "+")


def test_tilde_zero_nonfinite_result():
    with pytest.raises(StackMachineError, match="конечным"):
        apply_operator([float("inf"), 0, 0], "~")


def test_apply_division_overflow():
    with pytest.raises(StackMachineError):
        apply_operator([10**400, 1], "/")


def test_evaluate_example_1():
    assert evaluate("3 0 4 ~ 2 ~".split()) == 47


def test_evaluate_example_2():
    assert evaluate("2 2 + 4 - 4 ~ 2 3 * +".split()) == 22


def test_evaluate_simple():
    assert evaluate(["2", "2", "+"]) == 4


def test_evaluate_float_normalized():
    result = evaluate(["1.5", "2.5", "+"])
    assert result == 4
    assert isinstance(result, int)


def test_evaluate_division_not_integer():
    assert evaluate(["5", "2", "/"]) == 2.5


def test_evaluate_empty():
    with pytest.raises(StackMachineError, match="Пустое"):
        evaluate([])


def test_evaluate_invalid_token():
    with pytest.raises(StackMachineError, match="Неизвестный токен"):
        evaluate(["1", "x"])


def test_evaluate_insufficient_operands():
    with pytest.raises(StackMachineError, match="Недостаточно операндов"):
        evaluate(["1", "+"])


def test_evaluate_extra_values():
    with pytest.raises(StackMachineError, match="остаться одно значение"):
        evaluate(["1", "2", "+", "3"])


def test_evaluate_verbose(capsys):
    result = evaluate(["2", "2", "+"], verbose=True)
    out = capsys.readouterr().out

    assert result == 4
    assert "Шаг 1: токен '2' -> стек: [2]" in out
    assert "Шаг 2: токен '2' -> стек: [2, 2]" in out
    assert "Шаг 3: токен '+' -> стек: [4]" in out


def test_evaluate_silent(capsys):
    evaluate(["2", "2", "+"], verbose=False)
    assert capsys.readouterr().out == ""


def test_main_no_args(capsys):
    assert main([]) == 1
    err = capsys.readouterr().err
    assert "Использование" in err


def test_main_valid(capsys):
    assert main(["3", "0", "4", "~", "2", "~"]) == 0
    out = capsys.readouterr().out

    assert "Шаг" in out
    assert "3 0 4 ~ 2 ~ = 47" in out


def test_main_single_string(capsys):
    assert main(["2 2 +"]) == 0
    out = capsys.readouterr().out
    assert "2 2 + = 4" in out


def test_main_normalizes_spaces(capsys):
    assert main(["  2   2   +  "]) == 0
    out = capsys.readouterr().out
    assert "2 2 + = 4" in out


def test_main_error_division_by_zero(capsys):
    assert main(["1", "0", "/"]) == 1
    err = capsys.readouterr().err

    assert "Ошибка" in err
    assert "Деление на ноль" in err


def test_main_error_invalid_token(capsys):
    assert main(["x"]) == 1
    err = capsys.readouterr().err
    assert "Неизвестный токен" in err


def test_main_error_extra_values(capsys):
    assert main(["1", "2", "+", "3"]) == 1
    err = capsys.readouterr().err
    assert "остаться одно значение" in err


def test_main_empty_string_arg(capsys):
    assert main(["   "]) == 1
    err = capsys.readouterr().err
    assert "Пустое выражение" in err


def test_main_uses_sys_argv(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["main.py", "2", "2", "+"])
    assert main(None) == 0
    out = capsys.readouterr().out
    assert "2 2 + = 4" in out
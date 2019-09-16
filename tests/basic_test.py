import pytest


def test_basic():
    assert True


def test_pytest_zero_division():
    with pytest.raises(ZeroDivisionError):
        1 / 0

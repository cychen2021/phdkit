import time
import pytest

from phdkit.autoretry import AutoRetry, AutoRetryError


def test_autoretry_success():
    calls = {}

    def fn(x):
        calls["called"] = True
        return x * 2

    ar = AutoRetry(fn, max_retrys=3)
    assert ar(3) == 6
    assert calls.get("called")


def test_autoretry_retry_then_success(monkeypatch):
    attempts = {"count": 0}

    def flaky(x):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise ValueError("fail")
        return x + 1

    # avoid sleeping during test
    monkeypatch.setattr(time, "sleep", lambda s: None)

    ar = AutoRetry(flaky, max_retrys=3)
    assert ar(4) == 5
    assert attempts["count"] == 2


def test_autoretry_final_failure(monkeypatch):
    def always_fail():
        raise RuntimeError("nope")

    monkeypatch.setattr(time, "sleep", lambda s: None)

    ar = AutoRetry(always_fail, max_retrys=2)
    with pytest.raises(AutoRetryError) as exc:
        ar()
    assert "failed after" in str(exc.value).lower()

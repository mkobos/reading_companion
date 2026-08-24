"""Regression test: app.main must load backend/.env when actually served.

tests/conftest.py already calls load_dotenv() for every pytest run, which
masks whether app.main does this itself. But the real entrypoint
(`uv run uvicorn app.main:app`) never goes through conftest.py, so if
app.main doesn't call load_dotenv() itself, backend/.env is silently
never read outside of tests — see discussion-agent/app/fast_api_app.py,
which calls load_dotenv() for exactly this reason.
"""

import importlib
import sys


def test_main_module_calls_load_dotenv_on_import(monkeypatch):
    calls = []
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: calls.append((a, k)))

    original_module = sys.modules.pop("app.main", None)
    try:
        importlib.import_module("app.main")
    finally:
        if original_module is not None:
            sys.modules["app.main"] = original_module
        else:
            sys.modules.pop("app.main", None)

    assert calls, (
        "app.main must call load_dotenv() so backend/.env is read when "
        "running the real server, not just under pytest"
    )

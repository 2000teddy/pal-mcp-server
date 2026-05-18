"""Concurrency regression tests for conversation_memory.add_turn().

Covers the race-condition fix (TODO #2): the prior non-atomic
read-modify-write in add_turn() could drop turns when called in parallel.
The atomic_update-based implementation must preserve every turn.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, wait
from unittest.mock import patch

import pytest

from utils import conversation_memory
from utils.conversation_memory import (
    ThreadContext,
    add_turn,
    create_thread,
    get_thread,
)
from utils.storage_backend import InMemoryStorage


@pytest.fixture
def isolated_storage(monkeypatch):
    """Give each test its own InMemoryStorage, not the singleton."""
    storage = InMemoryStorage()
    monkeypatch.setattr(conversation_memory, "get_storage", lambda: storage)
    yield storage
    storage.shutdown()


def _add_turn_worker(thread_id: str, index: int) -> bool:
    return add_turn(
        thread_id=thread_id,
        role="user",
        content=f"turn-{index}",
        tool_name="chat",
    )


def test_parallel_add_turn_preserves_all_turns(isolated_storage):
    """50 threads hitting add_turn() on the same thread_id must all persist."""
    thread_id = create_thread("chat", {"prompt": "seed"})

    count = 50
    with ThreadPoolExecutor(max_workers=count) as pool:
        futures = [pool.submit(_add_turn_worker, thread_id, i) for i in range(count)]
        wait(futures)
        results = [f.result() for f in futures]

    assert all(results), "every add_turn call must report success"

    context = get_thread(thread_id)
    assert context is not None
    assert len(context.turns) == count, f"expected {count} turns after parallel add_turn, got {len(context.turns)}"
    contents = {turn.content for turn in context.turns}
    assert contents == {f"turn-{i}" for i in range(count)}


@pytest.mark.parametrize("run", range(5))
def test_parallel_add_turn_repeated_runs(isolated_storage, run):
    """Re-run the race 5x; flaky fixes would fail on at least one run."""
    thread_id = create_thread("chat", {"prompt": f"run-{run}"})
    count = 25

    with ThreadPoolExecutor(max_workers=count) as pool:
        futures = [pool.submit(_add_turn_worker, thread_id, i) for i in range(count)]
        wait(futures)
        for f in futures:
            assert f.result() is True

    context = get_thread(thread_id)
    assert context is not None
    assert len(context.turns) == count


def test_parallel_add_turn_enforces_max_turns(isolated_storage):
    """Under load near MAX_CONVERSATION_TURNS only the allowed count wins."""
    cap = 10
    with patch.object(conversation_memory, "MAX_CONVERSATION_TURNS", cap):
        thread_id = create_thread("chat", {"prompt": "cap"})
        attempts = 40

        with ThreadPoolExecutor(max_workers=attempts) as pool:
            futures = [pool.submit(_add_turn_worker, thread_id, i) for i in range(attempts)]
            wait(futures)
            results = [f.result() for f in futures]

        context = get_thread(thread_id)
        assert context is not None
        assert len(context.turns) == cap
        assert sum(1 for r in results if r) == cap
        assert sum(1 for r in results if not r) == attempts - cap


def test_atomic_update_callback_exception_does_not_corrupt_store(isolated_storage):
    """If modify_fn raises, the stored value must remain unchanged."""
    key = "thread:test-exc"
    isolated_storage.set_with_ttl(key, 3600, '{"sentinel": "before"}')

    def boom(_current):
        raise RuntimeError("callback failure")

    with pytest.raises(RuntimeError):
        isolated_storage.atomic_update(key, 3600, boom)

    assert isolated_storage.get(key) == '{"sentinel": "before"}'


def test_atomic_update_returning_none_aborts_write(isolated_storage):
    """Returning None from modify_fn leaves the current value untouched."""
    key = "thread:test-abort"
    isolated_storage.set_with_ttl(key, 3600, "keep")

    result = isolated_storage.atomic_update(key, 3600, lambda _cur: None)

    assert result is None
    assert isolated_storage.get(key) == "keep"


def test_atomic_update_receives_none_for_missing_key(isolated_storage):
    """Callback sees None when the key is absent."""
    observed = {}

    def capture(current):
        observed["value"] = current
        return "written"

    new = isolated_storage.atomic_update("thread:fresh", 3600, capture)
    assert observed["value"] is None
    assert new == "written"
    assert isolated_storage.get("thread:fresh") == "written"


def test_add_turn_thread_context_roundtrip(isolated_storage):
    """Sanity: after add_turn, the stored blob still deserializes cleanly."""
    thread_id = create_thread("chat", {"prompt": "rt"})
    assert add_turn(thread_id=thread_id, role="user", content="hello") is True

    raw = isolated_storage.get(f"thread:{thread_id}")
    assert raw is not None
    parsed = ThreadContext.model_validate_json(raw)
    assert parsed.thread_id == thread_id
    assert any(turn.content == "hello" for turn in parsed.turns)

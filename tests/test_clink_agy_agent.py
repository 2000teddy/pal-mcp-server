"""Tests for agy as a full clink client (AgyAgent: prompt-as-argument).

agy is the Gemini-CLI successor and, unlike claude/codex/gemini, takes the prompt
as a ``-p <prompt>`` command-line argument rather than via stdin. These tests pin:
the registry/factory wiring, the prompt-as-arg invocation, and that the default
(stdin) delivery for the other agents is unchanged.
"""

import asyncio
import shutil

import pytest

from clink.agents import create_agent
from clink.agents.agy import AgyAgent
from clink.agents.base import BaseCLIAgent
from clink.registry import ClinkRegistry


class DummyProcess:
    def __init__(self, *, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode
        self.stdin_data: bytes | None = None

    async def communicate(self, input_data=b""):
        self.stdin_data = input_data
        return self._stdout, self._stderr

    def kill(self):  # pragma: no cover - not exercised here
        pass


def _agy_client():
    return ClinkRegistry().get_client("agy")


def test_registry_loads_agy_client():
    client = _agy_client()
    assert client.name == "agy"
    assert client.parser == "agy_text"
    assert client.runner == "agy"
    assert client.executable == ["agy"]
    assert {"default", "planner", "codereviewer"} <= set(client.roles)


def test_factory_maps_agy_to_agy_agent():
    assert isinstance(create_agent(_agy_client()), AgyAgent)


def test_agy_prepares_prompt_as_argument_with_empty_stdin():
    agent = create_agent(_agy_client())
    command, stdin = agent._prepare_invocation(["agy", "--model", "x"], "Review this code")
    assert command == ["agy", "--model", "x", "-p", "Review this code"]
    assert stdin == b""


def test_default_agents_still_use_stdin():
    # Regression: the base (stdin) delivery is unchanged for non-arg-mode CLIs.
    base = BaseCLIAgent.__new__(BaseCLIAgent)
    command, stdin = BaseCLIAgent._prepare_invocation(base, ["claude", "--print"], "hi")
    assert command == ["claude", "--print"]
    assert stdin == b"hi"


@pytest.mark.asyncio
async def test_agy_run_spawns_with_prompt_arg_and_no_stdin(monkeypatch):
    client = _agy_client()
    agent = create_agent(client)

    process = DummyProcess(stdout=b"Looks good to me.", returncode=0)
    captured: dict[str, tuple] = {}

    async def fake_exec(*args, **_kwargs):
        captured["args"] = args
        return process

    # Re-patch shutil.which (the hermetic conftest fixture hides agy) so _run proceeds
    # to our mocked subprocess instead of the "not found" path.
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(shutil, "which", lambda name, *a, **k: f"/usr/bin/{name}")

    result = await agent.run(
        role=client.get_role("codereviewer"),
        prompt="Please review the diff.",
        files=[],
        images=[],
    )

    # The prompt is delivered as the final "-p <prompt>" args; stdin is empty.
    assert captured["args"][-2:] == ("-p", "Please review the diff.")
    assert process.stdin_data == b""
    assert result.parsed.content == "Looks good to me."
    assert result.parser_name == "agy_text"

"""CLI integration tests for scripts/thread_logger.py."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pytest


SCRIPT = str(Path(__file__).resolve().parent.parent / "scripts" / "thread_logger.py")


@pytest.fixture(autouse=True)
def isolated_dirs(tmp_path):
    """Redirect thread logger state/log dirs to temp so tests don't pollute workspace."""
    state_dir = tmp_path / ".thread-state"
    log_dir = tmp_path / "logs" / "threads"
    state_dir.mkdir(parents=True)
    log_dir.mkdir(parents=True)
    env_patch = {
        "THREAD_LOG_STATE_DIR": str(state_dir),
        "THREAD_LOG_DIR": str(log_dir),
    }
    yield env_patch


def run_cli(*args: str, env_override: dict | None = None) -> subprocess.CompletedProcess:
    import os
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    return subprocess.run(
        ["python3", SCRIPT, *args],
        capture_output=True, text=True, timeout=10,
        env=env,
    )


class TestCLIOpenClose:
    def test_open_returns_json(self, isolated_dirs):
        result = run_cli("open", "--branch", "cursorcachat-cli-test-cafe", "--prompt", "Test prompt", env_override=isolated_dirs)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "opened"
        assert data["thread_id"] == "cafe"

    def test_close_returns_json(self, isolated_dirs):
        run_cli("open", "--branch", "cursorcachat-cli-close-beef", "--prompt", "Close test", env_override=isolated_dirs)
        result = run_cli(
            "close", "--branch", "cursorcachat-cli-close-beef",
            "--title", "CLI Close Test",
            "--outcome", "completed",
            "--tags", "test", "cli",
            env_override=isolated_dirs,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "closed"
        assert data["thread_id"] == "beef"
        assert isinstance(data["files_changed"], int)

    def test_list_returns_output(self, isolated_dirs):
        result = run_cli("list", env_override=isolated_dirs)
        assert result.returncode == 0

    def test_list_json_format(self, isolated_dirs):
        result = run_cli("list", "--format", "json", env_override=isolated_dirs)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)

    def test_backfill_returns_json(self, isolated_dirs, tmp_path):
        transcript_root = tmp_path / "agent-transcripts"
        parent_id = "118435cc-b21b-4c1a-9136-bf152e779b2a"
        parent_dir = transcript_root / parent_id
        parent_dir.mkdir(parents=True)
        (parent_dir / f"{parent_id}.jsonl").write_text(
            json.dumps(
                {
                    "role": "user",
                    "message": {
                        "content": [{"type": "text", "text": "<user_query>\nBackfill me\n</user_query>"}]
                    },
                }
            )
            + "\n"
        )
        env = dict(isolated_dirs)
        env["AGENT_TRANSCRIPTS_DIR"] = str(transcript_root)

        result = run_cli("backfill", env_override=env)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "backfilled"
        assert data["created"] == 1


class TestCLIEdgeCases:
    def test_open_missing_prompt(self, isolated_dirs):
        result = run_cli("open", "--branch", "test-branch", env_override=isolated_dirs)
        assert result.returncode != 0

    def test_close_invalid_outcome(self, isolated_dirs):
        result = run_cli("close", "--branch", "test", "--outcome", "invalid", env_override=isolated_dirs)
        assert result.returncode != 0

    def test_open_idempotent(self, isolated_dirs):
        r1 = run_cli("open", "--branch", "cursorcachat-idem-test-dead", "--prompt", "First", env_override=isolated_dirs)
        r2 = run_cli("open", "--branch", "cursorcachat-idem-test-dead", "--prompt", "Second", env_override=isolated_dirs)
        assert r1.returncode == 0
        assert r2.returncode == 0
        d1 = json.loads(r1.stdout)
        d2 = json.loads(r2.stdout)
        assert d1["thread_id"] == d2["thread_id"]

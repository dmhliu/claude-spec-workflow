"""Tests for scripts/thread_logger.py — per-thread data logging."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from thread_logger import (
    extract_thread_id,
    parse_branch_name,
    capture_git_state,
    ThreadRecord,
    open_thread,
    close_thread,
    list_threads,
    backfill_threads_from_transcripts,
    ACTIVE_STATE_DIR,
    THREAD_LOG_DIR,
)


# --- Thread ID extraction ---


class TestExtractThreadId:
    def test_standard_cloud_agent_branch(self):
        assert extract_thread_id("cursorcachat-thread-data-logging-43cd") == "43cd"

    def test_short_branch(self):
        assert extract_thread_id("cursorcachat-fix-bug-a1b2") == "a1b2"

    def test_cursor_prefix_branch(self):
        assert extract_thread_id("cursor/add-readme-1234") == "1234"

    def test_plain_branch_falls_back_to_hash(self):
        tid = extract_thread_id("main")
        assert len(tid) == 8

    def test_feature_branch_extracts_suffix(self):
        assert extract_thread_id("cursorcachat-some-feature-ff00") == "ff00"

    def test_long_hex_suffix(self):
        assert extract_thread_id("cursorcachat-work-item-deadbeef") == "deadbeef"


class TestParseBranchName:
    def test_standard_format(self):
        result = parse_branch_name("cursorcachat-thread-data-logging-43cd")
        assert result["thread_id"] == "43cd"
        assert result["slug"] == "thread-data-logging"
        assert result["branch"] == "cursorcachat-thread-data-logging-43cd"

    def test_cursor_slash_format(self):
        result = parse_branch_name("cursor/fix-auth-5678")
        assert result["thread_id"] == "5678"
        assert result["slug"] == "fix-auth"

    def test_main_branch(self):
        result = parse_branch_name("main")
        assert result["branch"] == "main"
        assert result["slug"] == "main"
        assert len(result["thread_id"]) == 8


# --- Git state capture ---


class TestCaptureGitState:
    @patch("thread_logger.subprocess.run")
    def test_captures_head_sha(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="cef7b61\n",
        )
        state = capture_git_state()
        assert state["head_sha"].startswith("cef7b61")

    @patch("thread_logger.subprocess.run")
    def test_captures_branch(self, mock_run):
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="cef7b61\n"),
            MagicMock(returncode=0, stdout="main\n"),
        ]
        state = capture_git_state()
        assert "branch" in state


# --- ThreadRecord ---


class TestThreadRecord:
    def test_create_from_open(self):
        record = ThreadRecord.from_open(
            thread_id="43cd",
            branch="cursorcachat-test-43cd",
            initial_prompt="Fix the bug in auth",
        )
        assert record.thread_id == "43cd"
        assert record.initial_prompt == "Fix the bug in auth"
        assert record.started_at is not None
        assert record.closed_at is None

    def test_to_dict_includes_required_fields(self):
        record = ThreadRecord.from_open(
            thread_id="43cd",
            branch="cursorcachat-test-43cd",
            initial_prompt="Test prompt",
        )
        d = record.to_dict()
        assert "thread_id" in d
        assert "branch" in d
        assert "initial_prompt" in d
        assert "started_at" in d
        assert "repo" in d

    def test_to_json_is_single_line(self):
        record = ThreadRecord.from_open(
            thread_id="43cd",
            branch="cursorcachat-test-43cd",
            initial_prompt="Test",
        )
        line = record.to_jsonl()
        assert "\n" not in line
        parsed = json.loads(line)
        assert parsed["thread_id"] == "43cd"

    def test_close_populates_outcome_fields(self):
        record = ThreadRecord.from_open(
            thread_id="43cd",
            branch="cursorcachat-test-43cd",
            initial_prompt="Test",
        )
        record.close(
            session_title="Test Session",
            outcome="completed",
            files_changed=["a.py", "b.md"],
            commits=[{"sha": "abc", "message": "test"}],
            changelog_entries=["entry1"],
        )
        assert record.closed_at is not None
        assert record.outcome == "completed"
        assert record.session_title == "Test Session"
        assert len(record.files_changed) == 2
        assert record.duration_minutes is not None
        assert record.duration_minutes >= 0

    def test_from_dict_roundtrip(self):
        record = ThreadRecord.from_open(
            thread_id="43cd",
            branch="cursorcachat-test-43cd",
            initial_prompt="Test roundtrip",
        )
        d = record.to_dict()
        restored = ThreadRecord.from_dict(d)
        assert restored.thread_id == record.thread_id
        assert restored.initial_prompt == record.initial_prompt


# --- Open / Close lifecycle ---


class TestOpenThread:
    def test_open_creates_state_file(self, tmp_path):
        state_dir = tmp_path / ".thread-state"
        log_dir = tmp_path / "logs" / "threads"
        with patch("thread_logger.ACTIVE_STATE_DIR", state_dir), \
             patch("thread_logger.THREAD_LOG_DIR", log_dir):
            open_thread(
                branch="cursorcachat-test-feature-ab12",
                initial_prompt="Implement feature X",
            )
            state_file = state_dir / "cursorcachat-test-feature-ab12.json"
            assert state_file.exists()
            data = json.loads(state_file.read_text())
            assert data["thread_id"] == "ab12"
            assert data["initial_prompt"] == "Implement feature X"

    def test_open_is_idempotent(self, tmp_path):
        state_dir = tmp_path / ".thread-state"
        log_dir = tmp_path / "logs" / "threads"
        with patch("thread_logger.ACTIVE_STATE_DIR", state_dir), \
             patch("thread_logger.THREAD_LOG_DIR", log_dir):
            open_thread(
                branch="cursorcachat-test-ab12",
                initial_prompt="First prompt",
            )
            open_thread(
                branch="cursorcachat-test-ab12",
                initial_prompt="Second prompt (ignored)",
            )
            state_file = state_dir / "cursorcachat-test-ab12.json"
            data = json.loads(state_file.read_text())
            assert data["initial_prompt"] == "First prompt"


class TestCloseThread:
    def test_close_writes_per_thread_file(self, tmp_path):
        """Each thread gets its own JSON file under YYYY-MM/{thread_id}.json."""
        state_dir = tmp_path / ".thread-state"
        log_dir = tmp_path / "logs" / "threads"
        with patch("thread_logger.ACTIVE_STATE_DIR", state_dir), \
             patch("thread_logger.THREAD_LOG_DIR", log_dir), \
             patch("thread_logger._collect_git_diff") as mock_diff:
            mock_diff.return_value = {
                "files_changed": ["test.py"],
                "commits": [{"sha": "abc123", "message": "test"}],
            }
            open_thread(
                branch="cursorcachat-test-cd34",
                initial_prompt="Fix bug",
            )
            close_thread(
                branch="cursorcachat-test-cd34",
                session_title="Bug Fix Session",
                outcome="completed",
                changelog_entries=["[2026-03-05] CHANGE Fixed bug"],
                tags=["bugfix"],
            )
            month = datetime.now(timezone.utc).strftime("%Y-%m")
            thread_file = log_dir / month / "cd34.json"
            assert thread_file.exists()
            record = json.loads(thread_file.read_text())
            assert record["thread_id"] == "cd34"
            assert record["outcome"] == "completed"
            assert record["session_title"] == "Bug Fix Session"
            assert "Fix bug" in record["initial_prompt"]

    def test_close_enriches_with_subagent_summary_when_transcript_matches(self, tmp_path):
        state_dir = tmp_path / ".thread-state"
        log_dir = tmp_path / "logs" / "threads"
        transcript_root = tmp_path / "agent-transcripts"
        parent_id = "parent-thread-1234"
        parent_dir = transcript_root / parent_id
        subagent_dir = parent_dir / "subagents"
        parent_dir.mkdir(parents=True)
        subagent_dir.mkdir(parents=True)
        (parent_dir / f"{parent_id}.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "role": "user",
                            "message": {
                                "content": [
                                    {"type": "text", "text": "<user_query>\nNeed rollout help\n</user_query>"}
                                ]
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "role": "assistant",
                            "message": {"content": [{"type": "text", "text": "Parent response"}]},
                        }
                    ),
                ]
            )
            + "\n"
        )
        (subagent_dir / "subagent-one.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "role": "user",
                            "message": {
                                "content": [{"type": "text", "text": "Explore rollout pattern"}]
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "role": "assistant",
                            "message": {
                                "content": [{"type": "text", "text": "Found rollout summary"}]
                            },
                        }
                    ),
                ]
            )
            + "\n"
        )
        with patch("thread_logger.ACTIVE_STATE_DIR", state_dir), \
             patch("thread_logger.THREAD_LOG_DIR", log_dir), \
             patch("thread_logger.AGENT_TRANSCRIPTS_DIR", transcript_root), \
             patch("thread_logger._collect_git_diff") as mock_diff:
            mock_diff.return_value = {"files_changed": [], "commits": []}
            open_thread(
                branch="cursorcachat-test-subagents-aa11",
                initial_prompt="Need rollout help",
            )
            close_thread(
                branch="cursorcachat-test-subagents-aa11",
                session_title="Subagent Session",
                outcome="completed",
            )
            month = datetime.now(timezone.utc).strftime("%Y-%m")
            record = json.loads((log_dir / month / "aa11.json").read_text())
            assert record["transcript_id"] == parent_id
            assert record["subagent_count"] == 1
            assert record["subagents"][0]["subagent_id"] == "subagent-one"
            assert record["subagents"][0]["prompt_excerpt"] == "Explore rollout pattern"
            assert record["subagents"][0]["result_excerpt"] == "Found rollout summary"

    def test_close_removes_state_file(self, tmp_path):
        state_dir = tmp_path / ".thread-state"
        log_dir = tmp_path / "logs" / "threads"
        with patch("thread_logger.ACTIVE_STATE_DIR", state_dir), \
             patch("thread_logger.THREAD_LOG_DIR", log_dir), \
             patch("thread_logger._collect_git_diff") as mock_diff:
            mock_diff.return_value = {"files_changed": [], "commits": []}
            open_thread(
                branch="cursorcachat-test-ef56",
                initial_prompt="Test",
            )
            close_thread(
                branch="cursorcachat-test-ef56",
                session_title="Test",
                outcome="completed",
            )
            state_file = state_dir / "cursorcachat-test-ef56.json"
            assert not state_file.exists()

    def test_close_without_open_still_works(self, tmp_path):
        """Graceful degradation — if open was missed, close creates a minimal record."""
        state_dir = tmp_path / ".thread-state"
        log_dir = tmp_path / "logs" / "threads"
        with patch("thread_logger.ACTIVE_STATE_DIR", state_dir), \
             patch("thread_logger.THREAD_LOG_DIR", log_dir), \
             patch("thread_logger._collect_git_diff") as mock_diff:
            mock_diff.return_value = {"files_changed": [], "commits": []}
            close_thread(
                branch="cursorcachat-test-ae78",
                session_title="Orphan Close",
                outcome="completed",
            )
            month = datetime.now(timezone.utc).strftime("%Y-%m")
            thread_file = log_dir / month / "ae78.json"
            assert thread_file.exists()
            record = json.loads(thread_file.read_text())
            assert record["thread_id"] == "ae78"
            assert record["initial_prompt"] == "(not captured)"
            assert record["subagent_count"] == 0

    def test_concurrent_agents_no_conflict(self, tmp_path):
        """Two agents closing different threads write to different files — no conflict."""
        state_dir = tmp_path / ".thread-state"
        log_dir = tmp_path / "logs" / "threads"
        with patch("thread_logger.ACTIVE_STATE_DIR", state_dir), \
             patch("thread_logger.THREAD_LOG_DIR", log_dir), \
             patch("thread_logger._collect_git_diff") as mock_diff:
            mock_diff.return_value = {"files_changed": [], "commits": []}

            open_thread(branch="cursorcachat-agent-one-aa11", initial_prompt="Task A")
            open_thread(branch="cursorcachat-agent-two-bb22", initial_prompt="Task B")

            close_thread(branch="cursorcachat-agent-one-aa11", session_title="Agent 1", outcome="completed")
            close_thread(branch="cursorcachat-agent-two-bb22", session_title="Agent 2", outcome="completed")

            month = datetime.now(timezone.utc).strftime("%Y-%m")
            assert (log_dir / month / "aa11.json").exists()
            assert (log_dir / month / "bb22.json").exists()

            r1 = json.loads((log_dir / month / "aa11.json").read_text())
            r2 = json.loads((log_dir / month / "bb22.json").read_text())
            assert r1["thread_id"] == "aa11"
            assert r2["thread_id"] == "bb22"
            assert r1["initial_prompt"] == "Task A"
            assert r2["initial_prompt"] == "Task B"


# --- List / Summary ---


class TestListThreads:
    def test_list_empty(self, tmp_path):
        with patch("thread_logger.THREAD_LOG_DIR", tmp_path):
            results = list_threads()
            assert results == []

    def test_list_returns_records_from_per_thread_files(self, tmp_path):
        log_dir = tmp_path
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        month_dir = log_dir / month
        month_dir.mkdir(parents=True)
        record = {
            "thread_id": "ab12",
            "branch": "cursorcachat-test-ab12",
            "initial_prompt": "Test",
            "started_at": "2026-03-05T10:00:00+00:00",
            "outcome": "completed",
        }
        (month_dir / "ab12.json").write_text(json.dumps(record))
        with patch("thread_logger.THREAD_LOG_DIR", log_dir):
            results = list_threads()
            assert len(results) == 1
            assert results[0]["thread_id"] == "ab12"

    def test_list_filters_by_month(self, tmp_path):
        log_dir = tmp_path
        (log_dir / "2026-03").mkdir()
        (log_dir / "2026-02").mkdir()
        (log_dir / "2026-03" / "aaaa.json").write_text(json.dumps({"thread_id": "aaaa"}))
        (log_dir / "2026-02" / "bbbb.json").write_text(json.dumps({"thread_id": "bbbb"}))
        with patch("thread_logger.THREAD_LOG_DIR", log_dir):
            results = list_threads(month="2026-03")
            assert len(results) == 1
            assert results[0]["thread_id"] == "aaaa"

    def test_list_multiple_threads_in_month(self, tmp_path):
        log_dir = tmp_path
        month_dir = log_dir / "2026-03"
        month_dir.mkdir()
        (month_dir / "aa11.json").write_text(json.dumps({"thread_id": "aa11", "started_at": "2026-03-01T10:00:00+00:00"}))
        (month_dir / "bb22.json").write_text(json.dumps({"thread_id": "bb22", "started_at": "2026-03-02T10:00:00+00:00"}))
        (month_dir / "cc33.json").write_text(json.dumps({"thread_id": "cc33", "started_at": "2026-03-03T10:00:00+00:00"}))
        with patch("thread_logger.THREAD_LOG_DIR", log_dir):
            results = list_threads(month="2026-03")
            assert len(results) == 3

    def test_list_across_months(self, tmp_path):
        log_dir = tmp_path
        (log_dir / "2026-02").mkdir()
        (log_dir / "2026-03").mkdir()
        (log_dir / "2026-02" / "feb1.json").write_text(json.dumps({"thread_id": "feb1"}))
        (log_dir / "2026-03" / "mar1.json").write_text(json.dumps({"thread_id": "mar1"}))
        (log_dir / "2026-03" / "mar2.json").write_text(json.dumps({"thread_id": "mar2"}))
        with patch("thread_logger.THREAD_LOG_DIR", log_dir):
            results = list_threads()
            assert len(results) == 3

    def test_list_ignores_malformed_files(self, tmp_path):
        log_dir = tmp_path
        month_dir = log_dir / "2026-03"
        month_dir.mkdir()
        (month_dir / "good.json").write_text(json.dumps({"thread_id": "good"}))
        (month_dir / "bad.json").write_text("not json at all{{{")
        with patch("thread_logger.THREAD_LOG_DIR", log_dir):
            results = list_threads(month="2026-03")
            assert len(results) == 1
            assert results[0]["thread_id"] == "good"


class TestTranscriptBackfill:
    def test_backfill_creates_missing_thread_log_from_parent_transcript(self, tmp_path):
        log_dir = tmp_path / "logs" / "threads"
        transcript_root = tmp_path / "agent-transcripts"
        parent_id = "100b7f81-5b44-4646-a317-658bb00053c1"
        parent_dir = transcript_root / parent_id
        parent_dir.mkdir(parents=True)
        transcript_file = parent_dir / f"{parent_id}.jsonl"
        transcript_file.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "role": "user",
                            "message": {
                                "content": [
                                    {"type": "text", "text": "<user_query>\nNeed a coverage fix\n</user_query>"}
                                ]
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "role": "assistant",
                            "message": {"content": [{"type": "text", "text": "Working on it"}]},
                        }
                    ),
                ]
            )
            + "\n"
        )

        with patch("thread_logger.THREAD_LOG_DIR", log_dir), \
             patch("thread_logger.AGENT_TRANSCRIPTS_DIR", transcript_root), \
             patch("thread_logger._get_remote_url", return_value="newgumps/it-director"):
            created = backfill_threads_from_transcripts()

        assert created == 1
        month = datetime.fromtimestamp(transcript_file.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m")
        thread_file = log_dir / month / f"{parent_id}.json"
        assert thread_file.exists()
        record = json.loads(thread_file.read_text())
        assert record["thread_id"] == parent_id
        assert record["transcript_id"] == parent_id
        assert record["initial_prompt"] == "Need a coverage fix"
        assert record["subagent_count"] == 0
        assert record["backfilled_from_transcript"] is True

    def test_backfill_skips_transcript_when_matching_prompt_already_logged(self, tmp_path):
        log_dir = tmp_path / "logs" / "threads"
        month_dir = log_dir / "2026-03"
        month_dir.mkdir(parents=True)
        (month_dir / "existing.json").write_text(
            json.dumps(
                {
                    "thread_id": "existing",
                    "repo": "newgumps/it-director",
                    "initial_prompt": "Need a coverage fix",
                }
            )
        )
        transcript_root = tmp_path / "agent-transcripts"
        parent_id = "0a5befde-3987-465c-8ffa-0c94b54b296d"
        parent_dir = transcript_root / parent_id
        parent_dir.mkdir(parents=True)
        (parent_dir / f"{parent_id}.jsonl").write_text(
            json.dumps(
                {
                    "role": "user",
                    "message": {
                        "content": [{"type": "text", "text": "<user_query>\nNeed a coverage fix\n</user_query>"}]
                    },
                }
            )
            + "\n"
        )

        with patch("thread_logger.THREAD_LOG_DIR", log_dir), \
             patch("thread_logger.AGENT_TRANSCRIPTS_DIR", transcript_root):
            created = backfill_threads_from_transcripts()

        assert created == 0
        assert not any(path.name == f"{parent_id}.json" for path in month_dir.glob("*.json"))

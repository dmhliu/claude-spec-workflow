---
date: 2026-03-05
type: process
---

# Thread Data Logging

Per-thread input/output capture for Cursor agent sessions.

## Problem

Agent sessions produce valuable work, but the input (initial prompt) and output (files changed, commits, outcome) are never paired or stored together. The CHANGELOG captures outputs, but the prompts that drove them are lost. Without pairing input to output, there is no way to:

- Compare what was asked vs what was delivered
- Measure session duration or efficiency
- Identify patterns in successful vs. problematic sessions
- Build institutional knowledge about agent effectiveness

## Solution

A lightweight logging system that captures a structured record for every agent thread, stored as one JSON file per thread under monthly folders.

### Components

| Component | Path | Purpose |
|-----------|------|---------|
| Logger script | `scripts/thread_logger.py` | CLI tool: `open`, `close`, `list` commands |
| Cursor rule | `.cursor/rules/thread-logging.mdc` | Always-applied rule that tells agents to run the logger |
| Active state | `.thread-state/` (gitignored) | Ephemeral per-session state |
| Thread logs | `logs/threads/YYYY-MM/{thread_id}.json` | Per-thread files in monthly subdirs (committed) |
| S3 backup | `s3://gumps-it-artifacts/permanent/thread-logs/YYYY-MM/` | Permanent archive |

## Relationship To Knowledge Extraction

Thread logging is the raw capture layer. Prompt-derived knowledge extraction is a separate downstream process documented in `docs/processes/2026-03-07-thread-knowledge-extraction-pipeline.md`.

The layers are:

- **Raw**: local per-thread JSON plus central S3 mirror
- **Refined**: redacted structured dataset for analytics and clustering
- **Curated**: knowledge candidate queue for `knowledge-analyst` and `km-agent`

Thread logging should stay lightweight and deterministic. Knowledge extraction belongs in scheduled runtime, not in the close hook itself.

### Thread Record Schema

| Field | Type | Description |
|-------|------|-------------|
| `thread_id` | string | Short hex ID extracted from branch name |
| `branch` | string | Full Cursor-created branch name |
| `repo` | string | GitHub org/repo |
| `started_at` | ISO datetime | When the thread opened |
| `closed_at` | ISO datetime | When the thread closed |
| `duration_minutes` | float | Wall-clock session duration |
| `initial_prompt` | string | Full text of the user's first message |
| `session_title` | string | Session header from CHANGELOG |
| `git_base_sha` | string | HEAD SHA at thread start |
| `git_final_sha` | string | HEAD SHA at thread end |
| `files_changed` | string[] | Files modified during the session |
| `commits` | object[] | List of {sha, message} committed |
| `changelog_entries` | string[] | CHANGELOG lines from this session |
| `outcome` | enum | completed, partial, failed, abandoned |
| `tags` | string[] | Freeform categorization labels |
| `transcript_id` | string | Best-effort matching parent transcript UUID when a local transcript is found |
| `subagent_count` | integer | Number of sibling subagent transcripts found under the matched parent transcript |
| `subagents` | object[] | Best-effort summaries of subagent prompt/result pairs |

### Best-Effort Subagent Capture

When a matching parent transcript is available under the local transcript workspace, the close step attempts to:

1. Match the parent transcript by the first user prompt text.
2. Read any sibling `subagents/*.jsonl` files.
3. Persist lightweight subagent summaries into the raw thread record.

This is intentionally best-effort. If no transcript match is found, the thread log still closes normally with:

- `transcript_id = ""`
- `subagent_count = 0`
- `subagents = []`

The goal is to preserve useful subagent context without making thread closure depend on transcript availability.

### Thread ID

Extracted from the Cursor-created branch name:
- `cursorcachat-{slug}-{hex}` → `hex` (e.g., `43cd`)
- `cursor/{slug}-{id}` → `id`
- Fallback: 8-char UUID

### Deterministic Execution

| Phase | Mechanism | Trigger |
|-------|-----------|---------|
| Open | Always-applied Cursor rule | Agent reads user's first message |
| Close | Enhanced close-out checklist | Agent reaches end of session |

The always-applied rule (`thread-logging.mdc`) fires at the start of every conversation and instructs the agent to run the open command. The close-out checklist (extended in `changelog-rule.mdc`) includes running the close command before the final commit.

## Portfolio Rollout

Use `scripts/rollout_thread_logging.py` from the `it-director` repo to propagate the thread logging bundle to active sibling repos discovered by `scripts/list_dev_repos.py`.

### What it deploys

- `scripts/thread_logger.py`
- `.cursor/rules/thread-logging.mdc`
- `tests/test_thread_logger.py`
- `tests/test_thread_logger_cli.py`
- `docs/processes/THREAD_DATA_LOGGING.md`
- `.gitignore` entry for `.thread-state/`
- `changelog-rule.mdc` close-out upgrade so agents run `thread_logger.py close`

### Commands

```bash
# Preview target repos and pending changes
python3 scripts/rollout_thread_logging.py audit

# Roll out to all active repos
python3 scripts/rollout_thread_logging.py apply

# Limit to specific repos
python3 scripts/rollout_thread_logging.py audit --repo ccc-automation --repo mcp-gateway-v2
python3 scripts/rollout_thread_logging.py apply --repo ccc-automation --repo mcp-gateway-v2
```

The rollout intentionally skips obvious non-active repos like `*-old`, `*-deprecated`, and `jsrates-sandbox`.

## Usage

```bash
# Open a thread (agent does this automatically)
python3 scripts/thread_logger.py open \
  --branch "$(git branch --show-current)" \
  --prompt "user's first message"

# Close a thread (agent does this at session end)
python3 scripts/thread_logger.py close \
  --branch "$(git branch --show-current)" \
  --title "Session Title" \
  --outcome completed \
  --tags feature infrastructure \
  --s3-backup

# List threads
python3 scripts/thread_logger.py list
python3 scripts/thread_logger.py list --month 2026-03 --format json
```

## Analysis

```bash
# Count threads per month
ls logs/threads/2026-03/*.json | wc -l

# Average duration
python3 scripts/thread_logger.py list --format json | python3 -c "
import json, sys
records = json.load(sys.stdin)
durations = [r['duration_minutes'] for r in records if r.get('duration_minutes')]
print(f'Threads: {len(records)}, Avg duration: {sum(durations)/len(durations):.1f}m')
"

# Outcomes breakdown
python3 scripts/thread_logger.py list --format json | jq 'group_by(.outcome) | map({outcome: .[0].outcome, count: length})'

# Read a specific thread
cat logs/threads/2026-03/43cd.json | jq .
```

## Design Decisions

1. **Per-thread files over shared JSONL**: Each thread writes to `logs/threads/YYYY-MM/{thread_id}.json`. This eliminates merge conflicts when multiple cloud agents run concurrently — each agent writes to a unique file path. Monthly subdirectories keep the tree organized.

2. **Branch name as ID source**: Cursor cloud agents always create a branch. The hex suffix is unique per thread. No env var exposes a thread ID, so we parse the branch name.

3. **Gitignored active state**: `.thread-state/` is ephemeral per VM. Only the closed per-thread JSON files are committed. This avoids noise in git history during a session.

4. **Env var overrides**: `THREAD_LOG_STATE_DIR` and `THREAD_LOG_DIR` allow tests to run in isolation without polluting the workspace.

5. **Graceful degradation**: If the open step is missed, the close step still creates a minimal record with `(not captured)` as the prompt. No data is better than a crash.

6. **S3 permanent archive**: Thread logs under the `permanent/` prefix in the artifacts bucket transition to Glacier after 90 days — cheap long-term storage for historical analysis.

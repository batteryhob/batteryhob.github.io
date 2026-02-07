# CLAUDE.md

This repo has two things:

1. **Jekyll blog** — `batteryhob.github.io` (root level files)
2. **krim** — a Python CLI coding agent (`krim/` directory)

## krim

**Trust the model, keep the harness light.**

A thin CLI coding agent. 24 files, 2300 lines, 4 tools.

### Quick orientation

```
krim/
├── krim/              # package source (24 .py files)
│   ├── __main__.py    # CLI entry, interactive loop, slash commands
│   ├── agent.py       # core agent loop (330 lines, largest file)
│   ├── ui.py          # ASCII banner, prompt_toolkit input
│   ├── models/        # Claude + OpenAI providers
│   ├── tools/         # read, write, edit, bash
│   └── ...            # safety, compaction, config, mcp, skills, etc.
├── test_deep_verify.py  # 98-test verification suite
├── pyproject.toml     # package config, dependencies
├── examples/          # example .krim/ directory
└── README.md          # full docs
```

### Philosophy

1. **Trust the model** — 3-line system prompt. No sub-agents, no planning step.
2. **One file, one job** — Avg file is ~100 lines. Max is 330.
3. **Safe by default, overridable always** — deny > allow > ask. Every guard rail has `--no-*`.

### Key design decisions

- **Single agent loop**: `while turn < max_turns` in `agent.py`. Model calls tools, gets results, repeats. Break on text-only response.
- **Provider abstraction**: `models/base.py` defines `Model(ABC)` with `chat()`. Claude and OpenAI implement it. Agent doesn't know which.
- **Persistent bash cwd**: `__KRIM_CWD__` marker appended to every command. `rsplit` extracts new cwd from output. Exit code preserved via `$?`.
- **Compaction**: Phase 1 truncates old tool results. Phase 2 drops oldest message groups (tool_call + tool_result paired together to avoid API errors).
- **Doom loop**: Same tool call signature 3x in a row → force stop with summary prompt.
- **Fuzzy edit**: Exact match → whitespace-normalized → difflib fuzzy (0.8 threshold).
- **Layered config**: `~/.krim/` (global) → `.krim/` (project) → CLI flags.

### Running tests

```bash
cd krim
python test_deep_verify.py
```

Expects 98 PASS, 0 FAIL. No external API keys needed — tests use mock models.

### Dependencies

`anthropic`, `openai`, `rich`, `prompt_toolkit`. That's it.

### Bugs fixed (so you don't reintroduce them)

1. **Exit code lost in cwd tracking** — `false; echo MARKER; pwd` always exits 0. Fixed: capture `$?` before marker.
2. **Safety word boundary** — `lsblk` matched allow rule `ls`. Fixed: check `cmd == al` or `cmd.startswith(al + " ")`.
3. **Compaction orphan tool_calls** — Dropping messages individually could orphan tool_call references. Fixed: `_drop_oldest_group()` drops pairs.
4. **MAX_STEPS double-call** — Model completing on last turn still triggered MAX_STEPS_PROMPT. Fixed: `while-else` (else only runs when loop exhausts, not on break).
5. **MCP no timeout** — `_recv_raw` could hang forever. Fixed: `select.select()` with 60s timeout.
6. **deny_patterns false positive** — `"dd if="` matches `"add if="`. Known tradeoff, not fixed (fail-safe by design).

### Version

v0.3.0 — branch `claude/cli-model-iteration-tool-5NRpw`

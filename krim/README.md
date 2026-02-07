```
 ██╗  ██╗██████╗ ██╗███╗   ███╗
 ██║ ██╔╝██╔══██╗██║████╗ ████║
 █████╔╝ ██████╔╝██║██╔████╔██║
 ██╔═██╗ ██╔══██╗██║██║╚██╔╝██║
 ██║  ██╗██║  ██║██║██║ ╚═╝ ██║
 ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝
```

**Trust the model, keep the harness light.**

A thin CLI coding agent. 24 files, 2300 lines, 4 tools.

---

## Philosophy

1. **Trust the model** — 3-line system prompt. No scaffolding, no chain-of-thought wrappers, no sub-agents. The model decides what to do.
2. **One file, one job** — Every module does one thing. Largest file is 330 lines. Average is under 100.
3. **Safe by default, overridable always** — deny > allow > ask. Every guard rail has an off switch.

## Install

```bash
pip install -e .
```

Requires Python 3.10+ and an API key:

```bash
export ANTHROPIC_API_KEY="sk-..."   # for Claude (default)
export OPENAI_API_KEY="sk-..."      # for OpenAI
```

## Usage

```bash
# single prompt
krim "fix the failing test in test_api.py"

# interactive mode
krim

# options
krim --provider openai --model gpt-4o "refactor this"
krim --max-turns 20 "big refactor task"
krim --skill deploy "ship it"
krim --auto-commit "fix and commit"
krim --no-safety "run anything"
krim --verbose "debug this"
```

## Tools

| Tool | What it does |
|------|-------------|
| `bash` | Run shell commands. cwd persists across calls. Safety rules apply. |
| `read` | Read files with line numbers. Supports offset/limit for large files. |
| `write` | Write files. Creates parent directories. |
| `edit` | Replace strings in files. Exact match > whitespace-normalized > fuzzy (0.8 threshold). |

That's it. The model composes these four tools to do everything.

## Interactive Commands

```
/help      show commands
/tokens    token usage and stats
/compact   force context compaction
/config    show current configuration
/undo      undo last krim commit
/verbose   toggle verbose mode
exit       quit
```

Arrow keys navigate history. Tab completes commands.

## Configuration

Layered: `~/.krim/` (global) < `.krim/` (project) < CLI flags.

```
.krim/
├── config.json      # settings
├── KRIM.md          # instructions injected into system prompt
├── mcp.json         # MCP server configs
├── rules/
│   └── *.md         # additional rules
└── skills/
    └── <name>/
        └── SKILL.md # skill instructions
```

### config.json

```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "max_turns": 10,
  "auto_commit": false,
  "ask_by_default": true,
  "allow_commands": ["ls", "cat", "grep", "git status", "git diff", "pytest"],
  "deny_patterns": ["rm -rf /", "> /dev/sda", "mkfs."]
}
```

### KRIM.md

Free-form instructions appended to the system prompt. Use it for project-specific context:

```markdown
This is a Python FastAPI project. Tests are in tests/.
Run `pytest` to verify changes. Use ruff for linting.
Never modify alembic migrations directly.
```

### Skills

Reusable prompt packages. Activate with `--skill <name>`:

```bash
krim --skill deploy "ship the new feature"
krim --list-skills
```

### MCP

Connect external tool servers via [Model Context Protocol](https://modelcontextprotocol.io):

```json
{
  "mcpServers": {
    "web-search": {
      "command": ["node", "search-server/index.js"],
      "env": { "API_KEY": "..." }
    }
  }
}
```

## Safety

Commands go through a 3-tier check: **deny > allow > ask**.

- **deny**: substring match against dangerous patterns. Blocks immediately.
- **allow**: word-boundary match against safe command prefixes. Auto-approves.
- **ask**: everything else prompts the user for approval.

Override with `--no-safety` or set `"ask_by_default": false` in config.

## Architecture

```
krim/
├── __main__.py      # CLI entry, argument parsing, interactive loop
├── agent.py         # Core agent loop, doom detection, stats
├── ui.py            # Banner, prompt_toolkit input
├── prompt.py        # System prompt builder
├── config.py        # Layered config loader
├── context.py       # Environment context (cwd, git, file tree)
├── safety.py        # Bash command safety rules
├── compaction.py    # Token tracking, conversation compaction
├── truncate.py      # Output truncation (head/tail)
├── retry.py         # Exponential backoff
├── git.py           # Auto-commit, undo, selective staging
├── skills.py        # Skill discovery and injection
├── mcp.py           # MCP client (stdio, JSON-RPC)
├── models/
│   ├── base.py      # Abstract Model, ToolCall, ModelResponse
│   ├── claude.py    # Anthropic Claude provider
│   └── openai.py    # OpenAI provider
└── tools/
    ├── base.py      # Abstract Tool with schema generation
    ├── bash.py      # Shell execution, persistent cwd
    ├── read.py      # File reading with line numbers
    ├── write.py     # File writing
    └── edit.py      # String replacement with fuzzy matching
```

### How the loop works

```
User input
    ↓
[System prompt + context + history]
    ↓
Model → text response? → done
      → tool calls?    → execute each → append results → loop
      → doom loop?     → force stop with summary
      → max turns?     → force stop with summary
      → token limit?   → compact history, continue
```

Single loop. No routing, no planning step, no sub-agents.

### Compaction

When conversation approaches the token limit (~90K tokens):
1. **Phase 1**: Truncate old tool results to 100 chars
2. **Phase 2**: Drop oldest message groups (tool_call + tool_result pairs together, never orphaning references)

### Providers

Claude and OpenAI share the same `Model` interface. The agent doesn't know which one it's talking to — message format conversion happens in the provider layer.

## License

MIT

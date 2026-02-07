#!/usr/bin/env python3
"""Deep verification test suite for krim v0.3.0.

Goes beyond basic unit tests to cover:
- Cross-module interaction patterns
- Edge cases in message format integrity
- Safety rule boundary conditions
- Bash CWD with failing commands
- Compaction paired dropping under complex scenarios
- Edit tool fuzzy matching edge cases
- Agent doom loop near-threshold behavior
- Config merging edge cases
- Git staging patterns
- Model message format integrity
"""

import sys
import os
import json
import tempfile
import shutil

# ensure krim package is importable
sys.path.insert(0, os.path.dirname(__file__))

PASS = 0
FAIL = 0
ERRORS = []

def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        PASS += 1
        print(f"  PASS  {name}")
    except Exception as e:
        FAIL += 1
        ERRORS.append((name, str(e)))
        print(f"  FAIL  {name}: {e}")

# ============================================================
# 1. SAFETY MODULE - Edge Cases
# ============================================================
print("\n=== SAFETY MODULE ===")

def test_safety_word_boundary_ls():
    from krim.safety import Action, check_command
    # "ls" should be allowed, "lsblk" should NOT be auto-allowed
    assert check_command("ls", [], ["ls"], True) == Action.ALLOW
    assert check_command("lsblk", [], ["ls"], True) == Action.ASK  # not ALLOW
    assert check_command("ls -la", [], ["ls"], True) == Action.ALLOW
    assert check_command("ls\t-la", [], ["ls"], True) == Action.ALLOW
test("safety: word boundary ls vs lsblk", test_safety_word_boundary_ls)

def test_safety_git_commands():
    from krim.safety import Action, check_command
    allow = ["git status", "git diff", "git log"]
    assert check_command("git status", [], allow, True) == Action.ALLOW
    assert check_command("git status --short", [], allow, True) == Action.ALLOW
    assert check_command("git stash", [], allow, True) == Action.ASK  # NOT allowed
    assert check_command("git statusx", [], allow, True) == Action.ASK  # NOT allowed
test("safety: git command word boundaries", test_safety_git_commands)

def test_safety_deny_priority():
    from krim.safety import Action, check_command
    # deny takes priority over allow
    assert check_command("rm -rf /", ["rm -rf /"], ["rm"], True) == Action.DENY
test("safety: deny > allow priority", test_safety_deny_priority)

def test_safety_pipe_commands():
    from krim.safety import Action, check_command
    # piped commands: "cat foo | grep bar" - first command is "cat foo | grep bar"
    # the allow check is on the full command string
    assert check_command("cat foo | grep bar", [], ["cat"], True) == Action.ALLOW
    # but deny patterns match anywhere in the string
    assert check_command("cat foo | rm -rf /", ["rm -rf /"], ["cat"], True) == Action.DENY
test("safety: pipe commands", test_safety_pipe_commands)

def test_safety_semicolon_commands():
    from krim.safety import Action, check_command
    # semicolons: "ls; rm -rf /"
    assert check_command("ls; rm -rf /", ["rm -rf /"], ["ls"], True) == Action.DENY
test("safety: semicolon + deny pattern", test_safety_semicolon_commands)

def test_safety_deny_dd_false_positive():
    from krim.safety import Action, check_command
    # "dd if=" deny pattern: does "add if=something" trigger it?
    result = check_command("add if=something", ["dd if="], [], True)
    # This IS a known false positive - "dd if=" matches substring in "add if="
    # Document the behavior
    assert result == Action.DENY  # current behavior: false positive
test("safety: deny 'dd if=' false positive in 'add if='", test_safety_deny_dd_false_positive)

def test_safety_case_insensitive():
    from krim.safety import Action, check_command
    assert check_command("LS", [], ["ls"], True) == Action.ALLOW
    assert check_command("RM -RF /", ["rm -rf /"], [], True) == Action.DENY
test("safety: case insensitive matching", test_safety_case_insensitive)

def test_safety_empty_command():
    from krim.safety import Action, check_command
    assert check_command("", [], ["ls"], True) == Action.ASK
    assert check_command("   ", [], ["ls"], True) == Action.ASK
test("safety: empty/whitespace command", test_safety_empty_command)

def test_safety_exact_match_only():
    from krim.safety import Action, check_command
    # "python -c" allows "python -c 'print(1)'" but not "python -cx"
    assert check_command("python -c 'print(1)'", [], ["python -c"], True) == Action.ALLOW
    assert check_command("python -cx", [], ["python -c"], True) == Action.ASK
test("safety: exact prefix with space/tab", test_safety_exact_match_only)

def test_safety_no_safety_mode():
    from krim.safety import Action, check_command
    # ask_by_default=False means everything not denied is allowed
    assert check_command("anything", [], [], False) == Action.ALLOW
    assert check_command("rm -rf /", ["rm -rf /"], [], False) == Action.DENY
test("safety: no-safety mode", test_safety_no_safety_mode)

# ============================================================
# 2. BASH TOOL - Edge Cases
# ============================================================
print("\n=== BASH TOOL ===")

def test_bash_cwd_persistence():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt._ask_by_default = False
    original = bt.cwd
    bt.run("cd /tmp")
    assert bt.cwd == "/tmp", f"expected /tmp, got {bt.cwd}"
    bt.run("cd /")
    assert bt.cwd == "/", f"expected /, got {bt.cwd}"
test("bash: cwd persistence across calls", test_bash_cwd_persistence)

def test_bash_cwd_on_failure():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt._ask_by_default = False
    bt.run("cd /tmp")
    assert bt.cwd == "/tmp"
    # failing command should still track cwd (it doesn't change)
    result = bt.run("false")
    assert bt.cwd == "/tmp", f"cwd changed after failure: {bt.cwd}"
    assert "exit code" in result
test("bash: cwd preserved after failing command", test_bash_cwd_on_failure)

def test_bash_exit_code_preservation():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt._ask_by_default = False
    result = bt.run("exit 42")
    assert "[exit code: 42]" in result, f"exit code not preserved: {result}"
test("bash: exit code preservation", test_bash_exit_code_preservation)

def test_bash_exit_code_false():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt._ask_by_default = False
    result = bt.run("false")
    assert "[exit code: 1]" in result, f"false exit code wrong: {result}"
test("bash: false command exit code", test_bash_exit_code_false)

def test_bash_multiline_command():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt._ask_by_default = False
    result = bt.run("echo line1\necho line2\necho line3")
    assert "line1" in result
    assert "line2" in result
    assert "line3" in result
test("bash: multi-line command", test_bash_multiline_command)

def test_bash_cd_nonexistent():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt._ask_by_default = False
    original = bt.cwd
    result = bt.run("cd /nonexistent_dir_xyz")
    assert bt.cwd == original, f"cwd changed to nonexistent: {bt.cwd}"
    assert "exit code" in result or "No such" in result
test("bash: cd to nonexistent dir", test_bash_cd_nonexistent)

def test_bash_marker_in_output():
    """Command output containing the CWD marker should not break tracking."""
    from krim.tools.bash import BashTool, _CWD_MARKER
    bt = BashTool()
    bt._ask_by_default = False
    bt.run("cd /tmp")
    # output the marker string as part of the command
    result = bt.run(f'echo "prefix {_CWD_MARKER} suffix"')
    # cwd should still be /tmp (last marker wins via rsplit)
    assert bt.cwd == "/tmp", f"cwd corrupted by marker in output: {bt.cwd}"
test("bash: CWD marker in command output", test_bash_marker_in_output)

def test_bash_timeout():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt._ask_by_default = False
    result = bt.run("sleep 10", timeout=1)
    assert "timed out" in result
test("bash: command timeout", test_bash_timeout)

def test_bash_denied_command():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt.configure(
        deny_patterns=["rm -rf /"],
        allow_commands=[],
        ask_by_default=False,
    )
    result = bt.run("rm -rf /")
    assert "denied" in result
test("bash: denied command", test_bash_denied_command)

def test_bash_stderr_captured():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt._ask_by_default = False
    result = bt.run("echo err >&2")
    assert "err" in result
test("bash: stderr captured", test_bash_stderr_captured)

def test_bash_no_output():
    from krim.tools.bash import BashTool
    bt = BashTool()
    bt._ask_by_default = False
    result = bt.run("true")
    assert result == "(no output)"
test("bash: no output returns (no output)", test_bash_no_output)

# ============================================================
# 3. COMPACTION - Edge Cases
# ============================================================
print("\n=== COMPACTION ===")

def test_compact_short_messages():
    from krim.compaction import compact
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    result = compact(msgs)
    assert len(result) == 3  # no compaction on short conversations
test("compaction: short conversations untouched", test_compact_short_messages)

def test_compact_paired_drop_claude():
    """Tool use + tool result must be dropped together (Claude format)."""
    from krim.compaction import _drop_oldest_group
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": [
            {"type": "text", "text": "let me read"},
            {"type": "tool_use", "id": "t1", "name": "read", "input": {"path": "f.py"}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "file contents"},
        ]},
        {"role": "user", "content": "thanks"},
    ]
    original_len = len(msgs)
    dropped = _drop_oldest_group(msgs, 1)
    assert dropped
    # should drop both assistant(tool_use) + user(tool_result) = 2 messages
    assert len(msgs) == original_len - 2, f"expected {original_len-2}, got {len(msgs)}"
    # remaining: system + user("thanks")
    assert msgs[0]["role"] == "system"
    assert msgs[1]["content"] == "thanks"
test("compaction: paired drop claude format", test_compact_paired_drop_claude)

def test_compact_paired_drop_openai():
    """Tool use + tool result must be dropped together (OpenAI format)."""
    from krim.compaction import _drop_oldest_group
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": "thinking", "tool_calls": [
            {"id": "t1", "type": "function", "function": {"name": "bash", "arguments": "{}"}},
        ]},
        {"role": "tool", "tool_call_id": "t1", "content": "output"},
        {"role": "user", "content": "ok"},
    ]
    original_len = len(msgs)
    dropped = _drop_oldest_group(msgs, 1)
    assert dropped
    # should drop assistant(tool_calls) + tool result = 2 messages
    assert len(msgs) == original_len - 2, f"expected {original_len-2}, got {len(msgs)}"
test("compaction: paired drop openai format", test_compact_paired_drop_openai)

def test_compact_multi_tool_results():
    """Assistant with multiple tool_calls should drop all following tool results."""
    from krim.compaction import _drop_oldest_group
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t1", "name": "read", "input": {}},
            {"type": "tool_use", "id": "t2", "name": "bash", "input": {}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "r1"},
            {"type": "tool_result", "tool_use_id": "t2", "content": "r2"},
        ]},
        {"role": "user", "content": "next"},
    ]
    dropped = _drop_oldest_group(msgs, 1)
    assert dropped
    # should drop assistant + tool_results = 2 messages
    assert len(msgs) == 2  # system + "next"
test("compaction: multi-tool paired drop", test_compact_multi_tool_results)

def test_compact_openai_multi_tool_results():
    """OpenAI format: assistant(tool_calls) + multiple tool messages."""
    from krim.compaction import _drop_oldest_group
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "assistant", "tool_calls": [
            {"id": "t1", "type": "function", "function": {"name": "read", "arguments": "{}"}},
            {"id": "t2", "type": "function", "function": {"name": "bash", "arguments": "{}"}},
        ]},
        {"role": "tool", "tool_call_id": "t1", "content": "r1"},
        {"role": "tool", "tool_call_id": "t2", "content": "r2"},
        {"role": "user", "content": "next"},
    ]
    dropped = _drop_oldest_group(msgs, 1)
    assert dropped
    # should drop assistant + 2 tool messages = 3
    assert len(msgs) == 2  # system + "next"
test("compaction: openai multi-tool paired drop", test_compact_openai_multi_tool_results)

def test_compact_user_assistant_pair():
    from krim.compaction import _drop_oldest_group
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "user", "content": "next"},
    ]
    dropped = _drop_oldest_group(msgs, 1)
    assert dropped
    assert len(msgs) == 2  # system + "next"
test("compaction: user+assistant pair drop", test_compact_user_assistant_pair)

def test_compact_token_estimation():
    from krim.compaction import estimate_tokens, estimate_message_tokens
    assert estimate_tokens("") == 0
    assert estimate_tokens("abc") == 1  # 3 chars / 3
    assert estimate_tokens("abcdef") == 2  # 6 chars / 3
    msgs = [{"role": "user", "content": "x" * 300}]
    assert estimate_message_tokens(msgs) == 100  # 300/3
test("compaction: token estimation", test_compact_token_estimation)

def test_compact_needs_compaction():
    from krim.compaction import needs_compaction
    short = [{"role": "user", "content": "hi"}]
    assert not needs_compaction(short)
    # 120_000 * 0.75 = 90_000 tokens = 270_000 chars
    long_msg = [{"role": "user", "content": "x" * 300_000}]
    assert needs_compaction(long_msg)
test("compaction: needs_compaction threshold", test_compact_needs_compaction)

def test_compact_phase1_truncate():
    """Phase 1 should truncate old tool results but keep recent ones intact."""
    from krim.compaction import compact
    big_result = "x" * 1000
    msgs = [
        {"role": "system", "content": "s"},
        # old tool result (should be truncated)
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": big_result},
        ]},
        # padding messages to make total > 6 after system
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "u3"},
        {"role": "assistant", "content": "a3"},
        {"role": "user", "content": "u4"},
        {"role": "assistant", "content": "a4"},
    ]
    result = compact(msgs)
    # check that old tool result was truncated
    old_tool = result[1]["content"][0]["content"]
    assert len(old_tool) < len(big_result), f"tool result not truncated: {len(old_tool)}"
    assert "[compacted]" in old_tool
test("compaction: phase 1 truncates old tool results", test_compact_phase1_truncate)

def test_compact_no_mutation():
    """Compaction should not mutate original messages."""
    from krim.compaction import compact
    big_result = "x" * 1000
    original_block = {"type": "tool_result", "tool_use_id": "t1", "content": big_result}
    msgs = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": [original_block]},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "u3"},
        {"role": "assistant", "content": "a3"},
        {"role": "user", "content": "u4"},
        {"role": "assistant", "content": "a4"},
    ]
    compact(msgs)
    # original block must not be mutated
    assert original_block["content"] == big_result, "original message was mutated!"
test("compaction: no mutation of originals", test_compact_no_mutation)

# ============================================================
# 4. EDIT TOOL - Edge Cases
# ============================================================
print("\n=== EDIT TOOL ===")

def test_edit_exact_match():
    from krim.tools.edit import EditTool
    et = EditTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo():\n    return 1\n")
        f.flush()
        path = f.name
    try:
        result = et.run(path, "return 1", "return 2")
        assert "exact match" in result
        with open(path) as fh:
            assert "return 2" in fh.read()
    finally:
        os.unlink(path)
test("edit: exact match", test_edit_exact_match)

def test_edit_multiple_matches():
    from krim.tools.edit import EditTool
    et = EditTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("x = 1\nx = 1\n")
        f.flush()
        path = f.name
    try:
        result = et.run(path, "x = 1", "x = 2")
        assert "found 2 times" in result
    finally:
        os.unlink(path)
test("edit: multiple matches error", test_edit_multiple_matches)

def test_edit_whitespace_normalized():
    from krim.tools.edit import EditTool
    et = EditTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def  foo(  ):\n    return   1\n")
        f.flush()
        path = f.name
    try:
        result = et.run(path, "def foo():\n    return 1", "def bar():\n    return 2")
        assert "whitespace" in result or "fuzzy" in result, f"unexpected: {result}"
    finally:
        os.unlink(path)
test("edit: whitespace-normalized match", test_edit_whitespace_normalized)

def test_edit_fuzzy_match():
    from krim.tools.edit import EditTool
    et = EditTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        # slightly different content
        f.write("def calculate_total(items):\n    total = sum(items)\n    return total\n")
        f.flush()
        path = f.name
    try:
        # model provides slightly wrong version (typo in variable name)
        result = et.run(path,
            "def calculate_total(items):\n    totl = sum(items)\n    return totl",
            "def calculate_total(items):\n    result = sum(items)\n    return result")
        assert "fuzzy" in result, f"expected fuzzy match: {result}"
    finally:
        os.unlink(path)
test("edit: fuzzy match", test_edit_fuzzy_match)

def test_edit_no_match():
    from krim.tools.edit import EditTool
    et = EditTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("def foo():\n    return 1\n")
        f.flush()
        path = f.name
    try:
        result = et.run(path, "completely different content xyz", "new content")
        assert "not found" in result
    finally:
        os.unlink(path)
test("edit: no match at all", test_edit_no_match)

def test_edit_nonexistent_file():
    from krim.tools.edit import EditTool
    et = EditTool()
    result = et.run("/nonexistent/file.py", "old", "new")
    assert "not found" in result
test("edit: nonexistent file", test_edit_nonexistent_file)

def test_edit_empty_file():
    from krim.tools.edit import EditTool
    et = EditTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("")
        f.flush()
        path = f.name
    try:
        result = et.run(path, "something", "new")
        assert "not found" in result
    finally:
        os.unlink(path)
test("edit: empty file", test_edit_empty_file)

def test_edit_tilde_expansion():
    from krim.tools.edit import EditTool
    et = EditTool()
    result = et.run("~/nonexistent_file_xyz.py", "old", "new")
    assert "not found" in result
test("edit: tilde expansion", test_edit_tilde_expansion)

# ============================================================
# 5. READ TOOL - Edge Cases
# ============================================================
print("\n=== READ TOOL ===")

def test_read_basic():
    from krim.tools.read import ReadTool
    rt = ReadTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("line1\nline2\nline3\n")
        f.flush()
        path = f.name
    try:
        result = rt.run(path)
        assert "line1" in result
        assert "line2" in result
        assert "line3" in result
    finally:
        os.unlink(path)
test("read: basic file read", test_read_basic)

def test_read_offset_limit():
    from krim.tools.read import ReadTool
    rt = ReadTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        for i in range(100):
            f.write(f"line {i}\n")
        f.flush()
        path = f.name
    try:
        result = rt.run(path, offset=10, limit=5)
        assert "line 9" in result  # 0-indexed content, 1-indexed display
        assert "line 13" in result
        assert "line 15" not in result  # beyond limit
    finally:
        os.unlink(path)
test("read: offset and limit", test_read_offset_limit)

def test_read_nonexistent():
    from krim.tools.read import ReadTool
    rt = ReadTool()
    result = rt.run("/nonexistent/file.py")
    assert "not found" in result
test("read: nonexistent file", test_read_nonexistent)

def test_read_file_size_limit():
    from krim.tools.read import ReadTool
    rt = ReadTool()
    # create a file that exceeds MAX_FILE_SIZE
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        path = f.name
    try:
        # mock os.path.getsize to return > 10MB
        original_getsize = os.path.getsize
        os.path.getsize = lambda p: 20 * 1024 * 1024  # 20MB
        try:
            result = rt.run(path)
            assert "too large" in result
        finally:
            os.path.getsize = original_getsize
    finally:
        os.unlink(path)
test("read: file size limit", test_read_file_size_limit)

def test_read_empty_file():
    from krim.tools.read import ReadTool
    rt = ReadTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("")
        f.flush()
        path = f.name
    try:
        result = rt.run(path)
        assert result == ""  # empty file = empty result
    finally:
        os.unlink(path)
test("read: empty file", test_read_empty_file)

def test_read_tilde():
    from krim.tools.read import ReadTool
    rt = ReadTool()
    result = rt.run("~/nonexistent_xyz.py")
    assert "not found" in result
test("read: tilde expansion", test_read_tilde)

# ============================================================
# 6. WRITE TOOL - Edge Cases
# ============================================================
print("\n=== WRITE TOOL ===")

def test_write_creates_parent():
    from krim.tools.write import WriteTool
    wt = WriteTool()
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "sub", "dir", "file.py")
        result = wt.run(path, "hello")
        assert "wrote" in result
        with open(path) as f:
            assert f.read() == "hello"
test("write: creates parent directories", test_write_creates_parent)

def test_write_line_count():
    from krim.tools.write import WriteTool
    wt = WriteTool()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        path = f.name
    try:
        result = wt.run(path, "a\nb\nc\n")
        assert "3 lines" in result
        result = wt.run(path, "single")
        assert "1 lines" in result
        result = wt.run(path, "")
        assert "0 lines" in result
    finally:
        os.unlink(path)
test("write: line count reporting", test_write_line_count)

# ============================================================
# 7. TRUNCATE - Edge Cases
# ============================================================
print("\n=== TRUNCATE ===")

def test_truncate_short():
    from krim.truncate import truncate
    assert truncate("short", 100) == "short"
test("truncate: short text unchanged", test_truncate_short)

def test_truncate_exact_boundary():
    from krim.truncate import truncate
    text = "x" * 100
    assert truncate(text, 100) == text  # exactly at limit
    assert truncate(text, 99) != text  # just over limit
test("truncate: exact boundary", test_truncate_exact_boundary)

def test_truncate_head_tail():
    from krim.truncate import truncate
    text = "A" * 100 + "B" * 100
    result = truncate(text, 50)
    assert "A" in result  # head preserved
    assert "B" in result  # tail preserved
    assert "truncated" in result
test("truncate: head/tail preservation", test_truncate_head_tail)

def test_truncate_empty():
    from krim.truncate import truncate
    assert truncate("", 100) == ""
test("truncate: empty string", test_truncate_empty)

# ============================================================
# 8. AGENT - Message Format Integrity
# ============================================================
print("\n=== AGENT MESSAGE FORMAT ===")

def test_agent_claude_assistant_msg():
    from krim.agent import _build_assistant_msg_claude
    from krim.models.base import ModelResponse, ToolCall
    resp = ModelResponse(
        text="thinking...",
        tool_calls=[ToolCall(id="t1", name="bash", args={"command": "ls"})],
        stop=False,
    )
    msg = _build_assistant_msg_claude(resp)
    assert msg["role"] == "assistant"
    assert isinstance(msg["content"], list)
    assert len(msg["content"]) == 2
    assert msg["content"][0] == {"type": "text", "text": "thinking..."}
    assert msg["content"][1]["type"] == "tool_use"
    assert msg["content"][1]["id"] == "t1"
    assert msg["content"][1]["name"] == "bash"
    assert msg["content"][1]["input"] == {"command": "ls"}
test("agent: claude assistant message format", test_agent_claude_assistant_msg)

def test_agent_claude_assistant_text_only():
    from krim.agent import _build_assistant_msg_claude
    from krim.models.base import ModelResponse
    resp = ModelResponse(text="just text", tool_calls=[], stop=True)
    msg = _build_assistant_msg_claude(resp)
    assert msg["content"] == [{"type": "text", "text": "just text"}]
test("agent: claude text-only message", test_agent_claude_assistant_text_only)

def test_agent_openai_assistant_msg():
    from krim.agent import _build_assistant_msg_openai
    from krim.models.base import ModelResponse, ToolCall
    resp = ModelResponse(
        text="thinking...",
        tool_calls=[ToolCall(id="t1", name="bash", args={"command": "ls"})],
        stop=False,
    )
    msg = _build_assistant_msg_openai(resp)
    assert msg["role"] == "assistant"
    assert msg["content"] == "thinking..."
    assert len(msg["tool_calls"]) == 1
    assert msg["tool_calls"][0]["id"] == "t1"
    assert msg["tool_calls"][0]["type"] == "function"
    assert msg["tool_calls"][0]["function"]["name"] == "bash"
    assert json.loads(msg["tool_calls"][0]["function"]["arguments"]) == {"command": "ls"}
test("agent: openai assistant message format", test_agent_openai_assistant_msg)

def test_agent_openai_tool_result():
    from krim.agent import _build_tool_result_openai
    msg = _build_tool_result_openai("t1", "bash", "output here")
    assert msg == {
        "role": "tool",
        "tool_call_id": "t1",
        "name": "bash",
        "content": "output here",
    }
test("agent: openai tool result format", test_agent_openai_tool_result)

def test_agent_claude_no_text():
    """Claude message with tool calls but no text."""
    from krim.agent import _build_assistant_msg_claude
    from krim.models.base import ModelResponse, ToolCall
    resp = ModelResponse(
        text=None,
        tool_calls=[ToolCall(id="t1", name="read", args={"path": "f.py"})],
        stop=False,
    )
    msg = _build_assistant_msg_claude(resp)
    # no text block, only tool_use block
    assert len(msg["content"]) == 1
    assert msg["content"][0]["type"] == "tool_use"
test("agent: claude message without text", test_agent_claude_no_text)

def test_agent_openai_no_text():
    """OpenAI message with tool calls but no text."""
    from krim.agent import _build_assistant_msg_openai
    from krim.models.base import ModelResponse, ToolCall
    resp = ModelResponse(
        text=None,
        tool_calls=[ToolCall(id="t1", name="read", args={"path": "f.py"})],
        stop=False,
    )
    msg = _build_assistant_msg_openai(resp)
    assert "content" not in msg  # no content key when text is None
    assert len(msg["tool_calls"]) == 1
test("agent: openai message without text", test_agent_openai_no_text)

# ============================================================
# 9. AGENT - Doom Loop Detection
# ============================================================
print("\n=== DOOM LOOP DETECTION ===")

def test_doom_loop_detection():
    from krim.agent import Agent
    from krim.models.base import Model, ModelResponse, ToolCall

    class MockModel(Model):
        def chat(self, messages, tools, stream_callback=None):
            return ModelResponse(text="ok", tool_calls=[], stop=True)

    agent = Agent(MockModel(), "claude", "sys", [], max_turns=10)

    tc = [ToolCall(id="t1", name="bash", args={"command": "ls"})]
    assert not agent._check_doom_loop(tc)
    assert not agent._check_doom_loop(tc)
    assert agent._check_doom_loop(tc)  # 3rd time triggers
test("doom loop: triggers on 3rd identical call", test_doom_loop_detection)

def test_doom_loop_different_calls():
    from krim.agent import Agent
    from krim.models.base import Model, ModelResponse, ToolCall

    class MockModel(Model):
        def chat(self, messages, tools, stream_callback=None):
            return ModelResponse(text="ok", tool_calls=[], stop=True)

    agent = Agent(MockModel(), "claude", "sys", [], max_turns=10)

    tc1 = [ToolCall(id="t1", name="bash", args={"command": "ls"})]
    tc2 = [ToolCall(id="t2", name="bash", args={"command": "pwd"})]
    assert not agent._check_doom_loop(tc1)
    assert not agent._check_doom_loop(tc2)
    assert not agent._check_doom_loop(tc1)  # alternating, no doom
test("doom loop: different calls don't trigger", test_doom_loop_different_calls)

def test_doom_loop_reset_on_run():
    from krim.agent import Agent, RunStats
    from krim.models.base import Model, ModelResponse, ToolCall

    class MockModel(Model):
        def chat(self, messages, tools, stream_callback=None):
            return ModelResponse(text="done", tool_calls=[], stop=True)

    agent = Agent(MockModel(), "claude", "sys", [], max_turns=2)
    # populate doom history
    tc = [ToolCall(id="t1", name="bash", args={"command": "ls"})]
    agent._check_doom_loop(tc)
    agent._check_doom_loop(tc)
    # run() should clear _recent_calls
    agent.run("test")
    # after run, history should be empty
    assert len(agent._recent_calls) == 0
test("doom loop: reset on new run()", test_doom_loop_reset_on_run)

# ============================================================
# 10. AGENT - Max Turns Bug
# ============================================================
print("\n=== AGENT MAX TURNS ===")

def test_agent_max_turns_no_double_call():
    """Model completes naturally on last turn -> no MAX_STEPS_PROMPT should fire."""
    from krim.agent import Agent
    from krim.models.base import Model, ModelResponse

    call_count = 0
    class CountModel(Model):
        def chat(self, messages, tools, stream_callback=None):
            nonlocal call_count
            call_count += 1
            return ModelResponse(text=f"response {call_count}", tool_calls=[], stop=True)

    agent = Agent(CountModel(), "claude", "sys", [], max_turns=1)
    agent.run("test")

    # Model completes on last turn with no tool calls -> should NOT fire MAX_STEPS_PROMPT
    assert call_count == 1, f"double-call bug: model called {call_count} times instead of 1"
test("agent: no double-call when model completes on last turn", test_agent_max_turns_no_double_call)

def test_agent_max_turns_fires_when_tools_pending():
    """When all turns used up with tool calls still pending, MAX_STEPS_PROMPT should fire."""
    from krim.agent import Agent
    from krim.tools import create_tools
    from krim.models.base import Model, ModelResponse, ToolCall

    call_count = 0
    class ToolModel(Model):
        def chat(self, messages, tools, stream_callback=None):
            nonlocal call_count
            call_count += 1
            if tools:  # tools available = main loop
                return ModelResponse(
                    text=None,
                    tool_calls=[ToolCall(id=f"t{call_count}", name="bash", args={"command": f"echo {call_count}"})],
                    stop=False,
                )
            else:  # no tools = MAX_STEPS_PROMPT summary call
                return ModelResponse(text="summary", tool_calls=[], stop=True)

    tools = create_tools()
    from krim.tools.bash import BashTool
    for t in tools:
        if isinstance(t, BashTool):
            t._ask_by_default = False

    agent = Agent(ToolModel(), "claude", "sys", tools, max_turns=2)
    agent.run("test")

    # 2 turns of tool calls + 1 summary call = 3
    assert call_count == 3, f"expected 3 calls (2 tool + 1 summary), got {call_count}"
test("agent: MAX_STEPS fires when tools pending at max turns", test_agent_max_turns_fires_when_tools_pending)

# ============================================================
# 11. TOOL REGISTRY
# ============================================================
print("\n=== TOOL REGISTRY ===")

def test_tool_registry():
    from krim.tools import create_tools, get_tool, tool_schemas
    tools = create_tools()
    assert len(tools) == 4
    names = {t.name for t in tools}
    assert names == {"read", "write", "edit", "bash"}
test("registry: creates 4 tools", test_tool_registry)

def test_tool_schemas():
    from krim.tools import create_tools, tool_schemas
    tools = create_tools()
    schemas = tool_schemas(tools)
    assert len(schemas) == 4
    for s in schemas:
        assert "name" in s
        assert "description" in s
        assert "input_schema" in s
        assert s["input_schema"]["type"] == "object"
        assert "properties" in s["input_schema"]
        assert "required" in s["input_schema"]
test("registry: schemas have correct structure", test_tool_schemas)

def test_tool_schema_optional():
    """Optional parameters should NOT be in required list."""
    from krim.tools import create_tools, tool_schemas
    tools = create_tools()
    schemas = tool_schemas(tools)
    # bash has "timeout" as optional
    bash_schema = next(s for s in schemas if s["name"] == "bash")
    assert "command" in bash_schema["input_schema"]["required"]
    assert "timeout" not in bash_schema["input_schema"]["required"]
    # read has "offset" and "limit" as optional
    read_schema = next(s for s in schemas if s["name"] == "read")
    assert "path" in read_schema["input_schema"]["required"]
    assert "offset" not in read_schema["input_schema"]["required"]
    assert "limit" not in read_schema["input_schema"]["required"]
test("registry: optional params excluded from required", test_tool_schema_optional)

def test_tool_schema_no_optional_key():
    """'optional' key should be stripped from properties in schema."""
    from krim.tools import create_tools, tool_schemas
    tools = create_tools()
    schemas = tool_schemas(tools)
    for s in schemas:
        for prop_name, prop_val in s["input_schema"]["properties"].items():
            assert "optional" not in prop_val, \
                f"'optional' key leaked into schema for {s['name']}.{prop_name}"
test("registry: 'optional' key stripped from schema properties", test_tool_schema_no_optional_key)

# ============================================================
# 12. GET_TOOL lookup
# ============================================================
print("\n=== TOOL LOOKUP ===")

def test_get_tool_found():
    from krim.tools import create_tools, get_tool
    tools = create_tools()
    assert get_tool(tools, "bash") is not None
    assert get_tool(tools, "read") is not None
test("get_tool: finds existing tool", test_get_tool_found)

def test_get_tool_not_found():
    from krim.tools import create_tools, get_tool
    tools = create_tools()
    assert get_tool(tools, "nonexistent") is None
test("get_tool: returns None for unknown", test_get_tool_not_found)

# ============================================================
# 13. CONFIG MERGING
# ============================================================
print("\n=== CONFIG ===")

def test_config_merge():
    from krim.config import _merge_config
    base = {"a": 1, "b": {"x": 1, "y": 2}}
    override = {"b": {"y": 3, "z": 4}, "c": 5}
    result = _merge_config(base, override)
    assert result == {"a": 1, "b": {"x": 1, "y": 3, "z": 4}, "c": 5}
test("config: deep merge", test_config_merge)

def test_config_load_json_malformed():
    from krim.config import _load_json
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("{invalid json")
        f.flush()
        path = f.name
    try:
        from pathlib import Path
        result = _load_json(Path(path))
        assert result == {}  # should return empty dict on malformed JSON
    finally:
        os.unlink(path)
test("config: malformed JSON returns empty", test_config_load_json_malformed)

def test_config_load_json_missing():
    from krim.config import _load_json
    from pathlib import Path
    result = _load_json(Path("/nonexistent/config.json"))
    assert result == {}
test("config: missing file returns empty", test_config_load_json_missing)

def test_config_merge_override_list():
    from krim.config import _merge_config
    base = {"allow_commands": ["ls", "cat"]}
    override = {"allow_commands": ["ls", "grep"]}
    result = _merge_config(base, override)
    # lists are replaced, not merged
    assert result["allow_commands"] == ["ls", "grep"]
test("config: list override replaces entirely", test_config_merge_override_list)

# ============================================================
# 14. RETRY
# ============================================================
print("\n=== RETRY ===")

def test_retry_success():
    from krim.retry import with_retry
    call_count = 0
    def fn():
        nonlocal call_count
        call_count += 1
        return "ok"
    wrapped = with_retry(fn, max_retries=3, base_delay=0.01)
    result = wrapped()
    assert result == "ok"
    assert call_count == 1
test("retry: success on first attempt", test_retry_success)

def test_retry_non_retriable():
    from krim.retry import with_retry
    def fn():
        raise ValueError("not retriable")
    wrapped = with_retry(fn, max_retries=3, base_delay=0.01)
    try:
        wrapped()
        assert False, "should have raised"
    except ValueError:
        pass  # expected
test("retry: non-retriable raises immediately", test_retry_non_retriable)

def test_retry_is_retriable():
    from krim.retry import is_retriable
    assert is_retriable(TimeoutError())
    assert is_retriable(ConnectionError())
    assert not is_retriable(ValueError())
    # test status code check
    class FakeError(Exception):
        status_code = 429
    assert is_retriable(FakeError())
    class FakeError2(Exception):
        status_code = 404
    assert not is_retriable(FakeError2())
test("retry: is_retriable checks", test_retry_is_retriable)

# ============================================================
# 15. SKILLS
# ============================================================
print("\n=== SKILLS ===")

def test_skills_discovery():
    from krim.skills import discover_skills, Skill
    with tempfile.TemporaryDirectory() as td:
        from pathlib import Path
        skills_dir = Path(td) / "skills"
        deploy_dir = skills_dir / "deploy"
        deploy_dir.mkdir(parents=True)
        (deploy_dir / "SKILL.md").write_text("Deploy skill instructions")

        skills = discover_skills(global_dir=Path(td))
        assert "deploy" in skills
        assert skills["deploy"].prompt == "Deploy skill instructions"
test("skills: discovery from directory", test_skills_discovery)

def test_skills_inject():
    from krim.skills import inject_skill, Skill
    skill = Skill(name="test", prompt="do testing", path="/tmp")
    result = inject_skill("base prompt", skill)
    assert "base prompt" in result
    assert "# Skill: test" in result
    assert "do testing" in result
test("skills: injection into prompt", test_skills_inject)

def test_skills_project_overrides_global():
    from krim.skills import discover_skills
    with tempfile.TemporaryDirectory() as gd, tempfile.TemporaryDirectory() as pd:
        from pathlib import Path
        # global skill
        gskill = Path(gd) / "skills" / "deploy"
        gskill.mkdir(parents=True)
        (gskill / "SKILL.md").write_text("global deploy")
        # project skill overrides
        pskill = Path(pd) / "skills" / "deploy"
        pskill.mkdir(parents=True)
        (pskill / "SKILL.md").write_text("project deploy")

        skills = discover_skills(global_dir=Path(gd), project_dir=Path(pd))
        assert skills["deploy"].prompt == "project deploy"
test("skills: project overrides global", test_skills_project_overrides_global)

# ============================================================
# 16. MCP TOOL SCHEMA
# ============================================================
print("\n=== MCP ===")

def test_mcp_tool_schema():
    """McpTool should include required field from MCP server."""
    from krim.mcp import McpTool
    # create a mock server (won't actually connect)
    tool = McpTool.__new__(McpTool)
    tool.name = "web_search"
    tool.description = "Search the web"
    tool.parameters = {"query": {"type": "string"}, "limit": {"type": "integer"}}
    tool._required = ["query"]
    tool._server = None

    schema = tool.schema()
    assert schema["name"] == "web_search"
    assert schema["input_schema"]["required"] == ["query"]
    assert "query" in schema["input_schema"]["properties"]
    assert "limit" in schema["input_schema"]["properties"]
test("mcp: tool schema includes required", test_mcp_tool_schema)

def test_mcp_config_load():
    from krim.mcp import load_mcp_config
    with tempfile.TemporaryDirectory() as td:
        from pathlib import Path
        mcp_json = Path(td) / "mcp.json"
        mcp_json.write_text(json.dumps({
            "mcpServers": {
                "test-server": {
                    "command": ["node", "server.js"],
                    "env": {"API_KEY": "xxx"}
                }
            }
        }))
        configs = load_mcp_config(global_dir=Path(td))
        assert len(configs) == 1
        assert configs[0].name == "test-server"
        assert configs[0].command == ["node", "server.js"]
        assert configs[0].env == {"API_KEY": "xxx"}
test("mcp: config loading", test_mcp_config_load)

# ============================================================
# 17. CONTEXT
# ============================================================
print("\n=== CONTEXT ===")

def test_context_cwd():
    from krim.context import get_cwd
    assert get_cwd() == os.getcwd()
test("context: get_cwd", test_context_cwd)

def test_context_build():
    from krim.context import build_context
    ctx = build_context()
    assert "cwd:" in ctx
test("context: build includes cwd", test_context_build)

# ============================================================
# 18. PROMPT
# ============================================================
print("\n=== PROMPT ===")

def test_prompt_core():
    from krim.prompt import CORE
    assert "krim" in CORE
    assert "bash" in CORE
    assert "read" in CORE
    assert "write" in CORE
    assert "edit" in CORE
    assert "fuzzy" in CORE.lower()
    assert "persist" in CORE.lower()
test("prompt: core includes all tools and hints", test_prompt_core)

def test_prompt_build():
    from krim.prompt import build_system_prompt
    from krim.config import KrimConfig
    config = KrimConfig()
    config.krim_md = "Project instructions here"
    config.rules = ["Rule 1", "Rule 2"]
    prompt = build_system_prompt(config, extra_tools=["web_search"])
    assert "krim" in prompt
    assert "web_search" in prompt
    assert "Project instructions here" in prompt
    assert "Rule 1" in prompt
    assert "Rule 2" in prompt
test("prompt: build with all sections", test_prompt_build)

# ============================================================
# 19. GIT
# ============================================================
print("\n=== GIT ===")

def test_git_is_git_repo():
    from krim.git import is_git_repo
    # we're in a git repo (batteryhob.github.io)
    result = is_git_repo()
    assert isinstance(result, bool)
test("git: is_git_repo returns bool", test_git_is_git_repo)

def test_git_dirty_files():
    from krim.git import get_dirty_files
    result = get_dirty_files()
    assert isinstance(result, list)
test("git: get_dirty_files returns list", test_git_dirty_files)

# ============================================================
# 20. CROSS-MODULE INTERACTION
# ============================================================
print("\n=== CROSS-MODULE INTERACTION ===")

def test_agent_tool_execution():
    """Agent._execute_tool should correctly dispatch to tools."""
    from krim.agent import Agent
    from krim.tools import create_tools
    from krim.models.base import Model, ModelResponse

    class MockModel(Model):
        def chat(self, messages, tools, stream_callback=None):
            return ModelResponse(text="ok", tool_calls=[], stop=True)

    tools = create_tools()
    agent = Agent(MockModel(), "claude", "sys", tools, max_turns=1)

    # execute read on nonexistent file
    result = agent._execute_tool("read", {"path": "/nonexistent/file.py"})
    assert "not found" in result

    # execute unknown tool
    result = agent._execute_tool("unknown_tool", {})
    assert "unknown tool" in result
test("cross: agent dispatches to real tools", test_agent_tool_execution)

def test_agent_mcp_tool_dispatch():
    """Agent should check MCP tools first."""
    from krim.agent import Agent
    from krim.models.base import Model, ModelResponse
    from krim.tools.base import Tool

    class MockModel(Model):
        def chat(self, messages, tools, stream_callback=None):
            return ModelResponse(text="ok", tool_calls=[], stop=True)

    class FakeMcpTool(Tool):
        name = "web_search"
        description = "search"
        parameters = {}
        def run(self, **kwargs):
            return f"searched for: {kwargs.get('query', '')}"

    agent = Agent(MockModel(), "claude", "sys", [], mcp_tools=[FakeMcpTool()], max_turns=1)
    result = agent._execute_tool("web_search", {"query": "test"})
    assert "searched for: test" in result
test("cross: agent dispatches to MCP tools", test_agent_mcp_tool_dispatch)

def test_agent_tool_error_boundary():
    """Tool exceptions should be caught and returned as error strings."""
    from krim.agent import Agent
    from krim.models.base import Model, ModelResponse
    from krim.tools.base import Tool

    class MockModel(Model):
        def chat(self, messages, tools, stream_callback=None):
            return ModelResponse(text="ok", tool_calls=[], stop=True)

    class BrokenTool(Tool):
        name = "broken"
        description = "broken tool"
        parameters = {}
        def run(self, **kwargs):
            raise RuntimeError("tool exploded")

    agent = Agent(MockModel(), "claude", "sys", [BrokenTool()], max_turns=1)
    result = agent._execute_tool("broken", {})
    assert "error" in result
    assert "tool exploded" in result
test("cross: tool error boundary", test_agent_tool_error_boundary)

def test_run_stats_tracking():
    from krim.agent import RunStats
    stats = RunStats()
    stats.record_tool_call("bash")
    stats.record_tool_call("bash")
    stats.record_tool_call("read")
    assert stats.tool_calls == 3
    assert stats.tool_call_names == {"bash": 2, "read": 1}
test("cross: RunStats tracking", test_run_stats_tracking)

def test_agent_full_loop():
    """Test a complete agent loop with a mock model that uses tools."""
    from krim.agent import Agent
    from krim.tools import create_tools
    from krim.models.base import Model, ModelResponse, ToolCall

    call_num = 0
    class SmartModel(Model):
        def chat(self, messages, tools, stream_callback=None):
            nonlocal call_num
            call_num += 1
            if call_num == 1:
                # first call: use a tool
                return ModelResponse(
                    text="Let me check",
                    tool_calls=[ToolCall(id="t1", name="bash", args={"command": "echo hello"})],
                    stop=False,
                )
            else:
                # second call: respond with text
                return ModelResponse(text="Done!", tool_calls=[], stop=True)

    tools = create_tools()
    # configure bash to not ask
    from krim.tools.bash import BashTool
    for t in tools:
        if isinstance(t, BashTool):
            t._ask_by_default = False

    agent = Agent(SmartModel(), "claude", "system prompt", tools, max_turns=5)
    stats = agent.run("test task")

    assert stats.turns == 2
    assert stats.tool_calls == 1
    assert stats.tool_call_names == {"bash": 1}
    # messages: system, user, assistant(tool_use), user(tool_result), assistant(text)
    assert len(agent.messages) >= 4
test("cross: full agent loop with tool use", test_agent_full_loop)

# ============================================================
# 21. EDGE CASES IN COMPACTION + AGENT INTERACTION
# ============================================================
print("\n=== COMPACTION + AGENT INTERACTION ===")

def test_compact_preserves_system():
    """Compaction must NEVER drop the system message."""
    from krim.compaction import compact
    msgs = [{"role": "system", "content": "IMPORTANT SYSTEM PROMPT " * 100}]
    # add many messages to trigger compaction
    for i in range(50):
        msgs.append({"role": "user", "content": f"q{i} " * 1000})
        msgs.append({"role": "assistant", "content": f"a{i} " * 1000})

    result = compact(msgs, max_tokens=500)
    assert result[0]["role"] == "system"
    assert "IMPORTANT SYSTEM PROMPT" in result[0]["content"]
test("compaction+agent: system message preserved", test_compact_preserves_system)

def test_compact_after_claude_tool_sequence():
    """Verify compaction handles a realistic Claude tool call sequence."""
    from krim.compaction import compact
    msgs = [
        {"role": "system", "content": "sys"},
    ]
    # add 20 tool use cycles
    for i in range(20):
        msgs.append({"role": "assistant", "content": [
            {"type": "text", "text": f"step {i}"},
            {"type": "tool_use", "id": f"t{i}", "name": "bash", "input": {"command": f"cmd{i}"}},
        ]})
        msgs.append({"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": f"t{i}", "content": f"output{i} " * 500},
        ]})
    msgs.append({"role": "user", "content": "final question"})
    msgs.append({"role": "assistant", "content": "final answer"})

    result = compact(msgs, max_tokens=1000)
    # system should be preserved
    assert result[0]["role"] == "system"
    # no orphaned tool_results (every tool_result should have a preceding tool_use)
    for i in range(1, len(result)):
        msg = result[i]
        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
            has_tool_result = any(
                isinstance(b, dict) and b.get("type") == "tool_result"
                for b in msg["content"]
            )
            if has_tool_result:
                # check that preceding message has tool_use
                prev = result[i-1]
                if prev.get("role") == "assistant" and isinstance(prev.get("content"), list):
                    has_tool_use = any(
                        isinstance(b, dict) and b.get("type") == "tool_use"
                        for b in prev["content"]
                    )
                    assert has_tool_use, f"orphaned tool_result at index {i}"
test("compaction+agent: no orphaned tool_results after compaction", test_compact_after_claude_tool_sequence)

# ============================================================
# 22. MODEL FACTORY
# ============================================================
print("\n=== MODEL FACTORY ===")

def test_model_factory_unknown():
    from krim.models import create_model
    try:
        create_model("unknown_provider")
        assert False, "should have raised"
    except ValueError as e:
        assert "unknown provider" in str(e)
test("model factory: unknown provider raises", test_model_factory_unknown)

def test_model_factory_defaults():
    from krim.models import DEFAULT_MODELS
    assert "claude" in DEFAULT_MODELS
    assert "openai" in DEFAULT_MODELS
test("model factory: default models exist", test_model_factory_defaults)

# ============================================================
# 23. EDIT TOOL - FUZZY FIND EDGE CASES
# ============================================================
print("\n=== EDIT FUZZY FIND ===")

def test_fuzzy_find_below_threshold():
    from krim.tools.edit import _fuzzy_find
    content = "def completely_different():\n    return 42\n"
    old = "class TotallyUnrelated:\n    pass\n"
    result = _fuzzy_find(content, old)
    assert result is None
test("fuzzy: below threshold returns None", test_fuzzy_find_below_threshold)

def test_fuzzy_find_single_line():
    from krim.tools.edit import _fuzzy_find
    content = "def foo():\n    return 1\n"
    old = "def fooo():"
    result = _fuzzy_find(content, old)
    assert result is not None  # should find approximate match
test("fuzzy: single line approximate match", test_fuzzy_find_single_line)

def test_normalize_whitespace():
    from krim.tools.edit import _normalize_whitespace
    assert _normalize_whitespace("  hello   world  ") == "hello world"
    assert _normalize_whitespace("\t\n  a  \n\t  b  ") == "a b"
    assert _normalize_whitespace("") == ""
test("fuzzy: normalize whitespace", test_normalize_whitespace)

# ============================================================
# SUMMARY
# ============================================================
print(f"\n{'='*60}")
print(f"RESULTS: {PASS} PASS, {FAIL} FAIL (total: {PASS + FAIL})")
print(f"{'='*60}")

if ERRORS:
    print("\nFAILURES:")
    for name, err in ERRORS:
        print(f"  {name}")
        print(f"    {err}")

sys.exit(1 if FAIL > 0 else 0)

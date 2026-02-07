"""Token tracking and conversation compaction.

Strategy:
- Estimate tokens from character count (rough: 1 token ~ 4 chars)
- When conversation approaches limit, compact by:
  1. Replacing old tool results with summaries
  2. Summarizing old conversation turns
  3. Preserving: system prompt, KRIM.md, recent messages
"""

from __future__ import annotations

import json


# rough estimate: 1 token ~ 4 chars for English, ~2 chars for CJK
def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return len(text) // 3  # conservative estimate


def estimate_message_tokens(messages: list[dict]) -> int:
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    total += estimate_tokens(json.dumps(block))
                else:
                    total += estimate_tokens(str(block))
        # tool_calls in openai format
        if "tool_calls" in msg:
            total += estimate_tokens(json.dumps(msg["tool_calls"]))
    return total


def needs_compaction(messages: list[dict], max_tokens: int = 120_000, threshold: float = 0.75) -> bool:
    used = estimate_message_tokens(messages)
    return used > max_tokens * threshold


def compact(messages: list[dict], max_tokens: int = 120_000) -> list[dict]:
    """Compact conversation to fit within token budget.

    Preserves: system message (index 0), last N user/assistant exchanges.
    Replaces: old tool results with short summaries.
    """
    if len(messages) <= 4:
        return messages

    system = messages[0] if messages[0].get("role") == "system" else None
    rest = messages[1:] if system else messages[:]

    # phase 1: truncate old tool results
    compacted = []
    for i, msg in enumerate(rest):
        # keep last 6 messages intact
        if i >= len(rest) - 6:
            compacted.append(msg)
            continue

        content = msg.get("content", "")
        role = msg.get("role", "")

        # truncate tool results (claude format: list of tool_result blocks)
        if role == "user" and isinstance(content, list):
            new_content = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    result_text = block.get("content", "")
                    if isinstance(result_text, str) and len(result_text) > 200:
                        # deep copy the block to avoid mutating the original
                        block = dict(block)
                        block["content"] = result_text[:100] + "... [compacted]"
                new_content.append(block)
            compacted.append(dict(msg, content=new_content))

        # truncate tool results (openai format)
        elif role == "tool":
            if isinstance(content, str) and len(content) > 200:
                compacted.append({**msg, "content": content[:100] + "... [compacted]"})
            else:
                compacted.append(msg)

        else:
            compacted.append(msg)

    # phase 2: if still too large, drop oldest non-system messages
    result = ([system] if system else []) + compacted
    while len(result) > 4 and estimate_message_tokens(result) > max_tokens * 0.6:
        # remove the oldest non-system message
        result.pop(1)

    return result

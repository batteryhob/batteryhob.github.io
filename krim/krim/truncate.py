"""Output truncation to protect the context window."""

from __future__ import annotations


def truncate(text: str, max_chars: int = 30_000) -> str:
    """Truncate output that would bloat the context window.

    Strategy: keep first and last portions so the model sees both
    the beginning (headers, first errors) and end (final status, exit code).
    """
    if len(text) <= max_chars:
        return text

    # 60% head, 40% tail
    head_size = int(max_chars * 0.6)
    tail_size = max_chars - head_size
    omitted = len(text) - max_chars

    return (
        text[:head_size]
        + f"\n\n... [{omitted:,} characters truncated] ...\n\n"
        + text[-tail_size:]
    )

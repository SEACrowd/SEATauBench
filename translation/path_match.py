from __future__ import annotations


def path_matches(path: tuple[str, ...], pattern: tuple[str, ...]) -> bool:
    """Match a tuple path with '*' wildcard support."""
    if len(path) != len(pattern):
        return False
    for actual, expected in zip(path, pattern):
        if expected == "*":
            continue
        if actual != expected:
            return False
    return True


def matches_any(path: tuple[str, ...], patterns: tuple[tuple[str, ...], ...]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


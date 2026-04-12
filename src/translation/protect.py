from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from translation.config import (
    CONTEXTUAL_BUCKET_PATH_HINTS,
    CONTEXTUAL_BUCKET_TEXT_CUES,
    DEFAULT_PROTECTED_PATTERNS,
    get_domain_contextual_protected_terms,
)
from translation.models import Segment


@dataclass(frozen=True)
class MaskedText:
    text: str
    placeholders: list[str]


@lru_cache(maxsize=16)
def _build_pattern_cached(protected_terms: frozenset[str]) -> re.Pattern[str]:
    """Build compiled regex pattern for protected terms (cached)."""

    def term_pattern(term: str) -> str:
        escaped = re.escape(term)
        if re.fullmatch(r"[A-Za-z0-9_]+", term):
            return rf"\b{escaped}\b"
        return escaped

    patterns: list[str] = list(DEFAULT_PROTECTED_PATTERNS)
    sorted_terms: list[str] = sorted(
        protected_terms, key=lambda t: len(t), reverse=True
    )
    for term in sorted_terms:
        if not term or term.isspace():
            continue
        patterns.append(term_pattern(term))
    union = "|".join(f"(?:{pat})" for pat in patterns)
    return re.compile(union)


def _build_pattern(protected_terms: set[str]) -> re.Pattern[str]:
    """Build compiled regex pattern for protected terms."""
    return _build_pattern_cached(frozenset(protected_terms))


def _term_occurrence_pattern(term: str) -> re.Pattern[str]:
    escaped = re.escape(term)
    if re.fullmatch(r"[A-Za-z0-9_ ]+", term):
        return re.compile(rf"(?<![A-Za-z0-9_]){escaped}(?![A-Za-z0-9_])")
    return re.compile(escaped)


def _line_slice(text: str, start: int, end: int) -> tuple[str, int]:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end], line_start


def _term_is_formatted_literal(term: str, line: str) -> bool:
    escaped = re.escape(term)
    patterns = (
        rf"`{escaped}`",
        rf"'{escaped}'",
        rf'"{escaped}"',
        rf"\*\*{escaped}\*\*",
    )
    return any(re.search(pattern, line) for pattern in patterns)


def _path_context_buckets(segment: Segment) -> set[str]:
    address = segment.address
    if not isinstance(address, tuple):
        return set()

    address_keys = {part for part in address if not part.isdigit()}
    buckets: set[str] = set()
    for bucket, hints in CONTEXTUAL_BUCKET_PATH_HINTS.items():
        if address_keys & hints:
            buckets.add(bucket)
    return buckets


def _match_has_textual_context(
    text: str,
    start: int,
    end: int,
    bucket: str,
    term: str,
) -> bool:
    line, _ = _line_slice(text, start, end)
    if _term_is_formatted_literal(term, line):
        return True
    for pattern in CONTEXTUAL_BUCKET_TEXT_CUES.get(bucket, ()):
        if re.search(pattern, line, flags=re.IGNORECASE):
            return True
    return False


def _contextual_matches_for_segment(segment: Segment) -> list[tuple[int, int, str]]:
    bucket_terms = get_domain_contextual_protected_terms(segment.domain)
    if not bucket_terms:
        return []

    path_buckets = _path_context_buckets(segment)
    matches: list[tuple[int, int, str]] = []

    for bucket, terms in bucket_terms.items():
        for term in sorted(terms, key=len, reverse=True):
            pattern = _term_occurrence_pattern(term)
            for match in pattern.finditer(segment.text):
                if bucket in path_buckets or _match_has_textual_context(
                    segment.text,
                    match.start(),
                    match.end(),
                    bucket,
                    term,
                ):
                    matches.append((match.start(), match.end(), match.group(0)))

    matches.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    selected: list[tuple[int, int, str]] = []
    last_end = -1
    for start, end, token in matches:
        if start < last_end:
            continue
        selected.append((start, end, token))
        last_end = end
    return selected


def _apply_manual_placeholders(
    text: str,
    matches: list[tuple[int, int, str]],
) -> MaskedText:
    if not matches:
        return MaskedText(text=text, placeholders=[])

    parts: list[str] = []
    placeholders: list[str] = []
    cursor = 0
    for start, end, token in matches:
        parts.append(text[cursor:start])
        placeholder = f"__PH_{len(placeholders)}__"
        placeholders.append(token)
        parts.append(placeholder)
        cursor = end
    parts.append(text[cursor:])
    return MaskedText(text="".join(parts), placeholders=placeholders)


def mask_protected_tokens(
    text: str,
    protected_terms: set[str],
    initial_placeholders: list[str] | None = None,
) -> MaskedText:
    """Replace protected tokens with placeholders before translation."""
    if not text:
        return MaskedText(text=text, placeholders=[])

    pattern = _build_pattern(protected_terms)
    placeholders: list[str] = list(initial_placeholders or [])

    def replacer(match: re.Match[str]) -> str:
        token = match.group(0)
        placeholder = f"__PH_{len(placeholders)}__"
        placeholders.append(token)
        return placeholder

    masked = pattern.sub(replacer, text)
    return MaskedText(text=masked, placeholders=placeholders)


def mask_segment_protected_tokens(
    segment: Segment,
    protected_terms: set[str],
) -> MaskedText:
    """Mask unconditional terms plus context-sensitive runtime literals."""
    contextual_terms = {
        term
        for terms in get_domain_contextual_protected_terms(segment.domain).values()
        for term in terms
    }
    contextual_matches = _contextual_matches_for_segment(segment)
    manually_masked = _apply_manual_placeholders(segment.text, contextual_matches)
    return mask_protected_tokens(
        manually_masked.text,
        protected_terms=protected_terms - contextual_terms,
        initial_placeholders=manually_masked.placeholders,
    )


def unmask_protected_tokens(translated_text: str, masked: MaskedText) -> str:
    """Restore placeholders and ensure they were not dropped/changed."""
    restored = translated_text
    for idx, original in enumerate(masked.placeholders):
        placeholder = f"__PH_{idx}__"
        if placeholder not in restored:
            # Some models occasionally emit the exact protected token instead of the
            # placeholder. Accept that passthrough as long as the token is preserved.
            if original in restored:
                continue
            raise ValueError(
                f"Missing placeholder {placeholder} in translated text: {translated_text!r}"
            )
        restored = restored.replace(placeholder, original)

    if re.search(r"__PH_\d+__", restored):
        raise ValueError(f"Unresolved placeholders in translation: {restored!r}")
    return restored

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from translation.config import DEFAULT_PROTECTED_PATTERNS


@dataclass(frozen=True)
class MaskedText:
    text: str
    placeholders: list[str]


@lru_cache(maxsize=16)
def _build_pattern_cached(protected_terms: frozenset[str]) -> re.Pattern[str]:
    """Build compiled regex pattern for protected terms (cached)."""
    patterns: list[str] = list(DEFAULT_PROTECTED_PATTERNS)
    sorted_terms: list[str] = sorted(
        protected_terms, key=lambda t: len(t), reverse=True
    )
    for term in sorted_terms:
        if not term or term.isspace():
            continue
        patterns.append(re.escape(term))
    union = "|".join(f"(?:{pat})" for pat in patterns)
    return re.compile(union)


def _build_pattern(protected_terms: set[str]) -> re.Pattern[str]:
    """Build compiled regex pattern for protected terms."""
    return _build_pattern_cached(frozenset(protected_terms))


def mask_protected_tokens(text: str, protected_terms: set[str]) -> MaskedText:
    """Replace protected tokens with placeholders before translation."""
    if not text:
        return MaskedText(text=text, placeholders=[])

    pattern = _build_pattern(protected_terms)
    placeholders: list[str] = []

    def replacer(match: re.Match[str]) -> str:
        token = match.group(0)
        placeholder = f"__PH_{len(placeholders)}__"
        placeholders.append(token)
        return placeholder

    masked = pattern.sub(replacer, text)
    return MaskedText(text=masked, placeholders=placeholders)


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

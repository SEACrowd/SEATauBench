"""Markdown split/rejoin by ATX heading.

Used by both the exporter (split source markdown into reviewable sections)
and the importer (rejoin reviewed sections back into a single markdown file).

Section IDs follow the format `NNN_<slug>_K`:
  - NNN: 1-based index in document order (zero-padded to 3 digits)
  - slug: lowercased heading text with non-alphanumerics collapsed to `-`
          (the literal "preamble" for content before the first heading)
  - K: dedup counter when the same slug appears more than once

Keeping split and rejoin in one module guarantees the export ↔ import
addresses agree.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from seatau.annotation.addresses import is_blank

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class Section:
    """One markdown heading-block plus its body."""

    section_id: str
    heading_line: str  # the literal heading line, or "Preamble" for pre-heading content
    text: str  # heading + body (joined with `\n`)


def slug(text: str) -> str:
    """Slugify a heading line for stable section_id generation."""
    s = _SLUG_NON_ALNUM.sub("-", text.strip().lower())
    return s.strip("-") or "section"


def split(markdown_text: str) -> list[Section]:
    """Split markdown by ATX headings into ordered sections.

    Content before the first heading is captured as `Preamble`.
    """
    lines = markdown_text.splitlines()
    raw: list[tuple[str, list[str]]] = []
    current_heading, current_lines = "Preamble", []
    for line in lines:
        if _HEADING_RE.match(line):
            if current_lines:
                raw.append((current_heading, current_lines))
            current_heading, current_lines = line.strip(), [line]
        else:
            current_lines.append(line)
    if current_lines:
        raw.append((current_heading, current_lines))

    seen: dict[str, int] = {}
    sections: list[Section] = []
    for idx, (heading, body_lines) in enumerate(raw, start=1):
        h_text = "preamble" if heading == "Preamble" else heading
        sl = slug(h_text)
        seen[sl] = seen.get(sl, 0) + 1
        sid = f"{idx:03d}_{sl}_{seen[sl]}"
        sections.append(
            Section(
                section_id=sid,
                heading_line=heading,
                text="\n".join(body_lines).strip(),
            )
        )
    return sections


def rejoin(english_text: str, section_id_to_final: dict[str, str]) -> str:
    """Rebuild a markdown file from the English source plus per-section overrides.

    For each section in the source document order, look up the reviewed final
    value by section_id. If found and non-blank, use it; otherwise fall back
    to the English text.
    """
    sections = split(english_text)
    out_parts: list[str] = []
    for section in sections:
        final = section_id_to_final.get(section.section_id)
        if final is not None and not is_blank(final):
            out_parts.append(str(final))
        else:
            out_parts.append(section.text)
    return "\n".join(out_parts)

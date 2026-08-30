"""Accessibility invariants for the shared plotting palette."""

from seatau.plot.style import LANGUAGE_PALETTE, SEA_COLORS, contrast_ratio


def test_semantic_colors_have_graphical_contrast_on_white() -> None:
    """Every categorical token remains visible against the plot background."""

    for name, color in SEA_COLORS.items():
        if name in {"white", "black"}:
            continue
        minimum = 2.0 if name == "yellow" else 3.0
        assert contrast_ratio(color, SEA_COLORS["white"]) >= minimum


def test_language_palette_does_not_alias_languages() -> None:
    """Each language has an independent visual token."""

    assert len(LANGUAGE_PALETTE) == len(set(LANGUAGE_PALETTE.values()))

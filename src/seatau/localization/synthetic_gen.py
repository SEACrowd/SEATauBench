"""Generate realistic fake names, addresses, and nearby value sets.

The notebook prototype in ``faker-name.ipynb`` used Faker to sample locale-
appropriate names and addresses. This module turns that prototype into a
reusable API with deterministic output per language.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from faker import Faker

from seatau.paths import LANGUAGES_PATH

LANGUAGE_FAKER_LOCALES: dict[str, str] = {
    "id": "id_ID",
    "th": "th_TH",
    "vi": "vi_VN",
    "zh": "zh_CN",
    "tl": "en_PH",
}


def _load_language_codes() -> set[str]:
    payload = json.loads(LANGUAGES_PATH.read_text(encoding="utf-8"))
    return {code for code in payload if code != "en"}


SUPPORTED_LOCALIZED_LANGUAGES = frozenset(_load_language_codes())


def _stable_seed(lang: str, seed: int | None) -> int:
    if seed is not None:
        return seed
    digest = hashlib.sha256(f"seatau-localization:{lang}".encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big", signed=False)


def _normalize_text(value: Any) -> str:
    text = str(value).replace("\n", ", ")
    text = re.sub(r"\s+", " ", text).strip(" ,")
    return text


def _unique_values(factory: Callable[[], Any], count: int) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    attempts = 0
    max_attempts = max(100, count * 40)
    while len(values) < count and attempts < max_attempts:
        candidate = _normalize_text(factory())
        attempts += 1
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        values.append(candidate)
    if not values:
        raise RuntimeError("unable to generate any synthetic values")
    return values


_HONORIFIC_PREFIXES = {
    "bà",
    "bác",
    "cô",
    "dr.",
    "drs.",
    "h.",
    "hj.",
    "mr.",
    "mrs.",
    "ms.",
    "ông",
    "quý",
}
_NAME_SUFFIX_HINTS = {"jr.", "sr."}


def _clean_person_name(value: Any) -> str:
    text = _normalize_text(value)
    if "," in text:
        text = text.split(",", 1)[0].strip()
    tokens = text.split()
    while tokens:
        head = tokens[0].lower().rstrip(".")
        if head in _HONORIFIC_PREFIXES:
            tokens.pop(0)
            continue
        if len(tokens) >= 2 and " ".join(tokens[:2]).lower() in {"quý ông", "quý cô"}:
            tokens = tokens[2:]
            continue
        break
    while tokens and tokens[-1].lower().rstrip(".") in _NAME_SUFFIX_HINTS:
        tokens.pop()
    return " ".join(tokens) if tokens else text


def _secondary_address(faker: Faker) -> str:
    provider = getattr(faker, "secondary_address", None)
    if callable(provider):
        try:
            value = provider()
            if value:
                return _normalize_text(value)
        except AttributeError:
            pass
    return _normalize_text(faker.bothify("Apt. ##"))


def _provider_or_fallback(faker: Faker, attr: str, fallback: Callable[[], Any]) -> str:
    provider = getattr(faker, attr, None)
    if callable(provider):
        try:
            value = provider()
            if value:
                return _normalize_text(value)
        except AttributeError:
            pass
    return _normalize_text(fallback())


@dataclass(frozen=True)
class SyntheticValuePools:
    """Locale-specific synthetic values ready to be reused in scripts."""

    language: str
    faker_locale: str
    seed: int
    full_names: list[str]
    first_names: list[str]
    last_names: list[str]
    full_addresses: list[str]
    street_addresses: list[str]
    secondary_addresses: list[str]
    cities: list[str]
    states: list[str]
    countries: list[str]
    postcodes: list[str]
    emails: list[str]
    phone_numbers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _faker_for_language(lang: str, seed: int | None) -> Faker:
    if lang not in LANGUAGE_FAKER_LOCALES:
        raise ValueError(f"unsupported localized language: {lang!r}")
    faker = Faker(LANGUAGE_FAKER_LOCALES[lang])
    faker.seed_instance(_stable_seed(lang, seed))
    return faker


def generate_value_pools(
    lang: str,
    *,
    count: int = 32,
    seed: int | None = None,
) -> SyntheticValuePools:
    """Generate a reusable synthetic value pool for a localized language."""

    faker = _faker_for_language(lang, seed)
    seed_value = _stable_seed(lang, seed)
    value_count = max(8, count)

    name_samples = _unique_values(
        lambda: _clean_person_name(faker.name()), value_count * 4
    )
    first_names: list[str] = []
    last_names: list[str] = []
    seen_first: set[str] = set()
    seen_last: set[str] = set()
    for sample in name_samples:
        parts = sample.split()
        if not parts:
            continue
        first_name = parts[0]
        last_name = parts[-1]
        if first_name not in seen_first:
            seen_first.add(first_name)
            first_names.append(first_name)
        if last_name not in seen_last:
            seen_last.add(last_name)
            last_names.append(last_name)

    return SyntheticValuePools(
        language=lang,
        faker_locale=LANGUAGE_FAKER_LOCALES[lang],
        seed=seed_value,
        full_names=name_samples[:value_count],
        first_names=first_names,
        last_names=last_names,
        full_addresses=_unique_values(
            lambda: _normalize_text(faker.address()), value_count
        ),
        street_addresses=_unique_values(
            lambda: _provider_or_fallback(faker, "street_address", faker.address),
            value_count,
        ),
        secondary_addresses=_unique_values(
            lambda: _secondary_address(faker), value_count
        ),
        cities=_unique_values(
            lambda: _provider_or_fallback(faker, "city", faker.word), value_count
        ),
        states=_unique_values(
            lambda: _provider_or_fallback(faker, "state", faker.city), value_count
        ),
        countries=_unique_values(
            lambda: _provider_or_fallback(faker, "country", faker.city), value_count
        ),
        postcodes=_unique_values(
            lambda: _provider_or_fallback(
                faker, "postcode", lambda: faker.bothify("#####")
            ),
            value_count,
        ),
        emails=_unique_values(
            lambda: _provider_or_fallback(
                faker, "email", lambda: f"{faker.user_name()}@example.com"
            ),
            value_count,
        ),
        phone_numbers=_unique_values(
            lambda: _provider_or_fallback(
                faker, "phone_number", lambda: faker.bothify("###-###-####")
            ),
            value_count,
        ),
    )


def save_value_pools(pools: SyntheticValuePools, path: Path) -> Path:
    """Write a synthetic value pool to JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(pools.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def load_value_pools(path: Path) -> SyntheticValuePools:
    """Load a synthetic value pool from JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    return SyntheticValuePools(**payload)

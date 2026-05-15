from __future__ import annotations

from seatau.localization.synthetic import generate_value_pools


def test_generate_value_pools_is_deterministic() -> None:
    pools_a = generate_value_pools("vi", count=8, seed=123)
    pools_b = generate_value_pools("vi", count=8, seed=123)

    assert pools_a.faker_locale == "vi_VN"
    assert pools_a.full_names[:3] == pools_b.full_names[:3]
    assert pools_a.full_addresses[:3] == pools_b.full_addresses[:3]
    assert pools_a.phone_numbers[:3] == pools_b.phone_numbers[:3]

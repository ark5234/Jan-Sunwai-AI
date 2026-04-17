import pytest

from app.category_utils import canonicalize_label


@pytest.mark.parametrize(
    "raw_label, expected",
    [
        ("sanitation", "Health Department"),
        ("sanitation issue", "Health Department"),
        ("it department", "IT Department"),
        ("IT team issue", "IT Department"),
        ("traffic", "Enforcement"),
        ("municipal - street lighting", "Electrical Department"),
        ("police - traffic", "Enforcement"),
        ("fire hazard near wire", "Fire Department"),
        ("random unknown label", "Uncategorized"),
    ],
)
def test_canonicalize_label_common_routes(raw_label: str, expected: str) -> None:
    assert canonicalize_label(raw_label) == expected


def test_canonicalize_label_avoids_it_pronoun_false_positive() -> None:
    # The phrase contains "it" as a pronoun; it should not route to IT Department.
    assert canonicalize_label("there is garbage and it smells") == "Uncategorized"

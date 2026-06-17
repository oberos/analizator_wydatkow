from collections.abc import Mapping

FALLBACK_CHART_PALETTE: tuple[str, ...] = (
    "#0d6efd",
    "#20c997",
    "#fd7e14",
    "#6610f2",
    "#198754",
    "#dc3545",
    "#0dcaf0",
    "#adb5bd",
)

DEFAULT_CATEGORY_COLOR = "#6c757d"


def color_for_category_name(
    category_name: str,
    predefined_colors: Mapping[str, str] | None = None,
) -> str:
    if predefined_colors and category_name in predefined_colors:
        return predefined_colors[category_name]

    hash_value = sum(ord(char) for char in category_name)
    return FALLBACK_CHART_PALETTE[hash_value % len(FALLBACK_CHART_PALETTE)]

"""
Draftail rich-text feature: Font family.

Registers:
- One ``InlineStyleFeature`` per configured custom font family.
- A ``"font-family"`` ControlFeature for the toolbar dropdown.
"""

from draftail_text_utils.conf import (
    feature_enabled,
    font_family_type_id,
    load_font_families,
)

from .base import (
    control_json_script,
    register_control_feature,
    register_inline_style_feature,
)


def register(features):
    if not feature_enabled("FONT_FAMILY"):
        return

    font_families = load_font_families()

    if not font_families:
        return

    for font in font_families:
        font_family = font["value"]
        type_ = font.get("type") or font_family_type_id(font["label"])

        register_inline_style_feature(
            features,
            type_,
            {"fontFamily": font_family},
            f'span[style="font-family: {font_family};"]',
        )

    register_control_feature(
        features,
        "font-family",
        icon="font",
        label="Font Family",
        description="Change font family",
        js=["draftail_text_utils/js/font_family.js"],
        css={"all": ("draftail_text_utils/css/font_family.css",)},
    )


def control():
    if not feature_enabled("FONT_FAMILY"):
        return

    return control_json_script(
        type_="font-family",
        icon="font",
        label="Font Family",
        description="Change font family",
    )

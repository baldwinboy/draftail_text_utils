"""
Draftail rich-text feature: Font size toolbar control.

Registers a ``"font-size"`` ControlFeature that applies/removes the
``size`` property on the unified ``TEXT_STYLE`` entity.
"""

from draftail_text_utils.conf import feature_enabled

from .base import (
    control_json_script,
    register_control_feature,
)


def register(features):
    if not feature_enabled("FONT_SIZE"):
        return

    register_control_feature(
        features,
        feature_name="font-size",
        icon="text-height",
        label="Font Size",
        description="Change font size",
        js=["draftail_text_utils/js/font_size.js"],
        css={"all": ("draftail_text_utils/css/font_size.css",)},
    )


def control():
    if not feature_enabled("FONT_SIZE"):
        return

    return control_json_script(
        type_="font-size",
        icon="text-height",
        label="Font Size",
        description="Change font size",
    )

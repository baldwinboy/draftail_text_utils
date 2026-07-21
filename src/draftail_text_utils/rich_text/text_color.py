"""
Draftail rich-text feature: Text color toolbar control.

Registers a ``"text-color"`` ControlFeature that applies/removes the
``color`` property on the unified ``TEXT_STYLE`` entity.
"""

from draftail_text_utils.conf import feature_enabled

from .base import (
    control_json_script,
    register_control_feature,
)


def register(features):
    if not feature_enabled("TEXT_COLOR"):
        return

    register_control_feature(
        features,
        feature_name="text-color",
        js=["draftail_text_utils/js/text_color.js"],
        css={"all": ("draftail_text_utils/css/text_color.css",)},
    )


def control():
    if not feature_enabled("TEXT_COLOR"):
        return

    return control_json_script(
        type_="text-color",
        icon="palette",
        label="Text Color",
        description="Change text color",
    )

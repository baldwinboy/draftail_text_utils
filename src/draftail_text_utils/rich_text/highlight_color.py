"""
Draftail rich-text feature: Highlight color toolbar control.

Registers a ``"highlight-color"`` ControlFeature that applies/removes the
``backgroundColor`` property on the unified ``TEXT_STYLE`` entity.
"""

from draftail_text_utils.conf import feature_enabled

from .base import (
    control_json_script,
    register_control_feature,
)


def register(features):
    if not feature_enabled("HIGHLIGHT_COLOR"):
        return

    register_control_feature(
        features,
        feature_name="highlight-color",
        js=["draftail_text_utils/js/highlight_color.js"],
        css={"all": ("draftail_text_utils/css/highlight_color.css",)},
    )


def control():
    if not feature_enabled("HIGHLIGHT_COLOR"):
        return

    return control_json_script(
        type_="highlight-color",
        icon="highlighter",
        label="Highlight Color",
        description="Change highlight color",
    )

"""
Draftail rich-text feature: Context-bound (dynamic) link control.

Registers an opt-in ``"dynamic-link"`` ControlFeature that lets an author
attach a context expression (e.g. ``{{ user.url }}``) to the selected text.
The expression is stored on the unified ``TEXT_STYLE`` entity; the host
project resolves it at render time.
"""

from draftail_text_utils.conf import feature_enabled

from .base import (
    control_json_script,
    register_control_feature,
)


def register(features):
    if not feature_enabled("DYNAMIC_LINK"):
        return

    register_control_feature(
        features,
        feature_name="dynamic-link",
        icon="anchor",
        label="Dynamic Link",
        description="Link to a context value, e.g. {{ user.url }}",
        js=["draftail_text_utils/js/dynamic_link.js"],
        css={"all": ("draftail_text_utils/css/dynamic_link.css",)},
    )


def control():
    if not feature_enabled("DYNAMIC_LINK"):
        return

    return control_json_script(
        type_="dynamic-link",
        icon="anchor",
        label="Dynamic Link",
        description="Link to a context value, e.g. {{ user.url }}",
    )

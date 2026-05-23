"""
Draftail rich-text feature: Highlight color.

Registers:
- A ``"highlight-color-entity"`` EntityFeature for arbitrary text colors.
- A ``"highlight-color"`` ControlFeature for the toolbar control.
"""

import cssutils

from draftjs_exporter.dom import DOM
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    InlineEntityElementHandler,
)

from draftail_text_utils.conf import feature_enabled

from .base import (
    control_json_script,
    register_control_feature,
    register_entity_feature,
)


class HighlightColorEntityHandler(InlineEntityElementHandler):
    """
    Database HTML to Draft.js ContentState.
    Converts span elements with ``style="background-color: <color>;"`` to
    ``HIGHLIGHT_COLOR`` entities.
    """

    mutability = "MUTABLE"

    def get_attribute_data(self, attrs):
        """
        Extract the color from the style attribute and return it as
        an entity.
        """
        try:
            return {
                "backgroundColor": cssutils.parseStyle(attrs["style"])[
                    "background-color"
                ]
            }
        except Exception:
            return {}


def highlight_color_entity_decorator(props):
    """
    Draft.js ContentState to database HTML.
    Converts ``HIGHLIGHT_COLOR`` entities to span elements with
    ``style="background-color: <backgroundColor>;"``.
    """
    background_color = props.get("backgroundColor", None)
    children = props.get("children", None)

    if not background_color and not children:
        return None

    attrs = {}
    if background_color:
        attrs["style"] = f"background-color: {background_color};"
    attrs["data-entity-type"] = "HIGHLIGHT_COLOR"
    return DOM.create_element("span", attrs, children)


def register(features):
    if not feature_enabled("HIGHLIGHT_COLOR"):
        return

    register_entity_feature(
        features,
        feature_name="highlight-color-entity",
        entity_type="HIGHLIGHT_COLOR",
        attributes=["backgroundColor", "style", "data-entity-type"],
        decorator_fn=highlight_color_entity_decorator,
        handler_cls=HighlightColorEntityHandler,
        js=["draftail_text_utils/js/highlight_color_entity.js"],
    )

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

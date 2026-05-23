"""
Draftail rich-text feature: Text color.

Registers:
- A ``"text-color-entity"`` EntityFeature for arbitrary text colors.
- A ``"text-color"`` ControlFeature for the toolbar control.
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


class TextColorEntityHandler(InlineEntityElementHandler):
    """
    Database HTML to Draft.js ContentState.
    Converts span elements with ``style="color: <color>;"`` to
    ``TEXT_COLOR`` entities.
    """

    mutability = "MUTABLE"

    def get_attribute_data(self, attrs):
        """
        Extract the color from the style attribute and return it as
        an entity.
        """
        try:
            return {"color": cssutils.parseStyle(attrs["style"])["color"]}
        except Exception:
            return {}


def text_color_entity_decorator(props):
    """
    Draft.js ContentState to database HTML.
    Converts ``TEXT_COLOR`` entities to span elements with
    ``style="color: <color>;"``.
    """
    color = props.get("color", None)
    children = props.get("children", None)

    if not color and not children:
        return None

    attrs = {}
    if color:
        attrs["style"] = f"color: {color};"
    attrs["data-entity-type"] = "TEXT_COLOR"
    return DOM.create_element("span", attrs, children)


def register(features):
    if not feature_enabled("TEXT_COLOR"):
        return

    register_entity_feature(
        features,
        feature_name="text-color-entity",
        entity_type="TEXT_COLOR",
        attributes=["color", "style", "data-entity-type"],
        decorator_fn=text_color_entity_decorator,
        handler_cls=TextColorEntityHandler,
        js=["draftail_text_utils/js/text_color_entity.js"],
    )

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

"""
Draftail rich-text feature: Font size.

Registers:
- A ``"font-size-entity"`` EntityFeature for arbitrary font sizes.
- A ``"font-size"`` ControlFeature for the toolbar control.
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


class FontSizeEntityHandler(InlineEntityElementHandler):
    """
    Database HTML to Draft.js ContentState.
    Converts span elements with ``style="font-size: <size>px;"`` to
    ``FONT_SIZE_<size>`` entities.
    """

    mutability = "MUTABLE"

    def get_attribute_data(self, attrs):
        """
        Extract the font size from the style attribute and return it as
        an entity.
        """
        try:
            return {"size": cssutils.parseStyle(attrs["style"])["font-size"]}
        except Exception:
            return {}


def font_size_entity_decorator(props):
    """
    Draft.js ContentState to database HTML.
    Converts ``FONT_SIZE`` entities to span elements with
    ``style="font-size: <size>;"``.
    """
    size = props.get("size")
    children = props.get("children")
    attrs = {}
    if size:
        attrs["style"] = f"font-size: {size};"
    attrs["data-entity-type"] = "FONT_SIZE"
    return DOM.create_element("span", attrs, children)


def register(features):
    if not feature_enabled("FONT_SIZE"):
        return

    register_entity_feature(
        features,
        feature_name="font-size-entity",
        entity_type="FONT_SIZE",
        attributes=["size", "style", "data-entity-type"],
        decorator_fn=font_size_entity_decorator,
        handler_cls=FontSizeEntityHandler,
        js=["draftail_text_utils/js/font_size_entity.js"],
    )

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

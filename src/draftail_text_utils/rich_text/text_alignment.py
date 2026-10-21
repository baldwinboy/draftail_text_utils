"""
Draftail rich-text feature: Text alignment.

Registers:
- Legacy ``BlockFeature``s for old, block-type-based alignment content.
- A ``"text-alignment"`` ControlFeature for the toolbar button group.
- Converter rules that store alignment in block data, so alignment can
  coexist with heading, list, and other default block types.
"""

from django.utils.translation import gettext_lazy as _
from draftjs_exporter.defaults import render_children
from draftjs_exporter.dom import DOM
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    BLOCK_KEY_NAME,
    Block,
    BlockElementHandler,
)

from draftail_text_utils.conf import feature_enabled

from .base import (
    control_json_script,
    register_block_feature,
    register_control_feature,
)


ALIGNMENTS = [
    ("ALIGNMENT_LEFT", "left", "start", _("Left")),
    ("ALIGNMENT_CENTER", "center", "center", _("Center")),
    ("ALIGNMENT_RIGHT", "right", "end", _("Right")),
    ("ALIGNMENT_JUSTIFY", "justify", "justify", _("Justify")),
]

ALIGNMENT_STYLES = {
    value: style_value for _type, value, style_value, _label in ALIGNMENTS
}
STYLE_ALIGNMENTS = {
    style_value: value for _type, value, style_value, _label in ALIGNMENTS
}

BLOCK_TAGS = [
    ("unstyled", "p"),
    ("header-one", "h1"),
    ("header-two", "h2"),
    ("header-three", "h3"),
    ("header-four", "h4"),
    ("header-five", "h5"),
    ("header-six", "h6"),
    ("blockquote", "blockquote"),
    ("code-block", "pre"),
]

LIST_TAGS = [
    ("ordered-list-item", "ol"),
    ("unordered-list-item", "ul"),
]


class AlignmentBlock(Block):
    """A block that persists alignment in its Draft.js ``data`` field."""

    def __init__(self, typ, depth=0, key=None, alignment=None):
        super().__init__(typ, depth, key)
        self.data = {"alignment": alignment or "left"}

    def as_dict(self):
        return super().as_dict() | {"data": self.data}


class AlignmentHandler(BlockElementHandler):
    """Database HTML to ContentState, preserving the original block type."""

    def __init__(self, block_type=None):
        self.block_type = block_type

    def create_block(self, name, attrs, state, contentstate):
        block_type = self.block_type or state.list_item_type or "unstyled"
        style_value = attrs.get("data-dtu-text-align", "start")
        alignment = STYLE_ALIGNMENTS.get(style_value, "left")

        return AlignmentBlock(
            block_type,
            depth=state.list_depth,
            key=attrs.get(BLOCK_KEY_NAME),
            alignment=alignment,
        )


def _alignment_element(tag_name):
    """
    Build a Draft.js exporter element function for ``tag_name``.

    Alignment is read from block data and only added to the output when
    present, so unaligned blocks keep their normal database representation.
    """

    def element(props):
        block = props.get("block") or {}
        data = block.get("data") or {}
        alignment = data.get("alignment")

        attrs = {}
        if alignment:
            style_value = ALIGNMENT_STYLES.get(alignment)
            if style_value:
                attrs["class"] = "dtu-block_text-align"
                attrs["data-dtu-text-align"] = style_value

        return DOM.create_element(tag_name, attrs, render_children(props))

    element.__name__ = f"text_alignment_{tag_name}"
    element.__repr__ = lambda _self: f"text_alignment_{tag_name}"
    return element


def _alignment_converter_rule():
    block_map = {}
    from_database_format = {}

    for block_type, tag_name in BLOCK_TAGS:
        block_map[block_type] = {"element": _alignment_element(tag_name)}
        for _type, _value, style_value, _label in ALIGNMENTS:
            from_database_format[f"{tag_name}[data-dtu-text-align='{style_value}']"] = (
                AlignmentHandler(block_type)
            )

    for block_type, wrapper in LIST_TAGS:
        block_map[block_type] = {
            "element": _alignment_element("li"),
            "wrapper": wrapper,
        }
        for _type, _value, style_value, _label in ALIGNMENTS:
            from_database_format[f"li[data-dtu-text-align='{style_value}']"] = (
                AlignmentHandler()
            )

    return {
        "from_database_format": from_database_format,
        "to_database_format": {"block_map": block_map},
    }


def register(features):
    if not feature_enabled("TEXT_ALIGNMENT"):
        return

    # Keep parsing and re-saving old alignment content, which used block types
    # and a div wrapper. Scope the selectors to ``div`` so they cannot match
    # the new, alignment-preserving heading/list elements.
    for type_, _value, style_value, _label in ALIGNMENTS:
        register_block_feature(
            features,
            type_,
            {},
            css_selector=f"div.dtu-block_text-align[data-dtu-text-align='{style_value}']",
            props={
                "class": "dtu-block_text-align",
                "data-dtu-text-align": style_value,
            },
        )

    register_control_feature(
        features,
        "text-alignment",
        js=["draftail_text_utils/js/text_alignment.js"],
        css={"all": ("draftail_text_utils/css/text_alignment.css",)},
    )

    features.register_converter_rule(
        "contentstate",
        "text-alignment",
        _alignment_converter_rule(),
    )


def control():
    if not feature_enabled("TEXT_ALIGNMENT"):
        return

    return control_json_script(
        type_="text-alignment",
        label="Align Text",
        description="Change text alignment",
        icon="align-left",
        data=[
            {
                "type": type_,
                "value": value,
                "label": label,
                "style": {"textAlign": style_value},
                "icon": f"align-{value}",
            }
            for type_, value, style_value, label in ALIGNMENTS
        ],
    )

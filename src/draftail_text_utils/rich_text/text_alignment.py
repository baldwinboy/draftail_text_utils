"""
Draftail rich-text feature: Text alignment.

Registers:
- Four ``BlockFeature``s per alignment value.
- A ``"text-alignment"`` ControlFeature for the toolbar button group.
"""

from django.utils.translation import gettext_lazy as _

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


def register(features):
    if not feature_enabled("TEXT_ALIGNMENT"):
        return

    for type_, _value, styleValue, _label in ALIGNMENTS:
        register_block_feature(
            features,
            type_,
            {},
            css_selector=f".dtu-block_text-align[data-dtu-text-align='{styleValue}']",
            props={
                "class": "dtu-block_text-align",
                "data-dtu-text-align": styleValue,
            },
        )

    register_control_feature(
        features,
        "text-alignment",
        js=["draftail_text_utils/js/text_alignment.js"],
        css={"all": ("draftail_text_utils/css/text_alignment.css",)},
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
                "label": label,
                "style": {"textAlign": styleValue},
                "icon": f"align-{value}",
            }
            for type_, value, styleValue, label in ALIGNMENTS
        ],
    )

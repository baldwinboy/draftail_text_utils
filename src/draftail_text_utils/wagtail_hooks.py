"""
Wagtail hooks for draftail_text_utils.

Integrates all rich-text feature registrations and injects the
necessary CSS / JS assets into the Wagtail admin.
"""

import json

from urllib.parse import urljoin

from django.core.serializers.json import DjangoJSONEncoder
from django.templatetags.static import static
from django.utils.html import escape, format_html, mark_safe
from wagtail import hooks

from draftail_text_utils.conf import (
    feature_enabled,
    font_family_type_id,
    get_font_sizes,
    load_color_palette,
    load_font_families,
    load_font_urls,
)
from draftail_text_utils.rich_text import (
    dynamic_link,
    font_family,
    font_size,
    highlight_color,
    text_alignment,
    text_color,
    text_style,
)


@hooks.register("register_icons")
def register_icons(icons):
    return icons + [
        "draftail_text_utils/icons/align-center.svg",
        "draftail_text_utils/icons/align-justify.svg",
        "draftail_text_utils/icons/align-left.svg",
        "draftail_text_utils/icons/align-right.svg",
        "draftail_text_utils/icons/anchor.svg",
        "draftail_text_utils/icons/font.svg",
        "draftail_text_utils/icons/highlighter.svg",
        "draftail_text_utils/icons/palette.svg",
        "draftail_text_utils/icons/text-height.svg",
    ]


# ---------------------------------------------------------------------------
# Feature registration
# ---------------------------------------------------------------------------


@hooks.register("register_rich_text_features")
def register_text_style_feature(features):
    text_style.register(features)


@hooks.register("register_rich_text_features")
def register_text_alignment_feature(features):
    text_alignment.register(features)


@hooks.register("register_rich_text_features")
def register_text_color(features):
    text_color.register(features)


@hooks.register("register_rich_text_features")
def register_highlight_color(features):
    highlight_color.register(features)


@hooks.register("register_rich_text_features")
def register_font_family_feature(features):
    font_family.register(features)


@hooks.register("register_rich_text_features")
def register_font_size_feature(features):
    font_size.register(features)


@hooks.register("register_rich_text_features")
def register_dynamic_link_feature(features):
    dynamic_link.register(features)


# ---------------------------------------------------------------------------
# Asset injection
# ---------------------------------------------------------------------------


def _feature_static(path):
    return static(f"draftail_text_utils/{path}")


def _ordered_unique(items):
    """Return ``items`` de-duplicated while preserving order."""
    return list(dict.fromkeys(items))


@hooks.register("insert_global_admin_css")
def global_admin_css():
    links = []

    css_map = {
        "TEXT_COLOR": "css/text_color.css",
        "HIGHLIGHT_COLOR": "css/highlight_color.css",
        "FONT_FAMILY": "css/font_family.css",
        "FONT_SIZE": "css/font_size.css",
        "TEXT_ALIGNMENT": "css/text_alignment.css",
        "DYNAMIC_LINK": "css/dynamic_link.css",
    }

    for feature_name, css_path in css_map.items():
        if feature_enabled(feature_name):
            links.append(f'<link rel="stylesheet" href="{_feature_static(css_path)}">')

            if feature_name in ("TEXT_COLOR", "HIGHLIGHT_COLOR"):
                links.append(
                    f'<link rel="stylesheet" href="{_feature_static("css/color.css")}">'
                )

    # Add common assets if not empty
    if links:
        links.append(
            f'<link rel="stylesheet" href="{_feature_static("css/common.css")}">'
        )
        links.append(
            f'<link rel="preload" href="{_feature_static("js/common.js")}" as="script">'
        )
        links.append(f'<script src="{_feature_static("js/common.js")}"></script>')

    # Load font stylesheets (URLs come from settings/data, so escape them)
    preconnect_links = []
    for url in load_font_urls():
        if url:
            preconnect_links.append(
                f'<link rel="preconnect" href="{escape(urljoin(url, "/"))}">'
            )
            links.append(f'<link rel="stylesheet" href="{escape(url)}">')

    return mark_safe(  # noqa: S308
        "\n".join(_ordered_unique(links + preconnect_links))
    )


@hooks.register("insert_global_admin_js")
def global_admin_js():
    """
    Injects JS assets for draftail_text_utils rich-text
    features into the Wagtail admin
    """
    scripts = [
        format_html(
            "<script type='text/javascript'>{}</script>",
            mark_safe("window.draftailTextUtils = window.draftailTextUtils || {};"),
        ),
    ]

    if feature_enabled("TEXT_COLOR") or feature_enabled("HIGHLIGHT_COLOR"):
        colors = load_color_palette()
        scripts.append(_color_script(colors))

        if feature_enabled("TEXT_COLOR"):
            scripts.append(text_color.control())

        if feature_enabled("HIGHLIGHT_COLOR"):
            scripts.append(highlight_color.control())

    if feature_enabled("FONT_FAMILY"):
        families = load_font_families()
        scripts.append(_font_family_script(families))
        scripts.append(font_family.control())

    if feature_enabled("FONT_SIZE"):
        sizes = get_font_sizes()
        scripts.append(_font_size_script(sizes))
        scripts.append(font_size.control())

    if feature_enabled("TEXT_ALIGNMENT"):
        scripts.append(text_alignment.control())

    if feature_enabled("DYNAMIC_LINK"):
        scripts.append(dynamic_link.control())

    return mark_safe("\n".join(scripts))  # noqa: S308


# ---------------------------------------------------------------------------
# Inline data injection helpers
# ---------------------------------------------------------------------------


def _color_script(colors):
    text_colors = [
        {
            "type": f"TEXT_COLOR_{c['key'].upper()}",
            "label": c["label"],
            "value": c["value"],
            "key": c["key"],
            "style": {"color": c["value"]},
        }
        for c in colors
    ]
    highlight_colors = [
        {
            "type": f"HIGHLIGHT_COLOR_{c['key'].upper()}",
            "label": c["label"],
            "value": c["value"],
            "key": c["key"],
            "style": {"backgroundColor": c["value"]},
        }
        for c in colors
    ]
    data = {
        "customTextColors": text_colors,
        "customHighlightColors": highlight_colors,
    }
    json_str = json.dumps(data, cls=DjangoJSONEncoder)
    return format_html(
        "<script type='text/javascript'>{}</script>",
        mark_safe(  # noqa: S308
            f"Object.assign(window.draftailTextUtils, {json_str});"
        ),
    )


def _font_family_script(families):
    data = {
        "customFontFamilies": [
            {
                "label": str(f["label"]),
                "value": f["value"],
                "type": f.get("type") or font_family_type_id(f["label"]),
                "style": {"fontFamily": f["value"]},
            }
            for f in families
        ]
    }
    json_str = json.dumps(data, cls=DjangoJSONEncoder)
    return format_html(
        "<script type='text/javascript'>{}</script>",
        mark_safe(  # noqa: S308
            f"Object.assign(window.draftailTextUtils, {json_str});"
        ),
    )


def _font_size_script(sizes):
    data = {"customFontSizes": sizes}
    json_str = json.dumps(data, cls=DjangoJSONEncoder)
    return format_html(
        "<script type='text/javascript'>{}</script>",
        mark_safe(  # noqa: S308
            f"Object.assign(window.draftailTextUtils, {json_str});"
        ),
    )


# Keep original admin URL registration from the template


@hooks.register("register_admin_urls")
def register_admin_urls():
    from django.urls import include, path
    from django.views.i18n import JavaScriptCatalog

    urls = [
        path(
            "jsi18n/",
            JavaScriptCatalog.as_view(packages=["draftail_text_utils"]),
            name="javascript_catalog",
        ),
    ]

    return [
        path(
            "draftail_text_utils/",
            include(
                (urls, "draftail_text_utils"),
                namespace="draftail_text_utils",
            ),
        )
    ]

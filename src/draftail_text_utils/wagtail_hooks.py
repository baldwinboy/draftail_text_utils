"""
Wagtail hooks for draftail_text_utils.

Integrates all rich-text feature registrations and injects the
necessary CSS / JS assets into the Wagtail admin.
"""

import json

from urllib.parse import urljoin

from django.core.serializers.json import DjangoJSONEncoder
from django.templatetags.static import static
from django.utils.html import format_html, mark_safe
from wagtail import hooks

from draftail_text_utils.conf import (
    feature_enabled,
    get_font_sizes,
    load_color_palette,
    load_font_families,
    load_font_urls,
)
from draftail_text_utils.rich_text import (
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


# ---------------------------------------------------------------------------
# Asset injection
# ---------------------------------------------------------------------------


def _feature_static(path):
    return static(f"draftail_text_utils/{path}")


@hooks.register("insert_global_admin_css")
def global_admin_css():
    links = set()
    preconnect_links = set()

    css_map = {
        "TEXT_COLOR": "css/text_color.css",
        "HIGHLIGHT_COLOR": "css/highlight_color.css",
        "FONT_FAMILY": "css/font_family.css",
        "FONT_SIZE": "css/font_size.css",
        "TEXT_ALIGNMENT": "css/text_alignment.css",
    }

    for feature_name, css_path in css_map.items():
        if feature_enabled(feature_name):
            links.add(f'<link rel="stylesheet" href="{_feature_static(css_path)}">')

            if feature_name == "TEXT_COLOR" or feature_name == "HIGHLIGHT_COLOR":
                links.add(
                    f'<link rel="stylesheet" href="{_feature_static("css/color.css")}">'
                )

    # Add common assets if not empty
    if len(links) > 0:
        links.add(f'<link rel="stylesheet" href="{_feature_static("css/common.css")}">')
        links.add(
            f'<link rel="preload" href="{_feature_static("js/common.js")}" as="script">'
        )
        links.add(f'<script src="{_feature_static("js/common.js")}"></script>')

    # Load font stylesheets
    for url in load_font_urls():
        if url:
            preconnect_links.add(f'<link rel="preconnect" href="{urljoin(url, "/")}">')
            links.add(f'<link rel="stylesheet" href="{url}">')

    return mark_safe("\n".join(links.union(preconnect_links)))  # noqa: S308


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
    text_color_style_map = {
        f"TEXT_COLOR_{c['key'].upper()}": {"color": c["value"]} for c in colors
    }
    highlight_color_style_map = {
        f"HIGHLIGHT_COLOR_{c['key'].upper()}": {"backgroundColor": c["value"]}
        for c in colors
    }

    data = {
        "customTextColors": text_colors,
        "customHighlightColors": highlight_colors,
        "customTextColorStyleMap": text_color_style_map,
        "customHighlightColorStyleMap": highlight_color_style_map,
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
                "label": f["label"],
                "value": f["value"],
                "type": f.get(
                    "type", f"FONT_FAMILY_{f['label'].upper().replace(' ', '_')}"
                ),
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

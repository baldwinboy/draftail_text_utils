"""
Shared utilities for registering Draftail rich-text features.

Provides helpers to reduce boilerplate when registering inline-style
features, converter rules, and control plugins.
"""


from django.utils.html import json_script
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    BlockElementHandler,
    InlineStyleElementHandler,
)
from wagtail.admin.rich_text.editors.draftail.features import (
    BlockFeature,
    ControlFeature,
    EntityFeature,
    InlineStyleFeature,
)


def control_json_script(type_, label, description, icon, data=None):
    """
    Returns a JSON script for a toolbar control plugin for Draftail.
    """
    return json_script(
        {
            "type": type_,
            "label": label,
            "description": description,
            "icon": icon,
            "data": data,
        },
        f"draftail-plugin-control-{type_}",
    )


def register_inline_style_feature(
    features,
    type_,
    style,
    css_selector,
    element="span",
    props=None,
    label=None,
    description=None,
    icon=None,
):
    """
    Register a single inline-style Draftail feature with its converter rules.

    :param features: The Features registry from the hook.
    :param type_: Unique type identifer (e.g. ``"TEXT_COLOR_RED"``).
    :param style: Draftail style dict (e.g. ``{"color": "#EF4444"}``).
        Property names must be camelCase, i.e. `textAlign` instead of `text-align`.
    :param css_selector: CSS selector for `from_database_format` (e.g.
        ``'span[style="color: #EF4444;"]'``).
    :param element: HTML element to use when converting back (default ``span``).
    :param props: Extra HTML props for the output element.
    :param label: Label for the control in the toolbar.
    :param description: Description for the control in the toolbar.
    :param icon: Icon name for the control in the toolbar.
    """
    control = {
        "type": type_,
        "style": style,
    }
    props = props or {}
    props["style"] = style

    if label:
        control["label"] = label
    if description:
        control["description"] = description
    if icon:
        control["icon"] = icon

    features.register_editor_plugin(
        "draftail",
        type_,
        InlineStyleFeature(control),
    )

    db_conversion = {
        "from_database_format": {css_selector: InlineStyleElementHandler(type_)},
        "to_database_format": {
            "style_map": {type_: {"element": element, "props": props}}
        },
    }

    features.register_converter_rule("contentstate", type_, db_conversion)
    features.default_features.append(type_)


def register_block_feature(
    features,
    type_,
    style,
    css_selector,
    element="div",
    props=None,
    label=None,
    description=None,
    icon=None,
):
    """
    Register a single block Draftail feature with its converter rules.

    :param features: The Features registry from the hook.
    :param type_: Unique type identifer (e.g. ``"TEXT_COLOR_RED"``).
    :param style: Draftail style dict (e.g. ``{"color": "#EF4444"}``).
        Property names must be camelCase, i.e. `textAlign` instead of `text-align`.
    :param css_selector: CSS selector for `from_database_format` (e.g.
        ``'span[style="color: #EF4444;"]'``).
    :param element: HTML element to use when converting back (default ``span``).
    :param props: Extra HTML props for the output element.
    :param label: Label for the control in the toolbar.
    :param description: Description for the control in the toolbar.
    :param icon: Icon name for the control in the toolbar.
    """
    control = {
        "type": type_,
        "style": style,
    }
    props = props or {}
    props["style"] = style

    if label:
        control["label"] = label
    if description:
        control["description"] = description
    if icon:
        control["icon"] = icon

    features.register_editor_plugin(
        "draftail",
        type_,
        BlockFeature(control),
    )

    db_conversion = {
        "from_database_format": {css_selector: BlockElementHandler(type_)},
        "to_database_format": {
            "block_map": {type_: {"element": element, "props": props}}
        },
    }

    features.register_converter_rule("contentstate", type_, db_conversion)
    features.default_features.append(type_)


def register_control_feature(
    features,
    feature_name,
    label=None,
    description=None,
    icon=None,
    js_files=None,
    css_files=None,
    js=None,
    css=None,
):
    """
    Register a toolbar control plugin for Draftail.

    :param features: The Features registry.
    :param feature_name: The control's type identifer (e.g. ``"text-color"``).
    :param label: Label for the control in the toolbar.
    :param description: Description for the control in the toolbar.
    :param icon: Icon name for the control in the toolbar.
    :param js_files: List of JS file paths (e.g. ``["js/draftail/text_color.js"]``).
    :param css_files: Dict of CSS files (e.g. ``{"all": ("css/draftail/text_color.css",)}``).
    """
    js_files = js_files or js or []
    css_files = css_files or css or {}
    control = {
        "type": feature_name,
    }

    if label:
        control["label"] = label
    if description:
        control["description"] = description
    if icon:
        control["icon"] = icon
    features.register_editor_plugin(
        "draftail",
        feature_name,
        ControlFeature(
            control,
            js=js_files,
            css=css_files,
        ),
    )
    features.default_features.append(feature_name)


def register_entity_feature(
    features,
    feature_name,
    entity_type,
    attributes,
    decorator_fn,
    handler_cls,
    label=None,
    description=None,
    icon=None,
    js_files=None,
    css_files=None,
    js=None,
    css=None,
):
    """
    Register an entity-based Draftail feature (used for custom/arbitrary values).

    :param features: The Features registry.
    :param feature_name: Feature name (e.g. ``"custom-text-color"``).
    :param entity_type: Draftail entity type (e.g. ``"CUSTOM_TEXT_COLOR"``).
    :param attributes: Entity attributes list.
    :param decorator_fn: Callable that receives props and returns a DOM element.
    :param handler_cls: Subclass of ``InlineEntityElementHandler``.
    :param label: Label for the control in the toolbar.
    :param description: Description for the control in the toolbar.
    :param icon: Icon name for the control in the toolbar.
    :param js_files: JS files for the entity plugin.
    :param css_files: Dict of CSS files (e.g. ``{"all": ("css/draftail/text_color.css",)}``).
    """
    js_files = js_files or js or []
    css_files = css_files or css or {}

    control = {
        "type": entity_type,
        "attributes": attributes,
    }

    if label:
        control["label"] = label
    if description:
        control["description"] = description
    if icon:
        control["icon"] = icon

    features.register_editor_plugin(
        "draftail",
        feature_name,
        EntityFeature(
            control,
            js=js_files,
            css=css_files,
        ),
    )

    features.register_converter_rule(
        "contentstate",
        feature_name,
        {
            "from_database_format": {
                f"span[data-entity-type='{entity_type}']": handler_cls(entity_type),
            },
            "to_database_format": {
                "entity_decorators": {
                    entity_type: decorator_fn,
                }
            },
        },
    )

    features.default_features.append(feature_name)

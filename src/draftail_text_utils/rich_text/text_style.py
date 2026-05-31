import cssutils

from django.urls import reverse_lazy
from django.utils.html import escape
from draftjs_exporter.dom import DOM
from wagtail.admin.rich_text.converters.contentstate_models import (
    Entity,
    EntityRange,
)
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    FORCE_WHITESPACE,
    STRIP_WHITESPACE,
    InlineEntityElementHandler,
)
from wagtail.admin.rich_text.editors.draftail.features import EntityFeature
from wagtail.models import Page
from wagtail.rich_text import LinkHandler
from wagtail.whitelist import check_url


STYLE_KEYS = {"color", "backgroundColor", "size"}
LINK_KEYS = {"url", "id", "parentId"}


class TextStyleEntityHandler(InlineEntityElementHandler):
    """
    Database HTML to Draft.js ContentState.
    Converts span elements with ``data-entity-type="TEXT_STYLE"``
    and a ``style`` attribute into a single ``TEXT_STYLE`` entity
    with ``color``, ``backgroundColor``, and ``size`` data.
    """

    mutability = "MUTABLE"

    def get_attribute_data(self, attrs):
        try:
            style = cssutils.parseStyle(attrs["style"])
            data = {"url": ""}
            color = style.getPropertyValue("color")
            if color:
                data["color"] = color
            bg = style.getPropertyValue("background-color")
            if bg:
                data["backgroundColor"] = bg
            size = style.getPropertyValue("font-size")
            if size:
                data["size"] = size

            return data
        except Exception:
            return {}


class StyledLinkElementHandler(InlineEntityElementHandler):
    """
    Database HTML to Draft.js ContentState for ``<a>`` tags.

    Produces a ``LINK`` entity for unstyled links (no
    ``data-entity-type="TEXT_STYLE"``), and a ``TEXT_STYLE`` entity
    for styled links (with ``data-entity-type="TEXT_STYLE"``).

    The entity data carries both link fields (``id``, ``url``,
    ``parentId``) and style fields (``color``, ``backgroundColor``,
    ``size``) when applicable.
    """

    mutability = "MUTABLE"

    def handle_starttag(self, name, attrs, state, contentstate):
        if state.current_block is None:
            from wagtail.admin.rich_text.converters.html_to_contentstate import (
                add_paragraph_block,
            )

            add_paragraph_block(state, contentstate)

        if state.leading_whitespace == FORCE_WHITESPACE:
            state.current_block.text += " "
            state.leading_whitespace = STRIP_WHITESPACE

        attrs = dict(attrs)
        is_styled = attrs.get("data-entity-type") == "TEXT_STYLE"
        entity_type = "TEXT_STYLE" if is_styled else self.entity_type

        entity = Entity(
            entity_type,
            self.mutability,
            self.get_attribute_data(attrs),
        )
        key = contentstate.add_entity(entity)

        entity_range = EntityRange(key)
        entity_range.offset = len(state.current_block.text)
        state.current_block.entity_ranges.append(entity_range)
        state.current_entity_ranges.append(entity_range)

    def get_attribute_data(self, attrs):
        data = {}

        try:
            style = cssutils.parseStyle(attrs.get("style", ""))
            color = style.getPropertyValue("color")
            if color:
                data["color"] = color
            bg = style.getPropertyValue("background-color")
            if bg:
                data["backgroundColor"] = bg
            size = style.getPropertyValue("font-size")
            if size:
                data["size"] = size
        except Exception:  # noqa: S110
            # Style parsing is best-effort; entity data
            # may have just link fields and no style attrs.
            pass

        linktype = attrs.get("linktype")
        href = attrs.get("href")

        if linktype == "page":
            from wagtail.models import Page

            page_id = attrs.get("id")
            try:
                page = Page.objects.get(id=page_id).specific
                data["id"] = page.id
                data["url"] = page.url
                parent = page.get_parent()
                data["parentId"] = parent.id if parent else None
            except Page.DoesNotExist:
                data["id"] = int(page_id)
                data["url"] = None
                data["parentId"] = None
        elif href:
            data["url"] = href

        return data


def _has_styles(props):
    return any(props.get(k) for k in STYLE_KEYS)


def text_style_entity_decorator(props):
    """
    Draft.js ContentState to database HTML.

    Converts entities to the corresponding database HTML:
    - ``LINK`` entity without style data → ``<a>`` (plain link, backward
      compatible with Wagtail core format, no ``data-entity-type``).
    - ``TEXT_STYLE`` entity with link data and style data → ``<a>``
      with ``data-entity-type="TEXT_STYLE"`` (styled link).
    - ``TEXT_STYLE`` entity without link data → ``<span>`` with
      ``data-entity-type="TEXT_STYLE"`` (plain styled text).
    """
    color = props.get("color")
    background_color = props.get("backgroundColor")
    size = props.get("size")
    link_id = props.get("id")
    link_url = props.get("url")
    children = props.get("children")

    styles = []
    if color:
        styles.append(f"color: {color} !important")
    if background_color:
        styles.append(f"background-color: {background_color} !important")
    if size:
        if isinstance(size, (int, float)):
            size = f"{size}px"
        styles.append(f"font-size: {size} !important")

    has_styles = bool(styles)

    attrs = {}
    if has_styles:
        attrs["style"] = "; ".join(styles) + ";"

    if link_id is not None:
        attrs["linktype"] = "page"
        attrs["id"] = link_id
        if has_styles:
            attrs["data-entity-type"] = "TEXT_STYLE"
        return DOM.create_element("a", attrs, children)

    if link_url:
        attrs["href"] = check_url(link_url)
        if has_styles:
            attrs["data-entity-type"] = "TEXT_STYLE"
        return DOM.create_element("a", attrs, children)

    # span (no link) — always add data-entity-type for backward compatibility
    attrs["data-entity-type"] = "TEXT_STYLE"
    return DOM.create_element("span", attrs, children)


class StyledPageLinkHandler(LinkHandler):
    identifier = "page"

    @classmethod
    def get_model(cls):
        return Page

    @classmethod
    def expand_db_attributes(cls, attrs):
        style = attrs.get("style", "")
        try:
            page = cls.get_instance(attrs)
            href = page.url
            tag = f'<a href="{href}"'
        except Page.DoesNotExist:
            tag = "<a"
        if style:
            tag += f' style="{escape(style)}"'
        return tag + ">"

    @classmethod
    def expand_db_attributes_many(cls, attrs_list):
        instances = cls.get_many(attrs_list)
        results = []
        for attrs, page in zip(attrs_list, instances, strict=True):
            style = attrs.get("style", "")
            if page:
                href = page.url
                tag = f'<a href="{href}"'
            else:
                tag = "<a"
            if style:
                tag += f' style="{escape(style)}"'
            tag += ">"
            results.append(tag)
        return results


def register(features):
    features.register_editor_plugin(
        "draftail",
        "text-style-entity",
        EntityFeature(
            {
                "type": "TEXT_STYLE",
                "attributes": [
                    "color",
                    "backgroundColor",
                    "size",
                    "url",
                    "id",
                    "parentId",
                ],
                "chooserUrls": {
                    "pageChooser": reverse_lazy("wagtailadmin_choose_page"),
                    "externalLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_external_link"
                    ),
                    "emailLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_email_link"
                    ),
                    "phoneLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_phone_link"
                    ),
                    "anchorLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_anchor_link"
                    ),
                },
            },
            js=[
                "wagtailadmin/js/page-chooser-modal.js",
                "draftail_text_utils/js/styled_link_source.js",
                "draftail_text_utils/js/text_style_entity.js",
            ],
        ),
    )

    features.register_converter_rule(
        "contentstate",
        "text-style-entity",
        {
            "from_database_format": {
                'span[data-entity-type="TEXT_STYLE"]': TextStyleEntityHandler(
                    "TEXT_STYLE"
                ),
                'a[data-entity-type="TEXT_STYLE"]': StyledLinkElementHandler(
                    "TEXT_STYLE"
                ),
            },
            "to_database_format": {
                "entity_decorators": {
                    "TEXT_STYLE": text_style_entity_decorator,
                }
            },
        },
    )

    features.register_link_type(StyledPageLinkHandler)
    features.default_features.append("text-style-entity")

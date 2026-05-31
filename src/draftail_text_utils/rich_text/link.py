from django.urls import reverse_lazy
from django.utils.html import escape
from wagtail.admin.rich_text.editors.draftail.features import EntityFeature
from wagtail.rich_text.pages import PageLinkHandler

from draftail_text_utils.rich_text.text_style import (
    StyledLinkElementHandler,
    text_style_entity_decorator,
)


class StyledPageLinkHandler(PageLinkHandler):
    """
    Extends PageLinkHandler to preserve the ``style`` attribute
    when rewriting database HTML to front-end HTML.
    """

    @classmethod
    def expand_db_attributes_many(cls, attrs_list):
        results = super().expand_db_attributes_many(attrs_list)
        for i, attrs in enumerate(attrs_list):
            style = attrs.get("style")
            if style:
                results[i] = results[i].rstrip(">") + f' style="{escape(style)}">'
        return results


def register(features):
    """
    Overrides Wagtail core's ``link`` feature to support styled links.

    - Replaces the editor plugin with ``StyledLinkSource``, which
      creates ``TEXT_STYLE`` entities with link data.
    - Replaces ``from_database_format`` handlers so that they produce
      ``TEXT_STYLE`` entities (instead of ``LINK``) when
      ``data-entity-type="TEXT_STYLE"`` is present.
    - Keeps the ``to_database_format`` decorator for both ``LINK`` and
      ``TEXT_STYLE`` so that plain links remain backward-compatible
      (no ``data-entity-type``) while styled links get the attribute.
    - Registers ``StyledPageLinkHandler`` to preserve the ``style``
      attribute during front-end rendering.
    """

    # 1. Replace the editor plugin for the "link" feature
    features.register_editor_plugin(
        "draftail",
        "link",
        EntityFeature(
            {
                "type": "LINK",
                "icon": "link",
                "description": "Link",
                "attributes": [
                    "url",
                    "id",
                    "parentId",
                    "color",
                    "backgroundColor",
                    "size",
                ],
                "allowlist": {
                    "href": "^(http:|https:|mailto:|#|undefined$)",
                },
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
            ],
        ),
    )

    # 2. Replace converter rules for the "link" feature
    features.register_converter_rule(
        "contentstate",
        "link",
        {
            "from_database_format": {
                'a[linktype="page"]': StyledLinkElementHandler("LINK"),
                "a[href]": StyledLinkElementHandler("LINK"),
            },
            "to_database_format": {
                "entity_decorators": {
                    "LINK": text_style_entity_decorator,
                    "TEXT_STYLE": text_style_entity_decorator,
                }
            },
        },
    )

    # 3. Register the styled-page link handler for front-end rendering
    features.register_link_type(StyledPageLinkHandler)

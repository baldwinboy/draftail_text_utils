from urllib.parse import urljoin

from django import template
from django.utils.html import escape, mark_safe

from draftail_text_utils.conf import load_font_urls
from draftail_text_utils.wagtail_hooks import _feature_static


register = template.Library()


@register.simple_tag
def draftail_text_assets():
    links = []

    # Load font stylesheets (URLs come from settings/data, so escape them)
    for url in load_font_urls():
        if url:
            links.append(f'<link rel="preconnect" href="{escape(urljoin(url, "/"))}">')
            links.append(f'<link rel="stylesheet" href="{escape(url)}">')

    # Load draftail stylesheets
    links.append(f'<link rel="stylesheet" href="{_feature_static("css/page.css")}">')

    return mark_safe(  # noqa: S308
        "\n".join(dict.fromkeys(links))
    )

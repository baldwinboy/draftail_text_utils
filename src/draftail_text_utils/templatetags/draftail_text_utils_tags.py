from urllib.parse import urljoin

from django import template
from django.utils.html import mark_safe

from draftail_text_utils.conf import load_font_urls
from draftail_text_utils.wagtail_hooks import _feature_static


register = template.Library()


@register.simple_tag
def draftail_text_assets():
    links = set()
    preconnect_links = set()

    # Load font stylesheets
    for url in load_font_urls():
        if url:
            preconnect_links.add(f'<link rel="preconnect" href="{urljoin(url, "/")}">')
            links.add(f'<link rel="stylesheet" href="{url}">')

    # Load draftail stylesheets
    links.add(f'<link rel="stylesheet" href="{_feature_static("css/page.css")}">')

    return mark_safe("\n".join(links.union(preconnect_links)))  # noqa: S308

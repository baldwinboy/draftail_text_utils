"""Tests for Draftail rich-text feature registration."""

import pytest

from django.test import override_settings
from draftjs_exporter.dom import DOM

from draftail_text_utils.rich_text import (
    font_family,
    font_size,
    highlight_color,
    text_alignment,
    text_color,
    text_style,
)


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def configure_dom():
    """Ensure draftjs_exporter DOM is configured for decorator tests."""
    from draftjs_exporter.engines.string import DOMString

    if DOM.dom is None:
        DOM.dom = DOMString
    yield


class FakeFeatures:
    """Minimal mock of the Wagtail features registry."""

    def __init__(self):
        self.plugins = {}
        self.converter_rules = {}
        self.default_features = []

    def register_editor_plugin(self, editor, feature_name, plugin):
        self.plugins[feature_name] = plugin

    def register_converter_rule(self, editor, feature_name, rule):
        self.converter_rules[feature_name] = rule

    def register_link_type(self, handler):
        self.link_type = handler


# ---------------------------------------------------------------------------
# Individual feature registration tests
# ---------------------------------------------------------------------------


class TestTextColorRegistration:
    def test_registers_control_plugin(self):
        features = FakeFeatures()
        text_color.register(features)
        assert "text-color" in features.plugins
        assert "text-color" in features.default_features

    def test_disabled_via_settings(self):
        with override_settings(DRAFTAIL_TEXT_UTILS={"FEATURES": {"TEXT_COLOR": False}}):
            features = FakeFeatures()
            text_color.register(features)
            assert "text-color" not in features.default_features


class TestHighlightColorRegistration:
    def test_registers_control_plugin(self):
        features = FakeFeatures()
        highlight_color.register(features)
        assert "highlight-color" in features.plugins
        assert "highlight-color" in features.default_features


class TestFontFamilyRegistration:
    def test_noop_without_families(self):
        features = FakeFeatures()
        font_family.register(features)
        font_types = [
            f for f in features.default_features if f.startswith("FONT_FAMILY_")
        ]
        assert len(font_types) == 0
        assert "font-family" not in features.default_features

    def test_registers_families_when_configured(self):
        with override_settings(
            DRAFTAIL_TEXT_UTILS={
                "FONT_FAMILIES": [
                    {"label": "Roboto", "value": "Roboto, sans-serif"},
                    {"label": "Merriweather", "value": "Merriweather, serif"},
                ]
            }
        ):
            features = FakeFeatures()
            font_family.register(features)
            assert "FONT_FAMILY_ROBOTO" in features.default_features
            assert "FONT_FAMILY_MERRIWEATHER" in features.default_features

    def test_registers_control_plugin(self):
        with override_settings(
            DRAFTAIL_TEXT_UTILS={
                "FONT_FAMILIES": [
                    {"label": "Roboto", "value": "Roboto, sans-serif"},
                ]
            }
        ):
            features = FakeFeatures()
            font_family.register(features)
            assert "font-family" in features.plugins
            assert "font-family" in features.default_features


class TestFontSizeRegistration:
    def test_registers_control_plugin(self):
        features = FakeFeatures()
        font_size.register(features)
        assert "font-size" in features.plugins
        assert "font-size" in features.default_features

    def test_custom_range_via_settings(self):
        with override_settings(
            DRAFTAIL_TEXT_UTILS={
                "FONT_SIZES": {
                    "MIN": 20,
                    "MAX": 30,
                    "STEP": 5,
                    "PRESETS": [20, 25, 30],
                }
            }
        ):
            features = FakeFeatures()
            font_size.register(features)
            assert "font-size" in features.default_features


class TestTextStyleRegistration:
    def test_registers_entity_feature(self):
        features = FakeFeatures()
        text_style.register(features)
        assert "text-style-entity" in features.plugins
        assert "text-style-entity" in features.default_features

    def test_creates_converter_rules(self):
        features = FakeFeatures()
        text_style.register(features)
        assert "text-style-entity" in features.converter_rules
        rule = features.converter_rules["text-style-entity"]
        assert "from_database_format" in rule
        assert "to_database_format" in rule
        assert "entity_decorators" in rule["to_database_format"]
        assert "TEXT_STYLE" in rule["to_database_format"]["entity_decorators"]

    def test_entity_handler_parses_color(self):
        handler = text_style.TextStyleEntityHandler("TEXT_STYLE")
        data = handler.get_attribute_data({"style": "color: #a1b2c3;"})
        assert data["color"] == "#a1b2c3"

    def test_entity_handler_parses_background_color(self):
        handler = text_style.TextStyleEntityHandler("TEXT_STYLE")
        data = handler.get_attribute_data({"style": "background-color: #123abc;"})
        assert data["backgroundColor"] == "#123abc"

    def test_entity_handler_parses_font_size(self):
        handler = text_style.TextStyleEntityHandler("TEXT_STYLE")
        data = handler.get_attribute_data({"style": "font-size: 18px;"})
        assert data["size"] == "18px"

    def test_entity_handler_parses_combined_style(self):
        handler = text_style.TextStyleEntityHandler("TEXT_STYLE")
        data = handler.get_attribute_data(
            {"style": "color: #a1b2c3; background-color: #123abc; font-size: 18px;"}
        )
        assert data["color"] == "#a1b2c3"
        assert data["backgroundColor"] == "#123abc"
        assert data["size"] == "18px"

    def test_entity_handler_returns_url_on_parse_error(self):
        handler = text_style.TextStyleEntityHandler("TEXT_STYLE")
        data = handler.get_attribute_data({"style": "invalid"})
        assert data == {"url": ""}

    def test_entity_decorator_creates_span_with_color(self):
        el = text_style.text_style_entity_decorator(
            {"color": "#ff0000", "children": "text"}
        )
        assert el.type == "span"
        assert el.attr.get("data-entity-type") == "TEXT_STYLE"
        assert "color: #ff0000 !important" in el.attr.get("style", "")

    def test_entity_decorator_creates_span_with_all_properties(self):
        el = text_style.text_style_entity_decorator(
            {
                "color": "#ff0000",
                "backgroundColor": "#00ff00",
                "size": "18px",
                "children": "text",
            }
        )
        assert el.type == "span"
        assert el.attr.get("data-entity-type") == "TEXT_STYLE"
        style = el.attr.get("style", "")
        assert "color: #ff0000 !important" in style
        assert "background-color: #00ff00 !important" in style
        assert "font-size: 18px !important" in style

    def test_entity_decorator_converts_numeric_size_to_px(self):
        """Numeric size values should be converted to px strings."""
        el = text_style.text_style_entity_decorator({"size": 18, "children": "text"})
        style = el.attr.get("style", "")
        assert "font-size: 18px !important" in style

    def test_entity_decorator_converts_numeric_size_to_px_in_link(self):
        """Numeric size values should be converted to px in link entities."""
        el = text_style.text_style_entity_decorator(
            {
                "id": 1,
                "url": "/test/",
                "size": 24,
                "children": "linked",
            }
        )
        assert el.type == "a"
        style = el.attr.get("style", "")
        assert "font-size: 24px !important" in style

    def test_entity_decorator_handles_no_properties(self):
        el = text_style.text_style_entity_decorator({"children": "text"})
        assert el.type == "span"
        assert el.attr.get("data-entity-type") == "TEXT_STYLE"
        assert "style" not in el.attr

    def test_registers_anchor_handler_in_from_database_format(self):
        features = FakeFeatures()
        text_style.register(features)
        rule = features.converter_rules["text-style-entity"]
        from_db = rule["from_database_format"]
        assert 'a[data-entity-type="TEXT_STYLE"]' in from_db
        assert 'span[data-entity-type="TEXT_STYLE"]' in from_db

    def test_registers_page_link_handler(self):
        features = FakeFeatures()
        text_style.register(features)
        assert hasattr(features, "link_type")


class TestTextAlignmentRegistration:
    def test_registers_all_alignments(self):
        features = FakeFeatures()
        text_alignment.register(features)
        for align_type in [
            "ALIGNMENT_LEFT",
            "ALIGNMENT_CENTER",
            "ALIGNMENT_RIGHT",
            "ALIGNMENT_JUSTIFY",
        ]:
            assert align_type in features.default_features

    def test_registers_control_plugin(self):
        features = FakeFeatures()
        text_alignment.register(features)
        assert "text-alignment" in features.plugins
        assert "text-alignment" in features.default_features

    def test_converter_uses_div_element(self):
        features = FakeFeatures()
        text_alignment.register(features)
        rule = features.converter_rules["ALIGNMENT_CENTER"]
        block_entry = rule["to_database_format"]["block_map"]["ALIGNMENT_CENTER"]
        assert block_entry["element"] == "div"
        assert "dtu-block_text-align" in block_entry["props"]["class"]

    def test_disabled_via_settings(self):
        with override_settings(
            DRAFTAIL_TEXT_UTILS={"FEATURES": {"TEXT_ALIGNMENT": False}}
        ):
            features = FakeFeatures()
            text_alignment.register(features)
            assert "text-alignment" not in features.default_features


class TestFeatureDisabling:
    def test_disable_all_features(self):
        with override_settings(
            DRAFTAIL_TEXT_UTILS={
                "FEATURES": {
                    "TEXT_COLOR": False,
                    "HIGHLIGHT_COLOR": False,
                    "FONT_FAMILY": False,
                    "FONT_SIZE": False,
                    "TEXT_ALIGNMENT": False,
                }
            }
        ):
            features = FakeFeatures()
            text_style.register(features)
            text_color.register(features)
            highlight_color.register(features)
            font_family.register(features)
            font_size.register(features)
            text_alignment.register(features)
            assert "text-style-entity" in features.default_features  # always registered
            assert "text-color" not in features.default_features
            assert "highlight-color" not in features.default_features
            assert "font-family" not in features.default_features
            assert "font-size" not in features.default_features
            assert "text-alignment" not in features.default_features


# ---------------------------------------------------------------------------
# Wagtail hooks integration tests
# ---------------------------------------------------------------------------


class TestHookAssetInjection:
    def test_global_admin_css_includes_all_features(self):
        from draftail_text_utils.wagtail_hooks import global_admin_css

        result = global_admin_css()
        html = str(result)
        assert "draftail_text_utils/css/text_color.css" in html
        assert "draftail_text_utils/css/highlight_color.css" in html
        assert "draftail_text_utils/css/font_family.css" in html
        assert "draftail_text_utils/css/font_size.css" in html
        assert "draftail_text_utils/css/text_alignment.css" in html

    def test_global_admin_css_respects_disabled_features(self):
        with override_settings(
            DRAFTAIL_TEXT_UTILS={
                "FEATURES": {"TEXT_COLOR": False, "HIGHLIGHT_COLOR": False}
            }
        ):
            from draftail_text_utils.wagtail_hooks import global_admin_css

            result = global_admin_css()
            html = str(result)
            assert "draftail_text_utils/css/text_color.css" not in html
            assert "draftail_text_utils/css/highlight_color.css" not in html
            assert "draftail_text_utils/css/font_family.css" in html
            assert "draftail_text_utils/css/font_size.css" in html
            assert "draftail_text_utils/css/text_alignment.css" in html

    def test_global_admin_js_injects_data(self):
        from draftail_text_utils.wagtail_hooks import global_admin_js

        result = global_admin_js()
        html = str(result)
        assert "draftailTextUtils" in html

    def test_global_admin_js_includes_color_data(self):
        from draftail_text_utils.wagtail_hooks import global_admin_js

        result = global_admin_js()
        html = str(result)
        assert "customTextColors" in html
        assert "customHighlightColors" in html
        assert "customFontFamilies" in html

    def test_register_admin_urls(self):
        from draftail_text_utils.wagtail_hooks import register_admin_urls

        urls = register_admin_urls()
        assert len(urls) == 1
        pattern = urls[0].pattern
        assert pattern.regex.pattern.startswith("^draftail_text_utils/")


# ---------------------------------------------------------------------------
# Converter integration tests (round-trip)
# ---------------------------------------------------------------------------


class TestConverterRoundTrip:
    """Test that database HTML can round-trip through the converter."""

    def test_text_style_entity_rule_registered(self):
        features = FakeFeatures()
        text_style.register(features)
        rule = features.converter_rules["text-style-entity"]
        assert "from_database_format" in rule
        assert "to_database_format" in rule
        assert "TEXT_STYLE" in rule["to_database_format"]["entity_decorators"]

    def test_text_style_decorator_creates_span(self):
        el = text_style.text_style_entity_decorator(
            {"color": "#ff00ff", "children": "magic"}
        )
        assert el.type == "span"
        assert el.attr["data-entity-type"] == "TEXT_STYLE"

    def test_text_style_handler_parses_combined_style(self):
        handler = text_style.TextStyleEntityHandler("TEXT_STYLE")
        data = handler.get_attribute_data(
            {"style": "color: #abc123; background-color: #def456; font-size: 18px;"}
        )
        assert data["color"] == "#abc123"
        assert data["backgroundColor"] == "#def456"
        assert data["size"] == "18px"


# ---------------------------------------------------------------------------
# Styled link handler tests
# ---------------------------------------------------------------------------


class TestStyledLinkElementHandler:
    """Tests for StyledLinkElementHandler (from_database_format for <a> tags)."""

    def test_handles_external_link_with_style(self):
        handler = text_style.StyledLinkElementHandler("TEXT_STYLE")
        data = handler.get_attribute_data(
            {
                "href": "https://example.com",
                "style": "color: #ff0000;",
                "data-entity-type": "TEXT_STYLE",
            }
        )
        assert data["url"] == "https://example.com"
        # cssutils normalizes #ff0000 → #f00
        assert data["color"] in ("#ff0000", "#f00", "red")

    def test_handles_external_link_without_style(self):
        handler = text_style.StyledLinkElementHandler("TEXT_STYLE")
        data = handler.get_attribute_data({"href": "https://example.com"})
        assert data["url"] == "https://example.com"

    def test_handles_missing_page_with_style(self):
        handler = text_style.StyledLinkElementHandler("TEXT_STYLE")
        data = handler.get_attribute_data(
            {
                "linktype": "page",
                "id": "99999",
                "style": "background-color: #00ff00; font-size: 18px;",
                "data-entity-type": "TEXT_STYLE",
            }
        )
        assert data["id"] == 99999
        assert data["url"] is None
        assert data["parentId"] is None
        # cssutils normalizes #00ff00 → #0f0
        assert data["backgroundColor"] in ("#00ff00", "#0f0", "lime")
        assert data["size"] == "18px"

    def test_handles_page_link_without_style(self):
        """Unstyled page link (no data-entity-type) → only link data."""
        handler = text_style.StyledLinkElementHandler("TEXT_STYLE")
        data = handler.get_attribute_data({"linktype": "page", "id": "99999"})
        assert data["id"] == 99999
        assert data["url"] is None
        assert "color" not in data


class TestTextStyleDecoratorStyledLinks:
    """Tests for text_style_entity_decorator with link data."""

    def test_decorator_creates_a_for_styled_page_link(self):
        el = text_style.text_style_entity_decorator(
            {"id": 1, "url": "/test/", "color": "#ff0000", "children": "linked"}
        )
        assert el.type == "a"
        assert el.attr.get("data-entity-type") == "TEXT_STYLE"
        assert el.attr.get("linktype") == "page"
        assert el.attr.get("id") == "1"
        assert "color: #ff0000 !important" in el.attr.get("style", "")

    def test_decorator_creates_a_for_external_styled_link(self):
        el = text_style.text_style_entity_decorator(
            {
                "url": "https://example.com",
                "backgroundColor": "#00ff00",
                "children": "linked",
            }
        )
        assert el.type == "a"
        assert el.attr.get("data-entity-type") == "TEXT_STYLE"
        assert el.attr.get("href") == "https://example.com"
        assert "background-color: #00ff00 !important" in el.attr.get("style", "")

    def test_decorator_creates_a_without_data_entity_type_for_plain_link(self):
        """Plain link without style data → <a> without data-entity-type."""
        el = text_style.text_style_entity_decorator(
            {"id": 1, "url": "/test/", "children": "linked"}
        )
        assert el.type == "a"
        assert "data-entity-type" not in el.attr
        assert el.attr.get("linktype") == "page"
        assert "style" not in el.attr

    def test_decorator_creates_a_without_data_entity_type_for_external_plain_link(self):
        el = text_style.text_style_entity_decorator(
            {"url": "https://example.com", "children": "linked"}
        )
        assert el.type == "a"
        assert "data-entity-type" not in el.attr
        assert el.attr.get("href") == "https://example.com"
        assert "style" not in el.attr

    def test_decorator_creates_span_when_no_link_data(self):
        el = text_style.text_style_entity_decorator(
            {"color": "#ff0000", "children": "text"}
        )
        assert el.type == "span"
        assert el.attr.get("data-entity-type") == "TEXT_STYLE"

    def test_decorator_creates_a_with_all_styles(self):
        """Styled link with all three style properties."""
        el = text_style.text_style_entity_decorator(
            {
                "id": 1,
                "url": "/test/",
                "color": "#ff0000",
                "backgroundColor": "#00ff00",
                "size": "18px",
                "children": "styled",
            }
        )
        assert el.type == "a"
        assert el.attr.get("data-entity-type") == "TEXT_STYLE"
        assert el.attr.get("linktype") == "page"
        assert el.attr.get("id") == "1"
        style = el.attr.get("style", "")
        assert "color: #ff0000 !important" in style
        assert "background-color: #00ff00 !important" in style
        assert "font-size: 18px !important" in style

    def test_decorator_handles_empty_url_string(self):
        """Empty url string should render as span, not link."""
        el = text_style.text_style_entity_decorator(
            {"color": "#ff0000", "url": "", "children": "text"}
        )
        assert el.type == "span"
        assert "href" not in el.attr


class TestStyledLinkHtmlOutput:
    """Verify the decorator produces correct HTML with data-entity-type."""

    def test_styled_external_link_html(self):
        """Styled external link renders <a> with data-entity-type and style."""
        from draftjs_exporter.dom import DOM

        el = text_style.text_style_entity_decorator(
            {"url": "https://example.com", "color": "#ff0000", "children": "linked"}
        )
        html = DOM.render(el)
        assert html.startswith("<a ")
        assert 'data-entity-type="TEXT_STYLE"' in html
        assert 'style="' in html
        assert "color: #ff0000 !important" in html
        assert 'href="https://example.com"' in html

    def test_styled_page_link_html(self):
        """Styled page link renders <a> with data-entity-type and style."""
        from draftjs_exporter.dom import DOM

        el = text_style.text_style_entity_decorator(
            {"id": 1, "url": "/test/", "color": "#ff0000", "children": "linked"}
        )
        html = DOM.render(el)
        assert html.startswith("<a ")
        assert 'data-entity-type="TEXT_STYLE"' in html
        assert 'style="' in html
        assert 'linktype="page"' in html
        assert 'id="1"' in html

    def test_plain_link_html_no_data_entity_type(self):
        """Plain link without style renders <a> without data-entity-type."""
        from draftjs_exporter.dom import DOM

        el = text_style.text_style_entity_decorator(
            {"url": "https://example.com", "children": "linked"}
        )
        html = DOM.render(el)
        assert html.startswith("<a ")
        assert "data-entity-type" not in html
        assert "style" not in html
        assert 'href="https://example.com"' in html

    def test_styled_span_html(self):
        """Styled text without link renders <span> with data-entity-type."""
        from draftjs_exporter.dom import DOM

        el = text_style.text_style_entity_decorator(
            {"color": "#ff0000", "children": "text"}
        )
        html = DOM.render(el)
        assert html.startswith("<span ")
        assert 'data-entity-type="TEXT_STYLE"' in html
        assert 'style="' in html

    def test_styled_link_with_all_styles_html(self):
        """Styled link with all style props renders correct HTML."""
        from draftjs_exporter.dom import DOM

        el = text_style.text_style_entity_decorator(
            {
                "id": 1,
                "url": "/test/",
                "color": "#ff0000",
                "backgroundColor": "#00ff00",
                "size": "18px",
                "children": "styled",
            }
        )
        html = DOM.render(el)
        assert 'data-entity-type="TEXT_STYLE"' in html
        assert "color: #ff0000 !important" in html
        assert "background-color: #00ff00 !important" in html
        assert "font-size: 18px !important" in html


class TestStyleLinkRoundTrip:
    """Verify round-trip: entity data → decorator HTML → handler → entity data."""

    def test_styled_external_link_round_trip(self):
        """External styled link survives decorator → handler round trip."""
        from draftjs_exporter.dom import DOM

        original = {"url": "/test/", "color": "#ff0000"}
        el = text_style.text_style_entity_decorator({**original, "children": "text"})
        html = DOM.render(el)
        handler = text_style.StyledLinkElementHandler("TEXT_STYLE")
        parsed = handler.get_attribute_data(dict(el.attr))
        assert parsed["url"] == original["url"]
        assert parsed["color"] in ("#ff0000", "#f00", "red")
        # Verify HTML string has the expected attributes
        assert 'data-entity-type="TEXT_STYLE"' in html

    def test_styled_missing_page_round_trip(self):
        """Styled page link to a non-existent page survives round trip."""
        from draftjs_exporter.dom import DOM

        original = {"id": 99999, "url": None, "color": "#ff0000"}
        el = text_style.text_style_entity_decorator({**original, "children": "text"})
        html = DOM.render(el)
        handler = text_style.StyledLinkElementHandler("TEXT_STYLE")
        parsed = handler.get_attribute_data(dict(el.attr))
        assert parsed["id"] == original["id"]
        assert parsed["url"] is None
        assert parsed.get("color") in ("#ff0000", "#f00", "red")
        assert 'data-entity-type="TEXT_STYLE"' in html

    def test_styled_link_with_all_properties_round_trip(self):
        """All style props survive decorator → handler for external link."""
        from draftjs_exporter.dom import DOM

        original = {
            "url": "https://example.com",
            "color": "#ff0000",
            "backgroundColor": "#00ff00",
            "size": "18px",
        }
        el = text_style.text_style_entity_decorator({**original, "children": "text"})
        html = DOM.render(el)
        handler = text_style.StyledLinkElementHandler("TEXT_STYLE")
        parsed = handler.get_attribute_data(dict(el.attr))
        assert parsed["url"] == original["url"]
        assert parsed["color"] in ("#ff0000", "#f00", "red")
        assert parsed["backgroundColor"] in ("#00ff00", "#0f0", "lime")
        assert parsed["size"] == "18px"
        assert 'data-entity-type="TEXT_STYLE"' in html

    def test_full_decorator_handler_round_trip(self):
        """Full round trip: entity → decorator HTML → handler → matching data."""
        from draftjs_exporter.dom import DOM

        original = {
            "url": "https://example.com",
            "color": "#ff0000",
            "backgroundColor": "#00ff00",
            "size": "18px",
        }
        el = text_style.text_style_entity_decorator({**original, "children": "text"})
        html = DOM.render(el)

        # Parse the HTML back through the handler
        handler = text_style.StyledLinkElementHandler("TEXT_STYLE")
        parsed = handler.get_attribute_data(dict(el.attr))
        assert parsed["url"] == original["url"]
        assert parsed.get("color") in ("#ff0000", "#f00", "red")
        assert parsed.get("backgroundColor") in ("#00ff00", "#0f0", "lime")
        assert parsed.get("size") == "18px"

        # Verify the HTML that would be stored in the DB
        assert "<a " in html
        assert 'href="https://example.com"' in html
        assert 'data-entity-type="TEXT_STYLE"' in html
        assert "color: #ff0000 !important" in html
        assert "background-color: #00ff00 !important" in html
        assert "font-size: 18px !important" in html


# ---------------------------------------------------------------------------
# StyledPageLinkHandler tests
# ---------------------------------------------------------------------------


class TestStyledPageLinkHandler:
    """Tests for StyledPageLinkHandler (front-end rewrite)."""

    def test_expand_with_style(self, page):
        from draftail_text_utils.rich_text.text_style import StyledPageLinkHandler

        result = StyledPageLinkHandler.expand_db_attributes(
            {"id": str(page.id), "style": "color: red;"}
        )
        assert "href=" in result
        assert 'style="color: red;"' in result

    def test_expand_without_style(self, page):
        from draftail_text_utils.rich_text.text_style import StyledPageLinkHandler

        result = StyledPageLinkHandler.expand_db_attributes({"id": str(page.id)})
        assert "href=" in result
        assert "style" not in result

    def test_expand_bulk_with_style(self, page):
        from draftail_text_utils.rich_text.text_style import StyledPageLinkHandler

        results = StyledPageLinkHandler.expand_db_attributes_many(
            [
                {"id": str(page.id), "style": "color: red;"},
                {"id": str(page.id)},
                {"id": str(page.id), "style": "background-color: blue;"},
            ]
        )
        assert len(results) == 3
        assert 'style="color: red;"' in results[0]
        assert "style" not in results[1]
        assert 'style="background-color: blue;"' in results[2]

    def test_expand_missing_page(self):
        from draftail_text_utils.rich_text.text_style import StyledPageLinkHandler

        result = StyledPageLinkHandler.expand_db_attributes(
            {"id": "99999", "style": "color: red;"}
        )
        assert result == '<a style="color: red;">'


# ---------------------------------------------------------------------------
# LinkRewriter end-to-end tests (front-end rendering)
# ---------------------------------------------------------------------------


class TestLinkRewriterStylePreservation:
    """Verify styles survive LinkRewriter processing (front-end rendering)."""

    def test_external_link_style_preserved(self):
        """External styled link passes through LinkRewriter unchanged."""
        from wagtail.rich_text.rewriters import LinkRewriter

        rewriter = LinkRewriter()
        db_html = (
            '<a href="https://example.com" '
            'data-entity-type="TEXT_STYLE" '
            'style="color: red; background-color: blue;">linked</a>'
        )
        result = rewriter(db_html)
        assert 'href="https://example.com"' in result
        assert 'style="color: red; background-color: blue;"' in result
        assert 'data-entity-type="TEXT_STYLE"' in result

    def test_page_link_style_preserved(self, page):
        """Styled page link style preserved through StyledPageLinkHandler."""
        from wagtail.rich_text.rewriters import LinkRewriter

        from draftail_text_utils.rich_text.text_style import StyledPageLinkHandler

        rewriter = LinkRewriter(
            bulk_rules={
                "page": StyledPageLinkHandler.expand_db_attributes_many,
            },
        )
        db_html = (
            f'<a linktype="page" id="{page.id}" '
            'data-entity-type="TEXT_STYLE" '
            'style="color: red;">linked</a>'
        )
        result = rewriter(db_html)
        assert 'href="' in result
        assert 'style="color: red;"' in result

    def test_external_link_without_style_unchanged(self):
        """External link without style passes through unchanged."""
        from wagtail.rich_text.rewriters import LinkRewriter

        rewriter = LinkRewriter()
        db_html = '<a href="https://example.com">linked</a>'
        result = rewriter(db_html)
        assert result == db_html

    def test_page_link_without_style(self, page):
        """Plain page link (no style) produces valid href via handler."""
        from wagtail.rich_text.rewriters import LinkRewriter

        from draftail_text_utils.rich_text.text_style import StyledPageLinkHandler

        rewriter = LinkRewriter(
            bulk_rules={
                "page": StyledPageLinkHandler.expand_db_attributes_many,
            },
        )
        db_html = f'<a linktype="page" id="{page.id}">linked</a>'
        result = rewriter(db_html)
        assert result.startswith('<a href="')
        assert "style" not in result

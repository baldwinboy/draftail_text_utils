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


# ---------------------------------------------------------------------------
# Individual feature registration tests
# ---------------------------------------------------------------------------


class TestTextColorRegistration:
    def test_registers_entity_feature(self):
        features = FakeFeatures()
        text_color.register(features)
        assert "text-color-entity" in features.plugins
        assert "text-color-entity" in features.default_features

    def test_registers_control_plugin(self):
        features = FakeFeatures()
        text_color.register(features)
        assert "text-color" in features.plugins
        assert "text-color" in features.default_features

    def test_creates_converter_rules(self):
        features = FakeFeatures()
        text_color.register(features)
        assert "text-color-entity" in features.converter_rules
        rule = features.converter_rules["text-color-entity"]
        assert "from_database_format" in rule
        assert "to_database_format" in rule
        assert "entity_decorators" in rule["to_database_format"]
        assert "TEXT_COLOR" in rule["to_database_format"]["entity_decorators"]

    def test_disabled_via_settings(self):
        with override_settings(DRAFTAIL_TEXT_UTILS={"FEATURES": {"TEXT_COLOR": False}}):
            features = FakeFeatures()
            text_color.register(features)
            assert "text-color" not in features.default_features


class TestHighlightColorRegistration:
    def test_registers_entity_feature(self):
        features = FakeFeatures()
        highlight_color.register(features)
        assert "highlight-color-entity" in features.plugins
        assert "highlight-color-entity" in features.default_features

    def test_registers_control_plugin(self):
        features = FakeFeatures()
        highlight_color.register(features)
        assert "highlight-color" in features.plugins
        assert "highlight-color" in features.default_features

    def test_entity_handler_parses_style(self):
        handler = highlight_color.HighlightColorEntityHandler("HIGHLIGHT_COLOR")
        data = handler.get_attribute_data({"style": "background-color: #123456;"})
        assert data["backgroundColor"] == "#123456"

    def test_entity_decorator_creates_span(self):
        el = highlight_color.highlight_color_entity_decorator(
            {"backgroundColor": "#00ff00", "children": "text"}
        )
        assert el.type == "span"
        assert "background-color: #00ff00" in el.attr.get("style", "")


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
    def test_registers_entity_feature(self):
        features = FakeFeatures()
        font_size.register(features)
        assert "font-size-entity" in features.default_features
        assert "font-size-entity" in features.plugins
        plugin = features.plugins["font-size-entity"]
        assert plugin.data["type"] == "FONT_SIZE"

    def test_registers_control_plugin(self):
        features = FakeFeatures()
        font_size.register(features)
        assert "font-size" in features.plugins
        assert "font-size" in features.default_features

    def test_entity_handler_parses_style(self):
        handler = font_size.FontSizeEntityHandler("FONT_SIZE")
        data = handler.get_attribute_data({"style": "font-size: 16px;"})
        assert data["size"] == "16px"

    def test_entity_handler_parses_style_without_semicolon(self):
        handler = font_size.FontSizeEntityHandler("FONT_SIZE")
        data = handler.get_attribute_data({"style": "font-size: 16px"})
        assert data["size"] == "16px"

    def test_entity_decorator_creates_span(self):
        el = font_size.font_size_entity_decorator({"size": "16px", "children": "Hello"})
        assert el.type == "span"
        assert el.attr.get("data-entity-type") == "FONT_SIZE"
        assert "font-size: 16px;" in el.attr.get("style", "")

    def test_entity_decorator_handles_no_size(self):
        el = font_size.font_size_entity_decorator({"children": "text"})
        assert el.type == "span"
        assert el.attr.get("data-entity-type") == "FONT_SIZE"
        assert "style" not in el.attr

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
            assert "font-size-entity" in features.default_features
            assert "font-size" in features.default_features


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
            text_color.register(features)
            highlight_color.register(features)
            font_family.register(features)
            font_size.register(features)
            text_alignment.register(features)
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

    def test_text_color_entity_rule_registered(self):
        features = FakeFeatures()
        text_color.register(features)
        rule = features.converter_rules["text-color-entity"]
        assert "from_database_format" in rule
        assert "to_database_format" in rule
        assert "TEXT_COLOR" in rule["to_database_format"]["entity_decorators"]

    def test_highlight_color_entity_rule_registered(self):
        features = FakeFeatures()
        highlight_color.register(features)
        rule = features.converter_rules["highlight-color-entity"]
        assert "from_database_format" in rule
        assert "to_database_format" in rule
        assert "HIGHLIGHT_COLOR" in rule["to_database_format"]["entity_decorators"]

    def test_text_color_decorator_creates_span(self):
        el = text_color.text_color_entity_decorator(
            {"color": "#ff00ff", "children": "magic"}
        )
        assert el.type == "span"
        assert el.attr["data-entity-type"] == "TEXT_COLOR"

    def test_highlight_color_handler_parses_background_color(self):
        handler = highlight_color.HighlightColorEntityHandler("HIGHLIGHT_COLOR")
        data = handler.get_attribute_data({"style": "background-color: #abc123;"})
        assert data["backgroundColor"] == "#abc123"

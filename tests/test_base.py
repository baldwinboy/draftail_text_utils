"""Tests for the shared rich-text base utilities."""

import pytest

from wagtail.admin.rich_text.converters.html_to_contentstate import (
    InlineEntityElementHandler,
)
from wagtail.admin.rich_text.editors.draftail.features import (
    ControlFeature,
    EntityFeature,
    InlineStyleFeature,
)

from draftail_text_utils.rich_text.base import (
    register_control_feature,
    register_entity_feature,
    register_inline_style_feature,
)


pytestmark = pytest.mark.django_db


class FakeFeatures:
    """A minimal mock of the Wagtail features registry."""

    def __init__(self):
        self.plugins = {}
        self.converter_rules = {}
        self.default_features = []

    def register_editor_plugin(self, editor, feature_name, plugin):
        self.plugins[feature_name] = plugin

    def register_converter_rule(self, editor, feature_name, rule):
        self.converter_rules[feature_name] = rule


class TestRegisterInlineStyleFeature:
    def test_registers_plugin_and_rule(self):
        features = FakeFeatures()
        register_inline_style_feature(
            features,
            "TEST_STYLE",
            {"color": "red"},
            'span[style="color: red;"]',
        )

        assert "TEST_STYLE" in features.plugins
        assert isinstance(features.plugins["TEST_STYLE"], InlineStyleFeature)
        assert features.plugins["TEST_STYLE"].data["type"] == "TEST_STYLE"
        assert features.plugins["TEST_STYLE"].data["style"] == {"color": "red"}

        assert "TEST_STYLE" in features.converter_rules
        rule = features.converter_rules["TEST_STYLE"]
        assert "from_database_format" in rule
        assert "to_database_format" in rule


class TestRegisterControlFeature:
    def test_registers_control_and_appends_defaults(self):
        features = FakeFeatures()
        register_control_feature(
            features,
            "test-control",
            ["js/test.js"],
            {"all": ("css/test.css",)},
        )

        assert "test-control" in features.plugins
        assert isinstance(features.plugins["test-control"], ControlFeature)
        assert "test-control" in features.default_features


class TestRegisterEntityFeature:
    def test_registers_entity_and_appends_defaults(self):
        features = FakeFeatures()

        def decorator(props):
            from draftjs_exporter.dom import DOM

            return DOM.create_element("span", {}, props["children"])

        class FakeHandler(InlineEntityElementHandler):
            mutability = "MUTABLE"

            def get_attribute_data(self, attrs):
                return {}

        register_entity_feature(
            features,
            "test-entity",
            "TEST_ENTITY",
            ["attr"],
            decorator,
            FakeHandler,
            js=["js/test.js"],
        )

        assert "test-entity" in features.plugins
        assert isinstance(features.plugins["test-entity"], EntityFeature)
        assert "test-entity" in features.default_features
        assert (
            "TEST_ENTITY"
            in features.converter_rules["test-entity"]["to_database_format"][
                "entity_decorators"
            ]
        )

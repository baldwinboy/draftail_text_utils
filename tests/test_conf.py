"""Tests for draftail_text_utils configuration module."""

import types

from unittest.mock import MagicMock, patch

from django.test import override_settings

from draftail_text_utils.conf import (
    DEFAULT_COLORS,
    _extract_struct_from_field,
    _find_design_settings_model,
    _normalise_font_urls,
    get_font_sizes,
    get_setting,
    load_color_palette,
    load_font_families,
    load_font_families_from_module_settings,
    load_font_urls,
    load_font_urls_from_module_settings,
)


# Capture the real import_module BEFORE any patch replaces it.
_real_import_module = __import__("importlib").import_module


def _fake_import(fake_module):
    """Create a side_effect for import_module that returns fake_module
    only for the paths used in tests, and falls back to real import for
    everything else (needed so mock can resolve its own patch targets)."""

    def side_effect(name):
        if name in ("fake.path", "apps.core.models", "nonexistent"):
            return fake_module
        return _real_import_module(name)

    return side_effect


class TestDefaultConfig:
    def test_get_setting_default(self):
        assert get_setting("NONEXISTENT", "fallback") == "fallback"

    def test_get_setting_none_default(self):
        assert get_setting("NONEXISTENT") is None

    def test_get_font_sizes_defaults(self):
        sizes = get_font_sizes()
        assert sizes["MIN"] == 8
        assert sizes["MAX"] == 100
        assert sizes["STEP"] == 1
        assert 12 in sizes["PRESETS"]
        assert 96 in sizes["PRESETS"]

    def test_load_color_palette_defaults(self):
        colors = load_color_palette()
        assert len(colors) == 13
        assert colors[0]["key"] == "transparent"
        assert colors[0]["label"] == "Transparent"
        assert colors[0]["value"] == "#00000000"

    def test_load_font_families_defaults(self):
        families = load_font_families()
        assert families == []

    def test_default_colors_are_valid(self):
        for color in DEFAULT_COLORS:
            assert "key" in color
            assert "label" in color
            assert "value" in color


class TestCustomConfig:
    def test_custom_font_sizes(self):
        with override_settings(
            DRAFTAIL_TEXT_UTILS={
                "FONT_SIZES": {
                    "MIN": 10,
                    "MAX": 50,
                    "STEP": 5,
                    "PRESETS": [10, 20, 30, 40, 50],
                }
            }
        ):
            sizes = get_font_sizes()
            assert sizes["MIN"] == 10
            assert sizes["MAX"] == 50
            assert sizes["STEP"] == 5
            assert sizes["PRESETS"] == [10, 20, 30, 40, 50]

    def test_custom_color_palette(self):
        custom_colors = [
            {"key": "custom_red", "label": "Custom Red", "value": "#FF0000"},
        ]
        with override_settings(DRAFTAIL_TEXT_UTILS={"COLOR_PALETTE": custom_colors}):
            colors = load_color_palette()
            assert len(colors) == 1
            assert colors[0]["key"] == "custom_red"
            assert colors[0]["value"] == "#FF0000"

    def test_font_families_custom(self):
        custom_families = [
            {"label": "Roboto", "value": "Roboto, sans-serif"},
            {"label": "Merriweather", "value": "Merriweather, serif"},
        ]
        with override_settings(DRAFTAIL_TEXT_UTILS={"FONT_FAMILIES": custom_families}):
            families = load_font_families()
            assert len(families) == 2
            assert families[0]["label"] == "Roboto"

    def test_partial_font_sizes_config(self):
        with override_settings(DRAFTAIL_TEXT_UTILS={"FONT_SIZES": {"MIN": 1}}):
            sizes = get_font_sizes()
            assert sizes["MIN"] == 1
            assert sizes["MAX"] == 100
            assert sizes["STEP"] == 1
            assert 8 in sizes["PRESETS"]

    def test_color_palette_empty_list(self):
        with override_settings(DRAFTAIL_TEXT_UTILS={"COLOR_PALETTE": []}):
            colors = load_color_palette()
            assert colors == []


# ---------------------------------------------------------------------------
# wagtailtraverse utility tests
# ---------------------------------------------------------------------------


class TestExtractStructFromField:
    def test_none_returns_empty_dict(self):
        assert _extract_struct_from_field(None) == {}

    def test_empty_returns_empty_dict(self):
        assert _extract_struct_from_field("") == {}

    def test_plain_dict_returns_asis(self):
        assert _extract_struct_from_field({"a": 1}) == {"a": 1}

    def test_traverse_value_called_for_bound_block(self):
        mock_block = MagicMock()
        mock_block.value = {"font_family_heading": "Roboto"}
        mock_bound_block = MagicMock()
        mock_bound_block.block = True

        with patch(
            "draftail_text_utils.conf.traverse_value",
            return_value=[("", mock_bound_block)],
        ):
            mock_bound_block.value = {"font_family_heading": "Roboto"}
            result = _extract_struct_from_field([mock_block])
            assert result == {"font_family_heading": "Roboto"}

    def test_empty_list_returns_empty_dict(self):
        assert _extract_struct_from_field([]) == {}

    def test_list_of_non_blocks_returns_empty_dict(self):
        assert _extract_struct_from_field([1, 2, 3]) == {}


class TestNormaliseFontUrls:
    def test_none_returns_empty_list(self):
        assert _normalise_font_urls(None) == []

    def test_empty_string_returns_empty_list(self):
        assert _normalise_font_urls("") == []

    def test_string_wraps_in_list(self):
        assert _normalise_font_urls("https://fonts.bunny.net/css?family=roboto") == [
            "https://fonts.bunny.net/css?family=roboto"
        ]

    def test_list_passthrough(self):
        urls = [
            "https://fonts.bunny.net/css?family=roboto",
            "https://fonts.bunny.net/css?family=merriweather",
        ]
        assert _normalise_font_urls(urls) == urls


class TestFindDesignSettingsModel:
    def test_finds_site_design_settings(self):
        mock_settings = type(
            "SiteDesignSettings",
            (),
            {
                "_meta": type("Meta", (), {"label": "myapp.SiteDesignSettings"})(),
            },
        )
        fake_module = types.ModuleType("fake_module")
        fake_module.SiteDesignSettings = mock_settings

        result = _find_design_settings_model(fake_module)
        assert result is mock_settings

    def test_returns_none_when_not_found(self):
        fake_module = types.ModuleType("fake_module")
        fake_module.SomeModel = type(
            "SomeModel",
            (),
            {
                "_meta": type("Meta", (), {"label": "myapp.SomeModel"})(),
            },
        )

        result = _find_design_settings_model(fake_module)
        assert result is None


# ---------------------------------------------------------------------------
# Font family module loading
# ---------------------------------------------------------------------------


class TestFontFamilyModuleLoading:
    def test_explicit_list_returns_directly(self):
        families = [
            {"label": "Roboto", "value": "Roboto, sans-serif"},
        ]
        with override_settings(DRAFTAIL_TEXT_UTILS={"FONT_FAMILIES": families}):
            assert load_font_families() == families

    def test_dict_with_module_calls_loader(self):
        with (
            override_settings(
                DRAFTAIL_TEXT_UTILS={"FONT_FAMILIES": {"MODULE": "tests.test_conf"}}
            ),
            patch(
                "draftail_text_utils.conf.load_font_families_from_module_settings",
                return_value=[
                    {"label": "Via Module", "value": "ModuleFont, sans-serif"}
                ],
            ) as mock_loader,
        ):
            result = load_font_families()
            mock_loader.assert_called_once_with("tests.test_conf")
            assert result == [
                {"label": "Via Module", "value": "ModuleFont, sans-serif"}
            ]

    def test_dict_with_module_none_returns_empty(self):
        with override_settings(DRAFTAIL_TEXT_UTILS={"FONT_FAMILIES": {"MODULE": None}}):
            assert load_font_families() == []

    def test_load_from_module_draftail_font_families(self):
        fake_module = types.ModuleType("fake_module")
        fake_module.DRAFTAIL_FONT_FAMILIES = [
            {"label": "Fake", "value": "Fake, sans-serif"},
        ]
        with patch(
            "importlib.import_module",
            side_effect=_fake_import(fake_module),
        ):
            result = load_font_families_from_module_settings("fake.path")
            assert result == [{"label": "Fake", "value": "Fake, sans-serif"}]

    def test_load_from_module_import_error_returns_none(self):
        with patch(
            "importlib.import_module",
            side_effect=ImportError("no module"),
        ):
            assert load_font_families_from_module_settings("nonexistent") is None

    def test_load_font_families_defaults_when_unconfigured(self):
        with override_settings(DRAFTAIL_TEXT_UTILS={}):
            assert load_font_families() == []

    def test_load_from_typography_block_defaults(self):
        fake_module = types.ModuleType("fake_module")
        mock_block = type(
            "TypographyBlock",
            (),
            {
                "child_blocks": {
                    "font_family_heading": MagicMock(default="Roboto, sans-serif"),
                    "font_family_body": MagicMock(default="Merriweather, serif"),
                },
            },
        )
        fake_module.TypographyBlock = mock_block
        with patch(
            "importlib.import_module",
            side_effect=_fake_import(fake_module),
        ):
            result = load_font_families_from_module_settings("fake.path")
            assert result == [
                {"label": "Heading", "value": "Roboto, sans-serif"},
                {"label": "Body", "value": "Merriweather, serif"},
            ]

    def test_load_from_typography_instance_via_traverse(self):
        mock_settings_instance = MagicMock()
        mock_settings = type(
            "SiteDesignSettings",
            (),
            {
                "_meta": type("Meta", (), {"label": "myapp.SiteDesignSettings"})(),
                "load": classmethod(lambda cls: mock_settings_instance),
            },
        )
        fake_module = types.ModuleType("fake_module")
        fake_module.SiteDesignSettings = mock_settings
        with (
            patch(
                "importlib.import_module",
                side_effect=_fake_import(fake_module),
            ),
            patch(
                "draftail_text_utils.conf._extract_struct_from_field",
                return_value={
                    "font_family_heading": "Roboto, sans-serif",
                    "font_family_body": "Merriweather, serif",
                    "custom_fonts": [
                        {"label": "Mono", "font_family": "Fira Code, monospace"},
                    ],
                },
            ),
        ):
            result = load_font_families_from_module_settings("fake.path")
            assert result == [
                {"label": "Heading", "value": "Roboto, sans-serif"},
                {"label": "Body", "value": "Merriweather, serif"},
                {"label": "Mono", "value": "Fira Code, monospace"},
            ]


# ---------------------------------------------------------------------------
# Font URL loading
# ---------------------------------------------------------------------------


class TestFontUrlsLoading:
    def test_explicit_list_returns_directly(self):
        urls = [
            "https://fonts.bunny.net/css?family=roboto:400",
            "https://fonts.bunny.net/css?family=merriweather:400",
        ]
        with override_settings(DRAFTAIL_TEXT_UTILS={"FONT_URLS": urls}):
            assert load_font_urls() == urls

    def test_explicit_empty_list(self):
        with override_settings(DRAFTAIL_TEXT_UTILS={"FONT_URLS": []}):
            assert load_font_urls() == []

    def test_dict_with_module_calls_loader(self):
        with (
            override_settings(
                DRAFTAIL_TEXT_UTILS={"FONT_URLS": {"MODULE": "tests.test_conf"}}
            ),
            patch(
                "draftail_text_utils.conf.load_font_urls_from_module_settings",
                return_value=["https://fonts.bunny.net/css?family=opensans:400"],
            ) as mock_loader,
        ):
            result = load_font_urls()
            mock_loader.assert_called_once_with("tests.test_conf")
            assert result == ["https://fonts.bunny.net/css?family=opensans:400"]

    def test_dict_with_module_none_returns_empty(self):
        with override_settings(DRAFTAIL_TEXT_UTILS={"FONT_URLS": {"MODULE": None}}):
            assert load_font_urls() == []

    def test_load_from_module_draftail_font_urls(self):
        fake_module = types.ModuleType("fake_module")
        fake_module.DRAFTAIL_FONT_URLS = [
            "https://fonts.bunny.net/css?family=roboto:400",
        ]
        with patch(
            "importlib.import_module",
            side_effect=_fake_import(fake_module),
        ):
            result = load_font_urls_from_module_settings("fake.path")
            assert result == ["https://fonts.bunny.net/css?family=roboto:400"]

    def test_load_from_module_import_error_returns_none(self):
        with patch(
            "importlib.import_module",
            side_effect=ImportError("no module"),
        ):
            assert load_font_urls_from_module_settings("nonexistent") is None

    def test_load_font_urls_defaults_when_unconfigured(self):
        with override_settings(DRAFTAIL_TEXT_UTILS={}):
            assert load_font_urls() == []

    def test_site_design_settings_extraction_via_traverse(self):
        mock_settings_instance = MagicMock()
        mock_settings = type(
            "SiteDesignSettings",
            (),
            {
                "_meta": type("Meta", (), {"label": "myapp.SiteDesignSettings"})(),
                "load": classmethod(lambda cls: mock_settings_instance),
            },
        )
        fake_module = types.ModuleType("fake_module")
        fake_module.SiteDesignSettings = mock_settings
        with (
            patch(
                "importlib.import_module",
                side_effect=_fake_import(fake_module),
            ),
            patch(
                "draftail_text_utils.conf._extract_struct_from_field",
                return_value={
                    "font_url": "https://fonts.bunny.net/css?family=roboto:400",
                    "custom_fonts": [
                        {
                            "label": "Mono",
                            "font_family": "Fira Code, monospace",
                            "font_url": "https://fonts.bunny.net/css?family=fira:400",
                        },
                    ],
                },
            ),
        ):
            result = load_font_urls_from_module_settings("fake.path")
            assert result == [
                "https://fonts.bunny.net/css?family=roboto:400",
                "https://fonts.bunny.net/css?family=fira:400",
            ]


# ---------------------------------------------------------------------------
# Color palette module loading
# ---------------------------------------------------------------------------


class TestColorPaletteModuleLoading:
    def test_load_from_draftail_colors_list(self):
        fake_module = types.ModuleType("fake_module")
        fake_module.DRAFTAIL_COLORS = [
            {"key": "primary", "label": "Primary", "value": "#7C3AED"},
        ]
        with (
            patch(
                "importlib.import_module",
                side_effect=_fake_import(fake_module),
            ),
            override_settings(
                DRAFTAIL_TEXT_UTILS={
                    "COLORS": {"MODULE": "apps.core.models"},
                }
            ),
        ):
            result = load_color_palette()
            assert result == [
                {"key": "primary", "label": "Primary", "value": "#7C3AED"}
            ]

    def test_load_from_light_mode_default_colors(self):
        fake_module = types.ModuleType("fake_module")
        fake_module.LIGHT_MODE_DEFAULT_COLORS = {
            "primary": "#7C3AED",
            "secondary": "#EC4899",
        }
        with (
            patch(
                "importlib.import_module",
                side_effect=_fake_import(fake_module),
            ),
            override_settings(
                DRAFTAIL_TEXT_UTILS={
                    "COLORS": {"MODULE": "apps.core.models"},
                }
            ),
        ):
            result = load_color_palette()
            assert result == [
                {"key": "primary", "label": "Primary", "value": "#7C3AED"},
                {"key": "secondary", "label": "Secondary", "value": "#EC4899"},
            ]

    def test_load_from_site_design_settings_via_traverse(self):
        mock_settings_instance = MagicMock()
        mock_settings = type(
            "SiteDesignSettings",
            (),
            {
                "_meta": type("Meta", (), {"label": "myapp.SiteDesignSettings"})(),
                "load": classmethod(lambda cls: mock_settings_instance),
            },
        )
        fake_module = types.ModuleType("fake_module")
        fake_module.SiteDesignSettings = mock_settings
        with (
            patch(
                "importlib.import_module",
                side_effect=_fake_import(fake_module),
            ),
            patch(
                "draftail_text_utils.conf._extract_struct_from_field",
                return_value={
                    "light": {
                        "primary": "#7C3AED",
                        "secondary": "#EC4899",
                    },
                },
            ),
            override_settings(
                DRAFTAIL_TEXT_UTILS={
                    "COLORS": {"MODULE": "apps.core.models"},
                }
            ),
        ):
            result = load_color_palette()
            assert result == [
                {"key": "primary", "label": "Primary", "value": "#7C3AED"},
                {"key": "secondary", "label": "Secondary", "value": "#EC4899"},
            ]

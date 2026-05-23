"""
Configuration for draftail_text_utils via Django settings.

Usage in your Django settings:

    DRAFTAIL_TEXT_UTILS = {
        # ---- Font size ----
        "FONT_SIZES": {
            "MIN": 8,
            "MAX": 100,
            "STEP": 1,
            "PRESETS": [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72, 96],
        },
        # ---- Color palette ----
        # Option A: point to an existing module with a DRAFTAIL_COLORS list
        "COLORS": {
            "MODULE": None,  # e.g. "apps.core.models"
        },
        # Option B: provide an explicit palette (ignored if MODULE is set)
        "COLOR_PALETTE": None,  # falls back to built-in defaults
        # ---- Font families ----
        # Option A: point to an existing module with a DRAFTAIL_FONT_FAMILIES list
        #   or a SiteDesignSettings / TypographyBlock with font definitions.
        "FONT_FAMILIES": {
            "MODULE": None,  # e.g. "apps.core.models"
        },
        # Option B: provide an explicit list (ignored if MODULE is set):
        #   [{"label": "Roboto", "value": "'Roboto', sans-serif"}, ...]
        # ---- Font URL stylesheets ----
        # Option A: point to an existing module with a DRAFTAIL_FONT_URLS list,
        #   or a TypographyBlock / SiteDesignSettings with a font_url field.
        "FONT_URLS": {
            "MODULE": None,  # e.g. "apps.core.models"
        },
        # Option B: provide an explicit list of CSS URLs:
        #   ["https://fonts.bunny.net/css?family=...", ...]
        # ---- Feature toggles ----
        "FEATURES": {
            "TEXT_COLOR": True,
            "HIGHLIGHT_COLOR": True,
            "FONT_FAMILY": True,
            "FONT_SIZE": True,
            "TEXT_ALIGNMENT": True,
        },
    }
"""

import importlib
import logging

from django.conf import settings
from wagtailtraverse import traverse_value


logger = logging.getLogger(__name__)


DEFAULT_FONT_SIZES = {
    "MIN": 8,
    "MAX": 100,
    "STEP": 1,
    "PRESETS": [8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72, 96],
}

DEFAULT_COLORS = [
    {"key": "transparent", "label": "Transparent", "value": "#00000000"},
    {"key": "black", "label": "Black", "value": "#000000"},
    {"key": "white", "label": "White", "value": "#FFFFFF"},
    {"key": "gray", "label": "Gray", "value": "#6B7280"},
    {"key": "red", "label": "Red", "value": "#EF4444"},
    {"key": "orange", "label": "Orange", "value": "#F97316"},
    {"key": "yellow", "label": "Yellow", "value": "#EAB308"},
    {"key": "green", "label": "Green", "value": "#22C55E"},
    {"key": "teal", "label": "Teal", "value": "#14B8A6"},
    {"key": "blue", "label": "Blue", "value": "#3B82F6"},
    {"key": "indigo", "label": "Indigo", "value": "#6366F1"},
    {"key": "purple", "label": "Purple", "value": "#A855F7"},
    {"key": "pink", "label": "Pink", "value": "#EC4899"},
]

DEFAULT_FEATURES = {
    "TEXT_COLOR": True,
    "HIGHLIGHT_COLOR": True,
    "FONT_FAMILY": True,
    "FONT_SIZE": True,
    "TEXT_ALIGNMENT": True,
}


def _user_settings():
    return getattr(settings, "DRAFTAIL_TEXT_UTILS", {})


def _deep_merge(default, override):
    result = default.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


FULL_DEFAULTS = {
    "FONT_SIZES": DEFAULT_FONT_SIZES,
    "COLORS": {},
    "COLOR_PALETTE": None,
    "FONT_FAMILIES": None,
    "FONT_URLS": None,
    "FEATURES": DEFAULT_FEATURES,
}


def _merged_config():
    user = _user_settings()
    return _deep_merge(FULL_DEFAULTS.copy(), user)


def get_setting(key, default=None):
    config = _merged_config()
    return config.get(key, default)


def get_font_sizes():
    return get_setting("FONT_SIZES", DEFAULT_FONT_SIZES)


def get_font_size_presets():
    sizes = get_font_sizes()
    return sizes.get("PRESETS", DEFAULT_FONT_SIZES["PRESETS"])


def get_feature_toggles():
    return get_setting("FEATURES", DEFAULT_FEATURES)


def feature_enabled(name):
    return get_feature_toggles().get(name, True)


# ---------------------------------------------------------------------------
# wagtailtraverse-based extraction utilities
# ---------------------------------------------------------------------------


def _extract_struct_from_field(field_value):
    """
    Extract a plain dict from a Wagtail StreamValue / BoundBlock / StructValue,
    or return the value itself if it is already a dict/list.
    Returns an empty dict if extraction fails.
    """
    if not field_value:
        return {}

    if isinstance(field_value, dict):
        return field_value

    if isinstance(field_value, list):
        if field_value and hasattr(field_value[0], "block"):
            for _path, bound_block in traverse_value(field_value):
                return bound_block.value or {}
        return {}

    try:
        for _path, bound_block in traverse_value(field_value):
            return bound_block.value or {}
    except Exception:
        logger.exception("Failed to extract struct from field %s", field_value)

    return {}


def _find_design_settings_model(module):
    """Find a SiteDesignSettings-style model class in a module."""
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and hasattr(attr, "_meta"):
            try:
                if attr._meta.label and "SiteDesignSettings" in attr.__name__:
                    return attr
            except (AttributeError, KeyError):
                continue
    return None


def _find_typography_block(module):
    """Find a TypographyBlock / TypographyStreamBlock class in a module."""
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and "Typography" in getattr(attr, "__name__", ""):
            return attr
    return None


def _normalise_font_urls(font_urls):
    """Normalise font_urls to a list, handling string or single value input."""
    if not font_urls:
        return []
    if isinstance(font_urls, str):
        return [font_urls]
    return list(font_urls)


# ---------------------------------------------------------------------------
# Color palette loading
# ---------------------------------------------------------------------------


def load_color_palette():
    colors_config = get_setting("COLORS", {})
    module_path = colors_config.get("MODULE")

    if module_path:
        try:
            module = importlib.import_module(module_path)
            if hasattr(module, "DRAFTAIL_COLORS"):
                return module.DRAFTAIL_COLORS
            if hasattr(module, "COLOR_PALETTE"):
                raw = module.COLOR_PALETTE
                if isinstance(raw, dict):
                    return [
                        {"key": k, "label": k.replace("_", " ").title(), "value": v}
                        for k, v in raw.items()
                    ]
                return raw
        except (ImportError, AttributeError):
            pass

        result = load_colors_from_module_settings(module_path)
        if result is not None:
            return result

    explicit = get_setting("COLOR_PALETTE")
    if explicit is not None:
        return explicit

    return DEFAULT_COLORS


def load_colors_from_module_settings(module_path):
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return None

    palette = getattr(module, "LIGHT_MODE_DEFAULT_COLORS", None)
    if palette and isinstance(palette, dict):
        return [
            {"key": k, "label": k.replace("_", " ").title(), "value": v}
            for k, v in palette.items()
        ]

    model_class = _find_design_settings_model(module)
    if model_class:
        try:
            instance = model_class.load()
            cp_struct = _extract_struct_from_field(instance.color_palette)
            light = cp_struct.get("light", {})
            if light:
                return [
                    {"key": k, "label": k.replace("_", " ").title(), "value": v}
                    for k, v in light.items()
                ]
        except Exception:
            logger.warning(
                "Failed to load colours from module %s", module_path, exc_info=True
            )

    return None


# ---------------------------------------------------------------------------
# Font family loading
# ---------------------------------------------------------------------------


def load_font_families():
    value = get_setting("FONT_FAMILIES")

    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        module_path = value.get("MODULE")
        if module_path:
            result = load_font_families_from_module_settings(module_path)
            if result is not None:
                return result

    return []


def load_font_families_from_module_settings(module_path):
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return None

    if hasattr(module, "DRAFTAIL_FONT_FAMILIES"):
        return module.DRAFTAIL_FONT_FAMILIES

    typography_block = _find_typography_block(module)
    if typography_block:
        families = _extract_font_families_from_typography_block(typography_block)
        if families:
            return families

    model_class = _find_design_settings_model(module)
    if model_class:
        try:
            instance = model_class.load()
            families = _extract_font_families_from_typography_instance(instance)
            if families:
                return families
        except Exception:
            logger.warning(
                "Failed to load font families from module %s",
                module_path,
                exc_info=True,
            )

    return None


def _extract_font_families_from_typography_block(typography_block):
    families = []

    child_blocks = getattr(typography_block, "child_blocks", None)
    if child_blocks is None:
        child_blocks = {}
        try:
            child_blocks = {f.name: f for f in typography_block.base_blocks.items()}
        except (AttributeError, TypeError):
            pass

    for field_name in (
        "font_family_heading",
        "font_family_subheading",
        "font_family_body",
    ):
        block = child_blocks.get(field_name)
        if block is not None:
            default = getattr(block, "default", None)
            if default:
                label = field_name.replace("font_family_", "").replace("_", " ").title()
                families.append({"label": label, "value": str(default)})

    custom_block = child_blocks.get("custom_fonts")
    if custom_block is not None:
        default_list = getattr(custom_block, "default", None)
        if default_list:
            for cf in default_list:
                families.append(
                    {
                        "label": cf.get("label", cf.get("font_family", "")),
                        "value": cf.get("font_family", ""),
                    }
                )

    return families or None


def _extract_font_families_from_typography_instance(instance):
    tp_struct = _extract_struct_from_field(instance.typography)
    if not tp_struct:
        return None

    families = []
    for key in (
        "font_family_heading",
        "font_family_subheading",
        "font_family_body",
    ):
        value = tp_struct.get(key)
        if value:
            label = key.replace("font_family_", "").replace("_", " ").title()
            families.append({"label": label, "value": value})

    custom_fonts = tp_struct.get("custom_fonts", [])
    for cf in custom_fonts:
        families.append(
            {
                "label": cf.get("label", cf.get("font_family", "")),
                "value": cf.get("font_family", ""),
            }
        )

    return families or None


# ---------------------------------------------------------------------------
# Font URL loading
# ---------------------------------------------------------------------------


def load_font_urls():
    value = get_setting("FONT_URLS")

    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        module_path = value.get("MODULE")
        if module_path:
            result = load_font_urls_from_module_settings(module_path)
            if result is not None:
                return result

    return []


def load_font_urls_from_module_settings(module_path):
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return None

    if hasattr(module, "DRAFTAIL_FONT_URLS"):
        return module.DRAFTAIL_FONT_URLS

    typography_block = _find_typography_block(module)
    if typography_block:
        urls = _extract_font_urls_from_typography_block(typography_block)
        if urls:
            return urls

    model_class = _find_design_settings_model(module)
    if model_class:
        try:
            instance = model_class.load()
            tp_struct = _extract_struct_from_field(instance.typography)
            if tp_struct:
                urls = _normalise_font_urls(tp_struct.get("font_url", []))
                custom_fonts = tp_struct.get("custom_fonts", [])
                for cf in custom_fonts:
                    url = cf.get("font_url")
                    if url:
                        urls.append(url)
                if urls:
                    return urls
        except Exception:
            logger.warning(
                "Failed to load font URLs from module %s",
                module_path,
                exc_info=True,
            )

    return None


def _extract_font_urls_from_typography_block(typography_block):
    child_blocks = getattr(typography_block, "child_blocks", None)
    if child_blocks is None:
        try:
            child_blocks = {f.name: f for f in typography_block.base_blocks.items()}
        except (AttributeError, TypeError):
            child_blocks = {}

    urls = []
    for field_name in (
        "font_url",
        "google_fonts_url",
        "font_url_heading",
        "font_url_body",
        "font_url_subheading",
    ):
        block = child_blocks.get(field_name)
        if block is not None:
            default = getattr(block, "default", None)
            if default:
                urls.append(str(default))

    custom_block = child_blocks.get("custom_fonts")
    if custom_block is not None:
        default_list = getattr(custom_block, "default", None)
        if default_list:
            for cf in default_list:
                url = cf.get("font_url")
                if url:
                    urls.append(url)

    return list(dict.fromkeys(urls)) if urls else None

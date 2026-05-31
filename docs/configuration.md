# Configuration Guide

`draftail_text_utils` is configured via a single Django setting:

```python
DRAFTAIL_TEXT_UTILS = {
    # ---- Font sizes ----
    "FONT_SIZES": {
        "MIN": 8,  # Minimum font size (inclusive)
        "MAX": 100,  # Maximum font size (inclusive)
        "STEP": 1,  # Granularity / step between consecutive sizes
        "PRESETS": [8, 9, 10, 11, 12, 14, 16, 18, 24, 30, 36, 48, 60, 72, 96],
    },

    # ---- Colour palette ----
    # Option A: point to any module that exposes colour data
    "COLORS": {
        "MODULE": None,  # e.g. "apps.core.models"
    },
    # Option B: provide an explicit palette list (ignored if MODULE is set)
    "COLOR_PALETTE": None,  # falls back to the built-in 13-colour palette

    # ---- Font families ----
    "FONT_FAMILIES": None,  # list of {"label": str, "value": str}
    "FONT_URLS": None, # list of str

    # ---- Feature toggles ----
    "FEATURES": {
        "TEXT_COLOR": True,
        "HIGHLIGHT_COLOR": True,
        "FONT_FAMILY": True,
        "FONT_SIZE": True,
        "TEXT_ALIGNMENT": True,
    },
}
```

---

## Font sizes

`FONT_SIZES` controls the range of sizes that the rich-text editor
understands round-trip.  Every integer in `range(MIN, MAX+1, STEP)` is
registered as a separate `InlineStyleFeature` so that any arbitrary size
can round-trip through the database.

`PRESETS` controls which convenience options appear in the toolbar
dropdown for quick selection.

```python
DRAFTAIL_TEXT_UTILS = {
    "FONT_SIZES": {
        "MIN": 1,
        "MAX": 200,
        "STEP": 1,
        "PRESETS": [8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 42, 48, 60, 72, 96, 120, 144],
    },
}
```

> **Note on performance**: each integer in the range creates a separate
> Draftail inline style.  Keeping `MAX - MIN` reasonable (≤400) avoids
> excessive memory use in the editor.

---

## Colour palette

### Option A — reference an existing module (recommended)

If your project already defines colours — for example in a
`SiteDesignSettings` model — you can point to that module.  The loader
tries the following sources in order:

1. A `DRAFTAIL_COLORS` list on the module (each entry: `{"key": ...,
   "label": ..., "value": ...}`).
2. A `COLOR_PALETTE` dict (keys → hex values).  Keys are converted to
   title-cased labels automatically.
3. A `LIGHT_MODE_DEFAULT_COLORS` dict (keys → hex values).
4. An active `SiteDesignSettings` model with a `color_palette`
   `StreamField` containing `ColorSchemesBlock`.

```python
DRAFTAIL_TEXT_UTILS = {
    "COLORS": {
        "MODULE": "apps.core.models",  # your existing colour definitions live here
    },
}
```

### Option B — explicit palette

Pass a list of colour dicts directly:

```python
DRAFTAIL_TEXT_UTILS = {
    "COLOR_PALETTE": [
        {"key": "brand_primary", "label": "Brand Primary", "value": "#7C3AED"},
        {"key": "brand_secondary", "label": "Brand Secondary", "value": "#EC4899"},
        {"key": "brand_accent", "label": "Brand Accent", "value": "#F59E0B"},
    ],
}
```

### Option C — nothing (built-in defaults)

When neither `COLORS.MODULE` nor `COLOR_PALETTE` is set, the package uses
a built-in palette of 13 common colours including `transparent`, `black`,
`white`, `gray`, `red`, `orange`, `yellow`, `green`, `teal`, `blue`,
`indigo`, `purple`, and `pink`.

---

## Font families

Ensure font family files are loaded via CDN or CSS in your templates,
then configure the font families at build time or runtime.

### Option A — Runtime Configuration (recommended)

If your project already defines font families — for example in a
`SiteDesignSettings` model with a `TypographyBlock` or a `TypographyStreamBlock` —
you can point to that module.  The loader tries the following sources in order:

1. A `DRAFTAIL_FONT_FAMILIES` list on the module (each entry: `{"label": ...,
   "value": ...}`).
2. A `TypographyBlock` / `TypographyStreamBlock` class with
   `font_family_heading`, `font_family_body`, `font_family_subheading`,
   and `custom_fonts` fields.
3. An active `SiteDesignSettings` model with a `typography` `StreamField`.

```python
DRAFTAIL_TEXT_UTILS = {
    "FONT_FAMILIES": {
        "MODULE": "neuromancers_network.common.blocks.base",
    },
}
```

### Option B — Buildtime configuration

Provide the font families that editors should be able to apply directly:

```python
DRAFTAIL_TEXT_UTILS = {
    "FONT_FAMILIES": [
        {"label": "Roboto", "value": "'Roboto', sans-serif"},
        {"label": "Open Sans", "value": "'Open Sans', sans-serif"},
        {"label": "Merriweather", "value": "'Merriweather', serif"},
    ],
}
```

When no font families are configured (`None` or `{"MODULE": None}`), the
font-family toolbar control is hidden.

---

## Font URL stylesheets

`FONT_URLS` controls which CSS stylesheet `<link>` tags are injected into the
Wagtail admin and rendered by the `{% draftail_text_assets %}` template tag on the front end.

### Option A — Runtime Configuration (recommended)

If your project already defines font URLs — for example in a
`SiteDesignSettings` model with a `TypographyBlock` — point to that module.
The loader tries the following sources in order:

1. A `DRAFTAIL_FONT_URLS` list on the module (each entry is a URL string).
2. A `TypographyBlock` / `TypographyStreamBlock` class with `font_url`,
   `google_fonts_url`, `font_url_heading`, `font_url_body`,
   `font_url_subheading` fields, or `custom_fonts` entries with a `font_url` key.
3. An active `SiteDesignSettings` model with a `typography` `StreamField`
   containing custom fonts that have a `font_url` field.

```python
DRAFTAIL_TEXT_UTILS = {
    "FONT_URLS": {
        "MODULE": "apps.core.models",
    },
}
```

### Option B — Buildtime configuration

Provide a list of CSS URL strings directly:

```python
DRAFTAIL_TEXT_UTILS = {
    "FONT_URLS": [
        "https://fonts.bunny.net/css?family=roboto:400",
        "https://fonts.bunny.net/css?family=merriweather:400",
    ],
}
```

### Option C — Nothing (no font URLs loaded)

When `FONT_URLS` is unset (or `{"MODULE": None}`), no font stylesheets are
loaded.

### Using the `{% draftail_text_assets %}` template tag

For front-end templates, load the configured font URLs with the template tag:

```django
{% load draftail_text_utils_tags %}
{% draftail_text_assets %}
```

This renders `<link rel="stylesheet" href="...">` tags for every configured
URL, identical to the admin injection behaviour.

---

## Feature toggles

Each feature can be enabled or disabled independently:

```python
DRAFTAIL_TEXT_UTILS = {
    "FEATURES": {
        "TEXT_COLOR": True,
        "HIGHLIGHT_COLOR": False,   # disable highlight
        "FONT_FAMILY": True,
        "FONT_SIZE": True,
        "TEXT_ALIGNMENT": False,    # disable alignment
    },
}
```

When a feature is disabled, its assets (JS, CSS) are not injected into
the admin, and its Draftail plugins are not registered.

---

## Wiring up to a RichTextField / RichTextBlock

The features are registered as Wagtail "default features", meaning they
are automatically available on any `RichTextField` or `RichTextBlock`
that uses the default feature set.

If you use a restricted feature set, make sure to include the desired
feature names:

```python
from wagtail import blocks
from wagtail.fields import RichTextField

body = RichTextField(features=[
    "bold", "italic", "h2", "h3",
    # draftail_text_utils features:
    "styled-link",
    "text-color",
    "highlight-color",
    "font-family",
    "font-size",
    "text-alignment",
])
```

---

## Colours from an existing `SiteDesignSettings` model

If you already have a `SiteDesignSettings` with a `ColorSchemesBlock`
stream field (as shown in the task description), the module loader will
extract the **light** colour scheme automatically:

```python
DRAFTAIL_TEXT_UTILS = {
    "COLORS": {
        "MODULE": "apps.core.models",
    },
}
```

The loader looks for an active `SiteDesignSettings` instance, iterates
its `color_palette` stream field, and reads the `light` scheme's colours.

You can also define a minimal `DRAFTAIL_COLORS` list on any module:

```python
# apps/core/color_palette.py
DRAFTAIL_COLORS = [
    {"key": "primary", "label": "Primary", "value": "#7C3AED"},
    {"key": "secondary", "label": "Secondary", "value": "#EC4899"},
]
```

---

## How the module loader works (wagtailtraverse)

Internally, the `COLORS`, `FONT_FAMILIES`, and `FONT_URLS` module loaders use
[wagtailtraverse](https://pypi.org/project/wagtail-traverse/) to robustly
extract data from Wagtail's StreamField / StructBlock structures.

The core utility is `_extract_struct_from_field()`, which handles all of the
following without brittle `block.value` / `StreamField` iteration:

- **Plain dicts** — returned as-is.
- **StreamValue / BoundBlock / StructValue** — recursively traversed via
  `traverse_value()` to yield the underlying struct.
- **Empty / None** — safe fallback to `{}`.

This eliminates the fragile `dir()` + `child_blocks` introspection and
direct `block.value` access patterns, replacing them with a single,
`wagtailtraverse`-powered function.

### Simple example — module with lists

Create a module that exports named lists, then point to it:

```python
# apps/example/fonts.py
DRAFTAIL_FONT_FAMILIES = [
    {"label": "Inter", "value": "Inter, sans-serif"},
    {"label": "Merriweather", "value": "Merriweather, serif"},
]

DRAFTAIL_FONT_URLS = [
    "https://fonts.bunny.net/css?family=inter:400,700&display=swap",
    "https://fonts.bunny.net/css?family=merriweather:400,700&display=swap",
]

DRAFTAIL_COLORS = [
    {"key": "brand", "label": "Brand", "value": "#7C3AED"},
]
```

```python
DRAFTAIL_TEXT_UTILS = {
    "FONT_FAMILIES": {"MODULE": "apps.example.fonts"},
    "FONT_URLS": {"MODULE": "apps.example.fonts"},
    "COLORS": {"MODULE": "apps.example.fonts"},
}
```

### Advanced example — Neuromancers Network (SiteDesignSettings)

For projects with a `SiteDesignSettings` singleton model that stores
typography and colour schemes in StreamFields, the loader extracts data
using `_extract_struct_from_field()` + `traverse_value`:

```python
# apps/core/models.py
from wagtail.models import SiteManager
from wagtail.fields import StreamField
from wagtail.admin.panels import FieldPanel


class SiteDesignSettings(models.Model):
    site = models.OneToOneField(Site, on_delete=models.CASCADE)
    color_palette = StreamField([("color_schemes", ColorSchemesBlock())], blank=True)
    typography = StreamField([("typography", TypographyBlock())], blank=True)

    panels = [FieldPanel("color_palette"), FieldPanel("typography")]

    @classmethod
    def load(cls):
        return cls.objects.first() or cls()
```

The loader calls `_extract_struct_from_field()` on the `color_palette` /
`typography` fields, which safely traverses the StreamField hierarchy
regardless of nesting depth:

```python
# Internally, this is what happens:
from wagtailtraverse import traverse_value


def _extract_struct_from_field(field_value):
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
        return {}


# Usage:
cp_struct = _extract_struct_from_field(instance.color_palette)
light = cp_struct.get("light", {})  # -> {"primary": "#7C3AED", ...}

tp_struct = _extract_struct_from_field(instance.typography)
heading = tp_struct.get("font_family_heading", "Inter, sans-serif")
font_urls = tp_struct.get("font_url", [])
custom_fonts = tp_struct.get("custom_fonts", [])
```

This approach works with any StreamField layout and avoids manual
iteration over block lists or direct `.value` access.

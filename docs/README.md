# draftail-text-utils

Extends Wagtail's Draftail rich text editor with:

- **Styled links** — links that preserve text colour, highlight, and font size on save.
- **Text colour** — apply predefined or custom colours to selected text.
- **Highlight colour** — apply background / highlight colours.
- **Font family** — apply a custom font family to selected text.
- **Font size** — apply exact or preset font sizes.
- **Text alignment** — left, centre, right, or justify alignment.

## Quick start

```python
# 1. Install
pip install draftail-text-utils

# 2. Add to INSTALLED_APPS
INSTALLED_APPS = [
    ...
    "draftail_text_utils",
    ...
]

# 3. (Optional) configure colours, sizes, fonts
DRAFTAIL_TEXT_UTILS = {
    "FONT_SIZES": {
        "MIN": 8,
        "MAX": 72,
        "STEP": 1,
        "PRESETS": [8, 9, 10, 11, 12, 14, 16, 18, 24, 30, 36, 48, 60, 72],
    },
    "COLOR_PALETTE": [
        {"key": "primary", "label": "Primary", "value": "#7C3AED"},
        {"key": "secondary", "label": "Secondary", "value": "#EC4899"},
    ],
    "FONT_FAMILIES": [
        {"label": "Roboto", "value": "'Roboto', sans-serif"},
    ],
}

# 4. Use in RichTextField (all features are auto-enabled)
body = RichTextField()

# Or with selective features:
body = RichTextField(features=[
    "bold", "italic",
    "styled-link",
    "text-color",
    "font-family", "font-size",
])
```

## Architecture

```
src/draftail_text_utils/
├── __init__.py
├── apps.py              # AppConfig
├── conf.py              # Django settings → Python config
├── wagtail_hooks.py     # Main integration: feature registration + asset injection
├── rich_text/
│   ├── __init__.py
│   ├── base.py          # Shared feature registration helpers
│   ├── text_color.py
│   ├── highlight_color.py
│   ├── font_family.py
│   ├── font_size.py
│   └── text_alignment.py
├── static/
│   └── draftail_text_utils/
│       ├── js/          # 7 JS control/entity plugins
│       └── css/         # 5 CSS files
├── templates/
└── test/
```

## Feature reference

| Feature name | Type | JS plugin | CSS file | Description |
|---|---|---|---|---|
| `text-style-entity` | Entity | `text_style_entity.js` + `styled_link_source.js` + `common.js` | - | Unified entity for text colour, highlight, font size, AND styled links with tooltip (Edit/Remove) |
| `text-color` | Control (TEXT_STYLE entity) | `text_color.js` + `common.js` | `text_color.css` | Apply/remove text colour |
| `highlight-color` | Control (TEXT_STYLE entity) | `highlight_color.js` + `common.js` | `highlight_color.css` | Apply/remove highlight colour |
| `font-family` | InlineStyle + Control | `font_family.js` | `font_family.css` | Font family dropdown |
| `font-size` | InlineStyle + Control | `font_size.js` | `font_size.css` | Size input + presets |
| `text-alignment` | InlineStyle + Control | `text_alignment.js` | `text_alignment.css` | Alignment button group |

## Configuration

See [configuration.md](configuration.md) for the full reference.

## Changelog

See [CHANGELOG.md](../CHANGELOG.md).

## Development

```bash
# Install
uv sync --dev
npm ci

# Run tests
uv run pytest

# Lint
just lint

# Run demo site
just demo
```

## License

BSD-3-Clause

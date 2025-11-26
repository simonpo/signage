# HTML/CSS Templates

Modern HTML/CSS templates for rendering signage content using Jinja2.

## Template Structure

### Base Template
- **base.html**: Foundation template with 3840x2160 viewport, safe zones, and CSS utilities

### Layout Templates
Replicate the behavior of `text_layouts.py` layouts:

- **centered_layout.html**: Centered text with 220px line spacing
- **left_aligned_layout.html**: Left-aligned text with 150px spacing and indentation support
- **grid_layout.html**: Compact grid layout with 100px spacing for tabular data
- **split_layout.html**: Text on left half, reserved space for map/image on right
- **weather_layout.html**: Custom weather layout with mixed font sizes

### Specialized Templates
- **weather_cards.html**: Modern card-based weather dashboard with CSS Grid

## Safe Zones

All templates respect 5% safe margins:
- Horizontal: 192px (5% of 3840px)
- Vertical: 108px (5% of 2160px)
- Safe area: 3456x1944px

## Font Sizes

Matching PIL renderer font sizes:
- Title: 200px
- Body: 120px
- Small: 80px

## Usage

```python
from src.utils.template_renderer import TemplateRenderer

renderer = TemplateRenderer()

# Render text layout
html = renderer.render_layout('centered', lines=['Line 1', 'Line 2'])

# Render weather cards
html = renderer.render_weather_cards(weather_data)

# Save HTML
renderer.save_html(html, Path('output.html'))
```

## Converting to Images

HTML templates can be converted to PNG images using:
- Playwright (headless browser)
- Selenium WebDriver
- wkhtmltoimage
- Chrome/Chromium headless mode

The next phase will implement HTML-to-image conversion using Playwright.

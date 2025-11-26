"""
HTML template renderer using Jinja2.
Provides utilities for rendering HTML templates to images via headless browser.
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config import Config

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Renders Jinja2 HTML templates with context data.
    Templates are located in src/templates/ directory.
    """
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template renderer.
        
        Args:
            templates_dir: Path to templates directory (defaults to src/templates)
        """
        if templates_dir is None:
            templates_dir = Config.BASE_DIR / "src" / "templates"
        
        self.templates_dir = templates_dir
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self._register_filters()
        
        logger.debug(f"TemplateRenderer initialized with templates from {templates_dir}")
    
    def _register_filters(self):
        """Register custom Jinja2 filters."""
        
        @self.env.filter('enumerate')
        def do_enumerate(iterable, start=0):
            """Enumerate filter for Jinja2."""
            return enumerate(iterable, start)
        
        # Add wind direction compass filter
        @self.env.filter('compass')
        def wind_direction_compass(degrees):
            """Convert wind direction degrees to compass direction."""
            if degrees is None:
                return "N"
            
            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                         "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            index = round(degrees / 22.5) % 16
            return directions[index]
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render template with context data.
        
        Args:
            template_name: Name of template file (e.g., "centered_layout.html")
            context: Dictionary of context variables for template
        
        Returns:
            Rendered HTML string
        
        Raises:
            TemplateNotFound: If template file doesn't exist
            TemplateSyntaxError: If template has syntax errors
        """
        try:
            template = self.env.get_template(template_name)
            html = template.render(**context)
            
            logger.debug(f"Rendered template: {template_name}")
            return html
            
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}", exc_info=True)
            raise
    
    def render_layout(
        self,
        layout_type: str,
        lines: list,
        **kwargs
    ) -> str:
        """
        Render a text layout template.
        
        Args:
            layout_type: Layout type (centered, left, grid, split, weather)
            lines: List of text lines to render
            **kwargs: Additional context variables
        
        Returns:
            Rendered HTML string
        """
        template_name = f"{layout_type}_layout.html"
        context = {
            'lines': lines,
            **kwargs
        }
        
        return self.render(template_name, context)
    
    def render_weather_cards(self, weather_data: Any) -> str:
        """
        Render weather cards template.
        
        Args:
            weather_data: AmbientWeatherData object
        
        Returns:
            Rendered HTML string
        """
        # Calculate wind direction compass
        wind_direction = self._wind_direction_to_compass(weather_data.winddir)
        
        context = {
            'weather': weather_data,
            'wind_direction': wind_direction
        }
        
        return self.render('weather_cards.html', context)
    
    def _wind_direction_to_compass(self, degrees: Optional[int]) -> str:
        """Convert wind direction degrees to compass direction."""
        if degrees is None:
            return "N"
        
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def save_html(self, html: str, output_path: Path) -> None:
        """
        Save rendered HTML to file.
        
        Args:
            html: Rendered HTML string
            output_path: Path to save HTML file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Saved HTML to {output_path}")

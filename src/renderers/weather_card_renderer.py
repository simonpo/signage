"""
Modern card-based weather renderer inspired by dark mode weather dashboards.
Creates a visual layout with information cards instead of plain text.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from src.config import Config
from src.models.signage_data import AmbientWeatherData

logger = logging.getLogger(__name__)


class WeatherCardRenderer:
    """
    Renders weather data in a modern card-based layout.
    Left side: Main weather info with large temperature
    Right side: Data cards (pressure, UV, wind, rain)
    """
    
    # Layout constants
    CARD_BG_COLOR = (40, 40, 55, 220)  # Semi-transparent dark purple
    TEXT_COLOR = (255, 255, 255)
    SECONDARY_TEXT_COLOR = (180, 180, 200)
    ACCENT_COLOR = (100, 150, 255)
    
    def __init__(self):
        """Initialize renderer with fonts."""
        # Load fonts with various sizes
        try:
            self.font_huge = ImageFont.truetype(Config.FONT_PATH, 280)
            self.font_large = ImageFont.truetype(Config.FONT_PATH, 140)
            self.font_medium = ImageFont.truetype(Config.FONT_PATH, 90)
            self.font_normal = ImageFont.truetype(Config.FONT_PATH, 70)
            self.font_small = ImageFont.truetype(Config.FONT_PATH, 50)
            self.font_tiny = ImageFont.truetype(Config.FONT_PATH, 40)
        except Exception as e:
            logger.error(f"Failed to load fonts: {e}")
            raise
    
    def render(
        self,
        weather: AmbientWeatherData,
        background: Image.Image
    ) -> Image.Image:
        """
        Render weather data on background image.
        
        Args:
            weather: Weather data to render
            background: Background image (3840x2160)
        
        Returns:
            Rendered image
        """
        # Create working image
        img = background.copy()
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Split layout: left (main weather), right (cards)
        split_x = Config.IMAGE_WIDTH // 2
        
        # Render left side - main weather
        self._render_main_weather(draw, weather, 0, 0, split_x)
        
        # Render right side - data cards
        self._render_data_cards(draw, weather, split_x, 0)
        
        return img
    
    def _render_main_weather(
        self,
        draw: ImageDraw.ImageDraw,
        weather: AmbientWeatherData,
        x: int,
        y: int,
        width: int
    ):
        """Render main weather section (left side)."""
        # Weather icon placeholder (you can add actual weather icons later)
        icon_y = y + 200
        # For now, just draw a simple icon placeholder
        self._draw_weather_icon(draw, weather, x + 200, icon_y)
        
        # Large temperature
        temp_text = f"{weather.tempf:.0f}°"
        temp_y = icon_y + 250
        draw.text(
            (x + width // 2, temp_y),
            temp_text,
            fill=self.TEXT_COLOR,
            font=self.font_huge,
            anchor="mm"
        )
        
        # Weather description (based on rain)
        if weather.hourlyrainin > 0:
            desc = "Rain Possible"
        elif weather.dailyrainin > 0:
            desc = "Rainy"
        else:
            desc = "Clear"
        
        desc_y = temp_y + 200
        draw.text(
            (x + width // 2, desc_y),
            desc,
            fill=self.TEXT_COLOR,
            font=self.font_medium,
            anchor="mm"
        )
        
        # Feels like
        feels_y = desc_y + 180
        draw.text(
            (x + width // 2, feels_y),
            f"Feels Like {weather.feels_like:.0f}°",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_normal,
            anchor="mm"
        )
        
        # Temperature range bar (if we have high/low)
        if weather.temp_high and weather.temp_low:
            bar_y = feels_y + 150
            self._draw_temp_range_bar(
                draw,
                weather.temp_low,
                weather.tempf,
                weather.temp_high,
                x + 200,
                bar_y,
                width - 400
            )
        
        # Bottom row: Dew point and humidity
        bottom_y = Config.IMAGE_HEIGHT - 400
        left_x = x + width // 4
        right_x = x + 3 * width // 4
        
        # Dew point
        draw.text(
            (left_x, bottom_y),
            "Dew Point",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_small,
            anchor="mm"
        )
        draw.text(
            (left_x, bottom_y + 80),
            f"{weather.dew_point:.0f}°",
            fill=self.TEXT_COLOR,
            font=self.font_normal,
            anchor="mm"
        )
        
        # Humidity
        draw.text(
            (right_x, bottom_y),
            "Humidity",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_small,
            anchor="mm"
        )
        draw.text(
            (right_x, bottom_y + 80),
            f"{weather.humidity}%",
            fill=self.TEXT_COLOR,
            font=self.font_normal,
            anchor="mm"
        )
    
    def _render_data_cards(
        self,
        draw: ImageDraw.ImageDraw,
        weather: AmbientWeatherData,
        x: int,
        y: int
    ):
        """Render data cards (right side)."""
        # Card dimensions
        card_width = 800
        card_height = 380
        card_margin = 50
        cards_x = x + 100
        
        # Calculate starting Y to center cards vertically
        total_height = (card_height * 4) + (card_margin * 3)
        start_y = (Config.IMAGE_HEIGHT - total_height) // 2
        
        current_y = start_y
        
        # Card 1: Barometric Pressure
        self._draw_pressure_card(
            draw,
            weather,
            cards_x,
            current_y,
            card_width,
            card_height
        )
        current_y += card_height + card_margin
        
        # Card 2: UV Index / Solar Radiation
        if weather.uv is not None or weather.solarradiation is not None:
            self._draw_uv_card(
                draw,
                weather,
                cards_x,
                current_y,
                card_width,
                card_height
            )
            current_y += card_height + card_margin
        
        # Card 3: Rain
        self._draw_rain_card(
            draw,
            weather,
            cards_x,
            current_y,
            card_width,
            card_height
        )
        current_y += card_height + card_margin
        
        # Card 4: Wind
        self._draw_wind_card(
            draw,
            weather,
            cards_x,
            current_y,
            card_width,
            card_height
        )
    
    def _draw_card_background(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        radius: int = 20
    ):
        """Draw rounded rectangle card background."""
        # Draw rounded rectangle
        draw.rounded_rectangle(
            [(x, y), (x + width, y + height)],
            radius=radius,
            fill=self.CARD_BG_COLOR
        )
    
    def _draw_pressure_card(
        self,
        draw: ImageDraw.ImageDraw,
        weather: AmbientWeatherData,
        x: int,
        y: int,
        width: int,
        height: int
    ):
        """Draw barometric pressure card."""
        self._draw_card_background(draw, x, y, width, height)
        
        # Station ID / name (small text, top)
        draw.text(
            (x + 30, y + 30),
            weather.station_name.upper(),
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_tiny,
            anchor="lt"
        )
        
        # Pressure value (large, centered)
        pressure_text = f"{weather.baromrelin:.1f}"
        draw.text(
            (x + width // 2, y + height // 2),
            pressure_text,
            fill=self.TEXT_COLOR,
            font=self.font_large,
            anchor="mm"
        )
        
        # Unit
        draw.text(
            (x + width // 2 + 180, y + height // 2 + 20),
            "mb",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_small,
            anchor="lm"
        )
        
        # Trend indicator (top right)
        draw.text(
            (x + width - 80, y + 40),
            "TREND",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_tiny,
            anchor="rt"
        )
        draw.text(
            (x + width - 80, y + 80),
            "STEADY",
            fill=self.TEXT_COLOR,
            font=self.font_small,
            anchor="rt"
        )
    
    def _draw_uv_card(
        self,
        draw: ImageDraw.ImageDraw,
        weather: AmbientWeatherData,
        x: int,
        y: int,
        width: int,
        height: int
    ):
        """Draw UV index and solar radiation card."""
        self._draw_card_background(draw, x, y, width, height)
        
        # Station ID
        draw.text(
            (x + 30, y + 30),
            weather.station_name.upper(),
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_tiny,
            anchor="lt"
        )
        
        # UV label
        draw.text(
            (x + 30, y + 80),
            "UV",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_small,
            anchor="lt"
        )
        
        # UV value
        uv_text = f"{weather.uv:.1f}" if weather.uv is not None else "N/A"
        draw.text(
            (x + width // 2 - 100, y + height // 2),
            uv_text,
            fill=self.TEXT_COLOR,
            font=self.font_large,
            anchor="mm"
        )
        
        # Right side: Solar radiation and brightness
        if weather.solarradiation is not None:
            draw.text(
                (x + width - 50, y + height - 120),
                "BRIGHTNESS    SOLAR RADIATION",
                fill=self.SECONDARY_TEXT_COLOR,
                font=self.font_tiny,
                anchor="rt"
            )
            draw.text(
                (x + width - 50, y + height - 70),
                f"8867 lux        {weather.solarradiation:.0f} W/m²",
                fill=self.TEXT_COLOR,
                font=self.font_small,
                anchor="rt"
            )
    
    def _draw_rain_card(
        self,
        draw: ImageDraw.ImageDraw,
        weather: AmbientWeatherData,
        x: int,
        y: int,
        width: int,
        height: int
    ):
        """Draw rain accumulation card."""
        self._draw_card_background(draw, x, y, width, height)
        
        # Station ID
        draw.text(
            (x + 30, y + 30),
            weather.station_name.upper(),
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_tiny,
            anchor="lt"
        )
        
        # Label
        draw.text(
            (x + 30, y + 80),
            "last detected" if weather.dailyrainin == 0 else "RAIN",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_small,
            anchor="lt"
        )
        
        # Rain amount or N/A
        if weather.dailyrainin > 0:
            rain_text = f"{weather.dailyrainin:.2f}\""
        else:
            rain_text = "NONE"
        
        draw.text(
            (x + width // 2, y + height // 2 + 20),
            rain_text,
            fill=self.TEXT_COLOR,
            font=self.font_large,
            anchor="mm"
        )
        
        # Bottom right: Today/Yesterday amounts
        draw.text(
            (x + width - 50, y + height - 120),
            "RAIN (TODAY)    RAIN (YESTERDAY)",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_tiny,
            anchor="rt"
        )
        draw.text(
            (x + width - 50, y + height - 70),
            f"{weather.dailyrainin:.2f}\"              0.00\"",
            fill=self.TEXT_COLOR,
            font=self.font_small,
            anchor="rt"
        )
    
    def _draw_wind_card(
        self,
        draw: ImageDraw.ImageDraw,
        weather: AmbientWeatherData,
        x: int,
        y: int,
        width: int,
        height: int
    ):
        """Draw wind speed and direction card."""
        self._draw_card_background(draw, x, y, width, height)
        
        # Station ID
        draw.text(
            (x + 30, y + 30),
            weather.station_name.upper(),
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_tiny,
            anchor="lt"
        )
        
        # Wind direction compass
        wind_dir = self._wind_direction_to_compass(weather.winddir)
        draw.text(
            (x + 200, y + height // 2),
            wind_dir,
            fill=self.TEXT_COLOR,
            font=self.font_large,
            anchor="mm"
        )
        
        # Wind speed
        speed_text = f"{weather.windspeedmph:.1f}"
        draw.text(
            (x + width // 2 + 100, y + height // 2),
            speed_text,
            fill=self.TEXT_COLOR,
            font=self.font_large,
            anchor="mm"
        )
        
        # mph label
        draw.text(
            (x + width // 2 + 250, y + height // 2),
            "mph",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_small,
            anchor="lm"
        )
        
        # Bottom right: Gusting info
        draw.text(
            (x + width - 50, y + height - 120),
            "GUSTING",
            fill=self.SECONDARY_TEXT_COLOR,
            font=self.font_tiny,
            anchor="rt"
        )
        draw.text(
            (x + width - 50, y + height - 70),
            "2 - 5 mph",
            fill=self.TEXT_COLOR,
            font=self.font_small,
            anchor="rt"
        )
    
    def _draw_weather_icon(
        self,
        draw: ImageDraw.ImageDraw,
        weather: AmbientWeatherData,
        x: int,
        y: int
    ):
        """Draw simple weather icon (placeholder - can be enhanced with actual icons)."""
        # Simple icon: circle (sun) with rain drops if raining
        icon_size = 200
        
        if weather.hourlyrainin > 0:
            # Rain icon: cloud with rain drops
            # Cloud (ellipse)
            draw.ellipse(
                [(x, y + 50), (x + icon_size, y + icon_size - 50)],
                fill=self.SECONDARY_TEXT_COLOR
            )
            # Rain drops
            for i in range(3):
                drop_x = x + 40 + (i * 60)
                drop_y = y + icon_size
                draw.ellipse(
                    [(drop_x, drop_y), (drop_x + 20, drop_y + 40)],
                    fill=self.ACCENT_COLOR
                )
        else:
            # Sun icon: circle
            draw.ellipse(
                [(x, y), (x + icon_size, y + icon_size)],
                fill=(255, 200, 0),
                outline=self.TEXT_COLOR,
                width=3
            )
    
    def _draw_temp_range_bar(
        self,
        draw: ImageDraw.ImageDraw,
        low: float,
        current: float,
        high: float,
        x: int,
        y: int,
        width: int
    ):
        """Draw temperature range bar with current position indicator."""
        bar_height = 15
        
        # Calculate current position on bar
        temp_range = high - low
        if temp_range > 0:
            current_pos = (current - low) / temp_range
        else:
            current_pos = 0.5
        
        # Draw bar background (gradient from blue to red)
        draw.rounded_rectangle(
            [(x, y), (x + width, y + bar_height)],
            radius=8,
            fill=(100, 100, 150)
        )
        
        # Draw filled portion up to current temp
        fill_width = int(width * current_pos)
        draw.rounded_rectangle(
            [(x, y), (x + fill_width, y + bar_height)],
            radius=8,
            fill=(200, 100, 200)
        )
        
        # Draw current position indicator
        indicator_x = x + fill_width
        draw.ellipse(
            [(indicator_x - 20, y - 10), (indicator_x + 20, y + bar_height + 10)],
            fill=self.TEXT_COLOR,
            outline=self.ACCENT_COLOR,
            width=3
        )
        
        # Labels
        label_y = y + bar_height + 50
        draw.text((x, label_y), f"↓ {low:.0f}°", fill=self.SECONDARY_TEXT_COLOR, font=self.font_small, anchor="lt")
        draw.text((x + width, label_y), f"{high:.0f}° ↑", fill=self.SECONDARY_TEXT_COLOR, font=self.font_small, anchor="rt")
    
    def _wind_direction_to_compass(self, degrees: int) -> str:
        """Convert wind direction degrees to compass direction."""
        if degrees is None:
            return "N"
        
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]

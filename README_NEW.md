# 🖼️ Samsung Frame TV Signage

Automatically generates and uploads dynamic signage images to your Samsung Frame TV in Art Mode.

**v2.0** - Modular architecture with sports, ferry schedules, whale tracking, and more!

---

## 🚀 Features

- **Real-time Data Integration**
  - Tesla battery & range from Home Assistant
  - Live weather with condition-based backgrounds
  - Stock quotes during market hours
  - Ferry schedules with vessel tracking maps
  - NFL game scores with live updates
  - Whale sightings from Puget Sound

- **Beautiful 4K Rendering**
  - Edge-to-edge 3840×2160 display
  - Multiple layout engines (centered, left-aligned, split, grid)
  - Smart safe zones (5% margins)
  - Configurable backgrounds (gradient, local, Unsplash, Pexels)
  - Semi-transparent overlays for text readability

- **Intelligent Scheduling**
  - Daemon mode with live sports detection
  - Adjustable update intervals
  - Fast updates during live events
  - Cron job support

- **Clean Architecture**
  - Modular client/renderer separation
  - Type-safe data models
  - Comprehensive error handling
  - File management with 7-day retention

---

## ⚡ Quick Start

1. **Clone the repository**
    ```bash
    git clone https://github.com/simonpo/signage.git
    cd signage
    ```

2. **Set up your environment**
    ```bash
    cp .env.example .env
    nano .env  # Add your API keys and configuration
    ```

3. **Install dependencies**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    
    # If using marine traffic screenshots:
    playwright install chromium
    ```

4. **Generate images**
    ```bash
    # Generate all enabled signage
    python generate_signage.py --source all
    
    # Generate specific sources
    python generate_signage.py --source tesla
    python generate_signage.py --source weather
    python generate_signage.py --source nfl
    
    # Run in daemon mode
    python generate_signage.py --daemon
    ```

5. **Upload to Frame TV**
    ```bash
    python upload_to_frame.py
    ```

---

## 📁 Project Structure

```
signage/
├── src/
│   ├── clients/           # API clients for data sources
│   │   ├── base.py        # Base client with retry logic
│   │   ├── homeassistant.py
│   │   ├── weather.py
│   │   ├── stock.py
│   │   ├── ferry.py
│   │   ├── marine_traffic.py
│   │   ├── whale_tracker.py
│   │   └── sports/        # Sports-specific clients
│   ├── models/            # Data models
│   ├── renderers/         # Image rendering
│   ├── backgrounds/       # Background providers
│   ├── utils/             # Utilities
│   ├── config.py          # Configuration management
│   └── scheduler.py       # Daemon mode scheduler
├── generate_signage.py    # Main generation script
├── upload_to_frame.py     # Upload to Frame TV
├── backgrounds/           # Local background images
├── tests/                 # Test suite
└── scripts/               # Setup scripts
```

---

## 🎨 Layout Types

- **Centered**: Large text centered on screen (weather, stock quotes)
- **Left-Aligned**: Left-aligned with smart indentation (sports fixtures, whales)
- **Grid**: Compact table layout (league standings)
- **Split**: Text on left, map/image on right (ferry schedules)

---

## 🔧 Configuration

All configuration is in `.env`. See `.env.example` for a complete template.

### Required Settings

```bash
# Home Assistant
HA_URL=http://homeassistant.local:8123
HA_TOKEN=your_long_lived_token

# Tesla Entities
TESLA_BATTERY=sensor.tesla_battery
TESLA_RANGE=sensor.tesla_range

# Weather
WEATHER_CITY=Seattle
WEATHER_API_KEY=your_openweathermap_key
```

### Optional Features

```bash
# Sports (NFL)
SEAHAWKS_ENABLED=true

# Background Images
UNSPLASH_API_KEY=your_unsplash_key
PEXELS_API_KEY=your_pexels_key
```

---

## 🕐 Scheduling

### Daemon Mode (Recommended)

```bash
python generate_signage.py --daemon
```

Updates automatically with smart intervals - **every 2 min during live games**.

### Cron Jobs

```bash
./scripts/setup_cron.sh
```

---

## 🏈 Sports Integration

Currently supports NFL via ESPN API. Live game detection with automatic fast updates.

---

## 🖼️ Background Modes

1. **Gradient**: Smooth blue gradient
2. **Local**: Random from `backgrounds/topic/`
3. **Unsplash**: High-quality photos (cached 7 days)
4. **Pexels**: Stock photos (cached 7 days)

---

## 🧪 Testing

```bash
pytest tests/ -v
python -c "from src.config import Config; Config.validate(); print('✓')"
```

---

## 🔒 Security

- **Never commit `.env`**
- Use long-lived HA tokens
- Rotate API keys regularly

---

## 🙏 Credits

- **Samsung TV API**: [Nick Waterton's fork](https://github.com/NickWaterton/samsung-tv-ws-api)
- **ESPN API**: Sports data
- **OpenWeatherMap**: Weather data

---

## 📝 License

MIT License

---

**Made with ❤️ for the Samsung Frame TV**

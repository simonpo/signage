# Samsung Frame TV Signage

Generates data-driven images for display on Samsung Frame TVs in Art Mode. Still very much a work in progress.

## What it does

Fetches data from various sources (weather APIs, personal weather stations, ferry schedules, speedtest trackers, etc.) and renders them as 4K images with configurable backgrounds. These can be uploaded to a Samsung Frame TV to display alongside regular artwork.

The layout engine needs significant work and many planned topics haven't been implemented yet. See `ROADMAP.md` for what's planned.

## Available topics

- `weather` - OpenWeatherMap data with expanded conditions
- `ambient` - Personal Ambient Weather station data
- `sensors` - Multi-sensor view from Ambient Weather (greenhouse, chicken coop, etc.)
- `ferry` - WSDOT ferry schedules (Fauntleroy/Southworth route)
- `speedtest` - Local speedtest tracker results
- `tesla` - Home Assistant integration (battery, range)
- `stock` - Stock quotes
- `whales` - Marine traffic (when implemented)
- `sports` - Sports scores (partially implemented)

Run `python generate_signage.py --source <topic>` to generate an image, or `--source all` for everything.

## Setup

1. Clone and create a virtual environment:
   ```bash
   git clone https://github.com/simonpo/signage.git
   cd signage
   ./scripts/setup.sh
   ```

2. Configure your environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys, URLs, and tokens
   ```

3. Generate an image:
   ```bash
   source signage-env/bin/activate
   python generate_signage.py --source weather
   ```

4. Upload to your TV (optional):
   ```bash
   python upload_to_frame.py
   ```

## Configuration

All configuration is done via environment variables in `.env`. See `.env.example` for the full list of options. Key settings:

- API keys for OpenWeatherMap, Ambient Weather, etc.
- Background mode (`local`, `pexels`, `unsplash`, or `gradient`)
- Topic-specific settings (sensor names, ferry routes, etc.)

Don't commit your `.env` file.

## Project structure

```
src/
  clients/        - API clients for data sources
  models/         - Data models and signage content
  renderers/      - Image rendering and layouts
  backgrounds/    - Background providers
  utils/          - File management, caching
backgrounds/      - Local background images organised by topic
art_folder/       - Generated images (gitignored)
```

## Scheduling

Run `./scripts/setup_cron.sh` to configure automated generation. Edit the script first to set which topics you want and how often.

## Known issues

- Layout engine uses fixed spacing that doesn't adapt well to content length
- Some topics (whales, sports) are partially implemented
- Ferry layout could be improved
- No support for multiple weather locations yet
- Background image selection is basic

## Credits

Uses [Nick Waterton's samsung-tv-ws-api fork](https://github.com/NickWaterton/samsung-tv-ws-api) for uploads to 2024+ Frame TVs.

# Samsung Frame TV Signage

Generates and uploads dynamic signage images to a Samsung Frame TV in Art Mode.

## Features

- Fetches real-time data from Home Assistant (Tesla battery/range)
- Pulls weather and stock quotes
- Renders high-resolution 4K images with gradient background
- Securely uploads via `samsungtvws` (2024+ Frame support)
- All secrets stored in `.env` (never committed)

## Quick Start

```bash
git clone https://github.com/simonpo/signage.git
cd signage

# 1. Copy template
cp .env.example .env

# 2. Edit with your values
nano .env
#    - TV_IP, HA_URL, HA_TOKEN
#    - API keys, entities

# 3. Install
pip install -r requirements.txt

# 4. Run
python generate_signage.py   # creates images
python upload_to_frame.py    # uploads to TV

## Files

- `generate_signage.py` — creates images in `art_folder/`
- `upload_to_frame.py`   — uploads new images to TV
- `.env`                 — **your secrets** (git-ignored)
- `.env.example`         — template
- `requirements.txt`     — locked dependencies

## Security

- **Never commit `.env`**
- Use long-lived HA token (Profile → Long-Lived Access Tokens)
- Rotate API keys regularly

## Chapeau!

- **Samsung TV WebSocket API**:  
  [Nick Waterton’s `samsung-tv-ws-api` fork](https://github.com/NickWaterton/samsung-tv-ws-api)  
  Critical for 2024+ Frame TV Art Mode support. Thank you, Nick!
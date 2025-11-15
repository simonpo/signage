#!/usr/bin/env python3
"""
Generate signage images from HA, Weather, Stock.
All config from .env — NO SECRETS IN CODE.
"""

import json
import logging
import os
import random
from datetime import datetime
from pathlib import Path

import pytz
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# === LOAD .env ===
load_dotenv()

# === CONFIG FROM .env ===
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")
TESLA_BATTERY = os.getenv("TESLA_BATTERY")
TESLA_RANGE = os.getenv("TESLA_RANGE")
WEATHER_CITY = os.getenv("WEATHER_CITY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
STOCK_SYMBOL = os.getenv("STOCK_SYMBOL")
STOCK_API_KEY = os.getenv("STOCK_API_KEY")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "art_folder")
FONT_PATH = os.getenv("FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
TIMEZONE = os.getenv("TIMEZONE", "US/Pacific")

# === VALIDATE REQUIRED ===
required = ["HA_URL", "HA_TOKEN", "TESLA_BATTERY", "TESLA_RANGE", "WEATHER_CITY", "WEATHER_API_KEY"]
missing = [v for v in required if not os.getenv(v)]
if missing:
    raise RuntimeError(f"Missing .env vars: {', '.join(missing)}")

# === PATHS ===
BASE_DIR = Path(__file__).parent.resolve()
OUTPUT_PATH = BASE_DIR / OUTPUT_DIR
os.makedirs(OUTPUT_PATH, exist_ok=True)

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

# === TIME ===
try:
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
except Exception as e:
    logging.warning(f"Invalid timezone {TIMEZONE}: {e}. Using UTC.")
    tz = pytz.UTC
    now = datetime.now(tz)


# === HA FETCH ===
def fetch_ha(entity_id):
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }
    try:
        url = f"{HA_URL.rstrip('/')}/api/states/{entity_id}"
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("state", "N/A"), data.get("attributes", {})
    except Exception as e:
        logging.error(f"HA fetch failed for {entity_id}: {e}")
        return "N/A", {}


# === CREATE IMAGE ===
def create_signage(lines, filename):
    img = Image.new("RGB", (3840, 2160), (30, 30, 80))
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(2160):
        r = int(30 + (y / 2160) * 100)
        g = int(30 + (y / 2160) * 150)
        b = int(80 + (y / 2160) * 175)
        draw.line([(0, y), (3840, y)], fill=(r, g, b))

    # Fonts
    try:
        font_title = ImageFont.truetype(FONT_PATH, 180)
        font_body = ImageFont.truetype(FONT_PATH, 120)
        font_small = ImageFont.truetype(FONT_PATH, 80)
    except Exception as e:
        logging.warning(f"Font load failed: {e}. Using default.")
        font_title = font_body = font_small = ImageFont.load_default()

    # Draw lines
    y = 400
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_body)
        x = (3840 - bbox[2]) / 2
        draw.text((x, y), line, fill=(255, 255, 255), font=font_body)
        y += 220

    # Timestamp
    ts = f"Updated: {now.strftime('%m/%d %I:%M %p %Z')}"
    bbox = draw.textbbox((0, 0), ts, font=font_small)
    x = (3840 - bbox[2]) / 2
    draw.text((x, 1850), ts, fill=(200, 200, 255), font=font_small)

    # Save
    path = OUTPUT_PATH / filename
    img.save(path, "JPEG", quality=95)
    logging.info(f"Saved: {path}")
    return path


# === MAIN ===
def main():
    # 1. Tesla
    batt, battr = fetch_ha(TESLA_BATTERY)
    rng, rattr = fetch_ha(TESLA_RANGE)
    unit_b = battr.get("unit_of_measurement", "%")
    unit_r = rattr.get("unit_of_measurement", " mi")
    create_signage([
        "Tesla Model Y",
        f"Battery: {batt}{unit_b}",
        f"Range: {rng}{unit_r}"
    ], f"tesla_{random.randint(1000,9999)}.jpg")

    # 2. Weather
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {"q": WEATHER_CITY, "appid": WEATHER_API_KEY, "units": "imperial"}
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        w = r.json()
        temp = w["main"]["temp"]
        desc = w["weather"][0]["description"].title()
        create_signage([
            f"Weather in {WEATHER_CITY}",
            f"{temp}°F",
            desc
        ], f"weather_{random.randint(1000,9999)}.jpg")
    except Exception as e:
        logging.error(f"Weather fetch failed: {e}")

    # 3. Stock
    if STOCK_API_KEY and STOCK_SYMBOL:
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": STOCK_SYMBOL,
                "apikey": STOCK_API_KEY
            }
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            s = r.json()
            quote = s.get("Global Quote", {})
            price = quote.get("05. price", "N/A")
            change = quote.get("10. change percent", "N/A")
            create_signage([
                STOCK_SYMBOL,
                f"${price}",
                f"{change}"
            ], f"stock_{random.randint(1000,9999)}.jpg")
        except Exception as e:
            logging.error(f"Stock fetch failed: {e}")

    logging.info(f"Generated images in: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
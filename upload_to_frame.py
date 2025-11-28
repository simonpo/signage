#!/usr/bin/env python3
"""
Upload new images to Samsung Frame TV Art Mode.
All configuration is loaded from .env (never committed).
"""


import json
import logging
import os
import hashlib
from pathlib import Path

import urllib3
from dotenv import load_dotenv
from samsungtvws import SamsungTVWS

# === LOAD .env (safe, silent if missing) ===
load_dotenv()

# === CONFIG FROM .env ===
TV_IP = os.getenv("TV_IP")
TV_PORT = int(os.getenv("TV_PORT", "8002"))  # HTTPS default
TOKEN_FILE = os.getenv("TOKEN_FILE", "tv-token.txt")  # Relative to script
ART_FOLDER = os.getenv("ART_FOLDER", "art_folder/frame")  # Primary output for TV
UPLOADED_LOG = os.getenv("UPLOADED_LOG", "uploaded.json")

# === VALIDATE REQUIRED VARS ===
required_vars = ["TV_IP"]
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    raise RuntimeError(f"Missing required .env variables: {', '.join(missing)}")

# === PATHS (resolve relative to script location) ===
BASE_DIR = Path(__file__).parent.resolve()
TOKEN_PATH = BASE_DIR / TOKEN_FILE
ART_PATH = BASE_DIR / ART_FOLDER
LOG_PATH = BASE_DIR / UPLOADED_LOG

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S"
)

# === Suppress SSL warnings (safe on LAN) ===
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def main():
    # === STEP 1: Connect to TV ===
    try:
        tv = SamsungTVWS(host=TV_IP, port=TV_PORT, token_file=str(TOKEN_PATH))
        tv.open()
        logging.info(f"Connected to Samsung Frame TV at {TV_IP}:{TV_PORT}")
    except Exception as e:
        logging.error(f"Failed to connect to TV: {e}")
        return

    # === STEP 2: Check Art Mode support ===
    try:
        art = tv.art()
        if not art.supported():
            logging.error("Art Mode is NOT supported on this TV")
            tv.close()
            return
        logging.info("Art Mode is supported")
    except Exception as e:
        logging.error(f"Art Mode check failed: {e}")
        tv.close()
        return


    # === STEP 3: Load uploaded log (filename -> sha256 hash) ===
    uploaded = {}
    if LOG_PATH.exists():
        try:
            with open(LOG_PATH) as f:
                uploaded = json.load(f)
            if not isinstance(uploaded, dict):
                logging.warning(f"Uploaded log format invalid, resetting.")
                uploaded = {}
            logging.info(f"Loaded {len(uploaded)} previously uploaded file hashes")
        except Exception as e:
            logging.warning(f"Could not read {LOG_PATH}: {e}")

    # === STEP 4: Upload new images ===
    if not ART_PATH.exists() or not ART_PATH.is_dir():
        logging.error(f"Art folder not found: {ART_PATH}")
        tv.close()
        return

    new_uploads = 0
    for file_path in ART_PATH.iterdir():
        if not file_path.is_file():
            continue
        if not file_path.name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        # Compute SHA256 hash of file contents
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            file_hash = hashlib.sha256(data).hexdigest()
        except Exception as e:
            logging.error(f"Failed to read {file_path.name} for hashing: {e}")
            continue

        # Check if file with same name and hash was already uploaded
        prev_hash = uploaded.get(file_path.name)
        if prev_hash == file_hash:
            continue  # Already uploaded this version

        try:
            file_type = "JPEG" if file_path.suffix.lower() in {".jpg", ".jpeg"} else "PNG"
            art_id = art.upload(data, file_type=file_type)
            uploaded[file_path.name] = file_hash
            new_uploads += 1
            logging.info(f"Uploaded: {file_path.name} → {art_id}")
        except Exception as e:
            logging.error(f"Upload failed {file_path.name}: {e}")

    # === STEP 5: Save updated log ===

    try:
        with open(LOG_PATH, "w") as f:
            json.dump(uploaded, f, indent=2)
    except Exception as e:
        logging.error(f"Failed to save {LOG_PATH}: {e}")

    if new_uploads == 0:
        logging.info("No new images to upload")
    else:
        logging.info(f"Uploaded {new_uploads} new image(s)")

    # === STEP 6: Optional cleanup (keep last 100) ===
    try:
        available = art.available()
        if len(available) > 100:
            old_ids = [item["id"] for item in available[:-100]]
            art.delete_list(old_ids)
            logging.info(f"Deleted {len(old_ids)} old artworks")
    except Exception as e:
        logging.warning(f"Cleanup failed: {e}")

    # === STEP 7: Close ===
    tv.close()
    logging.info("Upload session complete!")


if __name__ == "__main__":
    main()

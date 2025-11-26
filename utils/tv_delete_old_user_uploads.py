#!/usr/bin/env python3
"""
Deletes user-uploaded (mobile) artworks from Frame TV older than a specified age.
You choose the threshold in hours.
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from samsungtvws import SamsungTVWS

# --- Load .env variables ---
load_dotenv()
TV_IP = os.getenv("TV_IP")
TV_PORT = int(os.getenv("TV_PORT", "8002"))
TOKEN_FILE = os.getenv("TOKEN_FILE", "tv-token.txt")

THRESHOLD_HOURS = 5  # Set your desired age threshold here
AGE_LIMIT = timedelta(hours=THRESHOLD_HOURS)


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y:%m:%d %H:%M:%S")
    except Exception:
        return None


def main():
    tv = SamsungTVWS(host=TV_IP, port=TV_PORT, token_file=TOKEN_FILE)
    tv.open()
    art = tv.art()
    if not art.supported():
        print("Art Mode not supported.")
        tv.close()
        return
    artworks = art.available()
    now = datetime.now()

    # Get user-uploaded images older than threshold
    to_delete = []
    for item in artworks:
        if item.get("content_type") != "mobile":
            continue
        dt = parse_date(item.get("image_date", ""))
        if dt and (now - dt) > AGE_LIMIT:
            to_delete.append(item["content_id"])

    if not to_delete:
        print("No user-uploaded images older than threshold found.")
    else:
        print(f"Deleting {len(to_delete)} artworks older than {THRESHOLD_HOURS} hours:")
        for cid in to_delete:
            print(f"  {cid}")
        art.delete_list(to_delete)
        print("Deletion complete.")

    tv.close()


if __name__ == "__main__":
    main()

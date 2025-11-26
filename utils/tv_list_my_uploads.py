#!/usr/bin/env python3
"""
Lists user-uploaded (mobile) artworks on Samsung Frame TV,
shows artwork content_id, image_date, and highlights any older than 25 hours.
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

CUTOFF = timedelta(hours=25)


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

    # Filter user uploads
    user_arts = [i for i in artworks if i.get("content_type") == "mobile"]
    if not user_arts:
        print("No user-uploaded artworks found.")
    else:
        print(f"User-uploaded artworks ({len(user_arts)}):")
        # Sort artworks by date, descending
        arts_with_date = []
        for item in user_arts:
            dt = parse_date(item.get("image_date", ""))
            arts_with_date.append((dt, item))
        arts_with_date.sort(
            key=lambda tup: tup[0] if tup[0] is not None else datetime.min, reverse=True
        )

        for dt, item in arts_with_date:
            cid = item.get("content_id", "<no id>")
            date_str = item.get("image_date", "")
            age_str = ""
            if dt:
                age = now - dt
                if age > CUTOFF:
                    age_str = f"OLD ({int(age.total_seconds() // 3600)} hours ago)"
                else:
                    age_str = f"{int(age.total_seconds() // 3600)} hours ago"
            else:
                age_str = "No date"
            print(f"ID: {cid} | Date: {date_str} | {age_str}")

    tv.close()


if __name__ == "__main__":
    main()

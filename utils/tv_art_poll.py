#!/usr/bin/env python3

"""
Polls the Samsung Frame TV's Art Mode and prints available artwork info.
Requires .env configuration: TV_IP, TV_PORT (optional), TOKEN_FILE (optional)
"""

import os
from dotenv import load_dotenv
from samsungtvws import SamsungTVWS

# Load configuration from .env
load_dotenv()
TV_IP = os.getenv("TV_IP")
TV_PORT = int(os.getenv("TV_PORT", "8002"))
TOKEN_FILE = os.getenv("TOKEN_FILE", "tv-token.txt")

if not TV_IP:
    raise RuntimeError("TV_IP missing from .env")

def main():
    print("Connecting to TV...")
    tv = SamsungTVWS(
        host=TV_IP,
        port=TV_PORT,
        token_file=TOKEN_FILE,
    )
    tv.open()

    print("Checking Art Mode support...")
    art = tv.art()
    if not art.supported():
        print("Art Mode not supported on this TV.")
        tv.close()
        return

    print("Polling for available artworks...")
    available = art.available()
    print("Available artworks response:")
    print(f"Type: {type(available)}")
    print(f"Raw output: {available}")

    if available and isinstance(available, list):
        print("\n---- Artworks info ----")
        for i, item in enumerate(available):
            print(f"{i+1}: {item}")
    elif available:
        print("Received non-list response:")
        print(available)
    else:
        print("No artworks returned")

    tv.close()

if __name__ == "__main__":
    main()

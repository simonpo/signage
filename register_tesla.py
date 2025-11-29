#!/usr/bin/env python3
"""
Register with Tesla Fleet API
This is required before you can access vehicles.
Uses partner token for registration.
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("TESLA_CLIENT_ID")
CLIENT_SECRET = os.getenv("TESLA_CLIENT_SECRET")
REGION = os.getenv("TESLA_REGION", "na")

REGIONS = {
    "na": "https://fleet-api.prd.na.vn.cloud.tesla.com",
    "eu": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
    "cn": "https://fleet-api.prd.cn.vn.cloud.tesla.cn",
}
BASE_URL = REGIONS[REGION]
TOKEN_URL = "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token"


def get_partner_token():
    """Get a partner token using client_credentials."""
    payload = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "openid vehicle_device_data vehicle_location energy_device_data",
        "audience": BASE_URL,
    }

    response = requests.post(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()

    return response.json()["access_token"]


def register(access_token):
    """Call the register endpoint."""
    url = f"{BASE_URL}/api/1/partner_accounts"

    # Use Tailscale Funnel hostname
    # The public key is not strictly required if we don't use vehicle commands
    payload = {"domain": "electric.powell.at"}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    print("Registering with Tesla Fleet API...")
    print(f"Region: {REGION}")
    print(f"URL: {url}")
    print()

    response = requests.post(url, json=payload, headers=headers)

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()

    if response.status_code in [200, 201]:
        print("✓ Registration successful!")
        return True
    elif response.status_code == 409:
        print("✓ Already registered!")
        return True
    else:
        print(f"✗ Registration failed: {response.status_code}")
        print(f"  {response.text}")
        return False


if __name__ == "__main__":
    print("Step 1: Getting partner authentication token...")
    partner_token = get_partner_token()
    print(f"✓ Got partner token: {partner_token[:50]}...")
    print()

    print("Step 2: Registering account...")
    success = register(partner_token)

    if success:
        print()
        print("=" * 60)
        print("Registration complete!")
        print("You can now run: python ./generate_signage.py --source tesla --html")
        print("=" * 60)

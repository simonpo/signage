#!/usr/bin/env python3
"""
Tesla Fleet API OAuth Helper
Performs the authorization_code flow to get access to your own vehicle.
"""

import json
import os
import secrets
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

# Load env
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("TESLA_CLIENT_ID")
CLIENT_SECRET = os.getenv("TESLA_CLIENT_SECRET")
REGION = os.getenv("TESLA_REGION", "na")
REDIRECT_URI = "http://localhost:3000/callback"

REGIONS = {
    "na": "https://fleet-api.prd.na.vn.cloud.tesla.com",
    "eu": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
    "cn": "https://fleet-api.prd.cn.vn.cloud.tesla.cn",
}
AUDIENCE = REGIONS[REGION]

AUTH_URL = "https://auth.tesla.com/oauth2/v3/authorize"
TOKEN_URL = "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token"

# State for OAuth flow
auth_code = None
state_value = secrets.token_urlsafe(32)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Tesla."""

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def do_GET(self):
        """Handle GET request (OAuth callback)."""
        global auth_code

        # Parse query parameters
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # Extract code and state
        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]

        if code and state == state_value:
            auth_code = code

            # Send success response
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <head><title>Tesla OAuth Success</title></head>
                <body style="font-family: Arial; text-align: center; padding-top: 100px;">
                    <h1>&#x2713; Authorization Successful!</h1>
                    <p>You can close this window and return to the terminal.</p>
                </body>
                </html>
            """
            )
        else:
            # Send error response
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"""
                <html>
                <head><title>Tesla OAuth Error</title></head>
                <body style="font-family: Arial; text-align: center; padding-top: 100px;">
                    <h1>&#x2717; Authorization Failed</h1>
                    <p>Please try again.</p>
                </body>
                </html>
            """
            )


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for access and refresh tokens."""
    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "audience": AUDIENCE,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid offline_access vehicle_device_data vehicle_location energy_device_data",
    }

    response = requests.post(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()

    return response.json()


def main():
    """Run OAuth flow."""
    print("=" * 60)
    print("Tesla Fleet API OAuth Authorization")
    print("=" * 60)
    print()

    # Build authorization URL
    params = {
        "client_id": CLIENT_ID,
        "locale": "en-US",
        "prompt": "login",
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid offline_access vehicle_device_data vehicle_location energy_device_data",
        "state": state_value,
    }

    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    print("Step 1: Opening browser for Tesla authorization...")
    print()
    print(f"URL: {auth_url}")
    print()

    # Open browser
    webbrowser.open(auth_url)

    print("Step 2: Starting local server on http://localhost:3000 ...")
    print("         Waiting for authorization callback...")
    print()

    # Start local server to receive callback
    server = HTTPServer(("localhost", 3000), OAuthCallbackHandler)

    # Wait for callback (timeout after 5 minutes)
    import time

    timeout = time.time() + 300
    while auth_code is None and time.time() < timeout:
        server.handle_request()

    if auth_code is None:
        print("\n✗ Authorization timed out after 5 minutes")
        return

    print("Step 3: Exchanging authorization code for tokens...")
    print()

    try:
        token_data = exchange_code_for_tokens(auth_code)

        # Save tokens
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 28800)  # Default 8 hours

        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Save to file
        with open(".tesla_tokens.json", "w") as f:
            json.dump(
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at.isoformat(),
                },
                f,
                indent=2,
            )

        print("✓ Success! Tokens saved to .tesla_tokens.json")
        print()
        print(f"Access Token: {access_token[:50]}...")
        print(f"Refresh Token: {refresh_token[:50] if refresh_token else 'N/A'}...")
        print(f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("You can now run: python ./generate_signage.py --source tesla --html")

    except Exception as e:
        print(f"\n✗ Failed to exchange code for tokens: {e}")


if __name__ == "__main__":
    main()

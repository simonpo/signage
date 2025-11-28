#!/bin/bash
# Tesla Fleet API Caddy setup script
# Run this on your Proxmox server

set -e

echo "Tesla Fleet API Caddy Setup"
echo "============================"
echo ""

# Create directory structure
mkdir -p ~/tesla-api
cd ~/tesla-api

# Create docker-compose.yml for Caddy
cat > docker-compose.yml << 'COMPOSE'
version: '3'

services:
  caddy:
    image: caddy:latest
    container_name: tesla-caddy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./well-known:/srv/.well-known:ro
      - ./caddy_data:/data
      - ./caddy_config:/config
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
COMPOSE

# Create Caddyfile (replace api.powell.at with your actual domain)
cat > Caddyfile << 'CADDY'
# Replace api.powell.at with your actual domain
# Caddy automatically gets SSL certificates from Let's Encrypt!

api.powell.at {
    # Tesla public key endpoint
    handle /.well-known/appspecific/com.tesla.3p.public-key.pem {
        root * /srv
        file_server
        header Content-Type application/x-pem-file
        header Access-Control-Allow-Origin *
    }

    # Health check endpoint
    handle / {
        respond "Tesla Fleet API - OK" 200
    }

    # Log errors
    log {
        output file /data/access.log
    }
}
CADDY

# Create well-known directory structure
mkdir -p well-known/appspecific

echo ""
echo "✓ Caddy setup created"
echo ""
echo "Next steps:"
echo "1. Edit Caddyfile and replace 'api.powell.at' with your actual domain"
echo ""
echo "2. Copy your tesla_public_key.pem to:"
echo "   ~/tesla-api/well-known/appspecific/com.tesla.3p.public-key.pem"
echo ""
echo "3. Get your public IP address:"
echo "   curl -4 ifconfig.me"
echo ""
echo "4. Configure DNS at EuroDNS:"
echo "   - Type: A"
echo "   - Name: api (do NOT use 'tesla' - prohibited by Tesla)"
echo "   - Value: [your public IP]"
echo "   - TTL: 3600"
echo ""
echo "5. Set up port forwarding on your router/OPNsense:"
echo "   - External Port 80 → Proxmox IP:80"
echo "   - External Port 443 → Proxmox IP:443"
echo ""
echo "6. Start Caddy (it will automatically get SSL certificate):"
echo "   docker-compose up -d"
echo ""
echo "7. Test the setup:"
echo "   curl https://api.powell.at/"
echo "   curl https://api.powell.at/.well-known/appspecific/com.tesla.3p.public-key.pem"
echo ""
echo "That's it! Caddy handles SSL automatically - no certbot needed!"
echo ""

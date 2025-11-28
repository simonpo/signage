#!/bin/bash
# Quick setup script for Tailscale on Proxmox
# Run this on your Mac to copy files and show next steps

PROXMOX_IP="192.168.1.30"

echo "Tesla Fleet API - Tailscale Funnel Setup"
echo "========================================="
echo ""
echo "Step 1: Copying public key to Proxmox..."
scp tesla_public_key.pem root@$PROXMOX_IP:~/
echo "✓ Done"
echo ""
echo "Step 2: Ready to SSH into Proxmox"
echo ""
echo "Copy/paste these commands on Proxmox:"
echo ""
echo "------- START COPY HERE -------"
cat << 'PROXMOX'
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start Tailscale and authenticate
tailscale up

# Enable HTTPS certificates
HOSTNAME=$(tailscale status --json | jq -r '.Self.DNSName' | sed 's/\.$//')
echo "Your Tailscale hostname is: $HOSTNAME"
tailscale cert $HOSTNAME

# Create Tesla API directory
mkdir -p ~/tesla-api/well-known/appspecific
cd ~/tesla-api

# Copy public key to correct location
cp ~/tesla_public_key.pem ~/tesla-api/well-known/appspecific/com.tesla.3p.public-key.pem

# Create docker-compose.yml
cat > docker-compose.yml << 'COMPOSE'
version: '3'

services:
  nginx:
    image: nginx:alpine
    container_name: tesla-nginx
    ports:
      - "127.0.0.1:8443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./well-known:/usr/share/nginx/html/.well-known:ro
      - /var/lib/tailscale/certs:/etc/nginx/certs:ro
    restart: unless-stopped
COMPOSE

# Create nginx.conf with actual hostname
cat > nginx.conf << NGINX_CONF
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-pem;

    server {
        listen 443 ssl http2;
        server_name _;

        ssl_certificate /etc/nginx/certs/$HOSTNAME.crt;
        ssl_certificate_key /etc/nginx/certs/$HOSTNAME.key;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location /.well-known/appspecific/com.tesla.3p.public-key.pem {
            root /usr/share/nginx/html;
            add_header Content-Type application/x-pem-file;
            add_header Access-Control-Allow-Origin *;
        }

        location / {
            return 200 "Tesla Fleet API - OK\n";
            add_header Content-Type text/plain;
        }
    }
}
NGINX_CONF

# Start nginx
docker-compose up -d

# Enable Tailscale Funnel
tailscale funnel 8443

# Show status
echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Your public URL is: https://$HOSTNAME"
echo ""
echo "Test it with:"
echo "  curl https://$HOSTNAME/"
echo "  curl https://$HOSTNAME/.well-known/appspecific/com.tesla.3p.public-key.pem"
echo ""
echo "Copy this hostname to use on your Mac!"
echo ""
PROXMOX
echo "------- END COPY HERE -------"
echo ""
echo "Now SSH into Proxmox and run those commands:"
echo "  ssh root@$PROXMOX_IP"
echo ""

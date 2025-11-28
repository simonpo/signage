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

# Create docker-compose.yml
cat > docker-compose.yml << 'COMPOSE'
version: '3'

services:
  nginx:
    image: nginx:alpine
    container_name: tesla-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./well-known:/usr/share/nginx/html/.well-known:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    restart: unless-stopped
    networks:
      - tesla-net

  certbot:
    image: certbot/certbot
    container_name: tesla-certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - tesla-net

networks:
  tesla-net:
    driver: bridge
COMPOSE

# Create nginx.conf
cat > nginx.conf << 'NGINX'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-pem;

    server {
        listen 80;
        server_name tesla.powell.at;

        # ACME challenge for Let's Encrypt
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        # Redirect all other HTTP to HTTPS
        location / {
            return 301 https://$host$request_uri;
        }
    }

    server {
        listen 443 ssl http2;
        server_name tesla.powell.at;

        ssl_certificate /etc/letsencrypt/live/tesla.powell.at/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/tesla.powell.at/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Tesla public key
        location /.well-known/appspecific/com.tesla.3p.public-key.pem {
            root /usr/share/nginx/html;
            add_header Content-Type application/x-pem-file;
            add_header Access-Control-Allow-Origin *;
        }

        # Health check
        location / {
            return 200 "Tesla Fleet API - OK\n";
            add_header Content-Type text/plain;
        }
    }
}
NGINX

# Create well-known directory structure
mkdir -p well-known/appspecific

echo ""
echo "✓ Docker Compose setup created"
echo ""
echo "Next steps:"
echo "1. Copy your tesla_public_key.pem to this location:"
echo "   ~/tesla-api/well-known/appspecific/com.tesla.3p.public-key.pem"
echo ""
echo "2. Get your public IP address:"
echo "   curl -4 ifconfig.me"
echo ""
echo "3. Configure DNS at EuroDNS:"
echo "   - Type: A"
echo "   - Name: tesla"
echo "   - Value: [your public IP]"
echo "   - TTL: 3600"
echo ""
echo "4. Set up port forwarding on your router:"
echo "   - External Port 80 → Proxmox IP:80"
echo "   - External Port 443 → Proxmox IP:443"
echo ""
echo "5. Start nginx (without SSL first):"
echo "   docker-compose up -d nginx"
echo ""
echo "6. Get SSL certificate:"
echo "   docker-compose run --rm certbot certonly --webroot -w /var/www/certbot -d tesla.powell.at --email your@email.com --agree-tos --no-eff-email"
echo ""
echo "7. Restart nginx with SSL:"
echo "   docker-compose restart nginx"
echo ""

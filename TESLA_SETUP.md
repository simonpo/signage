# Tesla Fleet API HTTPS Setup Guide

## Overview
We need to host your Tesla public key at `https://tesla.powell.at/.well-known/appspecific/com.tesla.3p.public-key.pem` for the Fleet API registration.

## Prerequisites
- Proxmox server with Docker/Docker Compose
- Your public IP address
- Access to EuroDNS to configure DNS
- Access to your router for port forwarding

## Step-by-Step Setup

### 1. Transfer Files to Proxmox

From your Mac, copy the setup script and public key to your Proxmox server:

```bash
# Get your Proxmox server IP (replace with actual IP)
PROXMOX_IP="192.168.1.XXX"

# Copy setup script
scp tesla-nginx-setup.sh root@$PROXMOX_IP:~/

# Copy public key
scp tesla_public_key.pem root@$PROXMOX_IP:~/
```

### 2. Run Setup Script on Proxmox

SSH into your Proxmox server:

```bash
ssh root@$PROXMOX_IP
```

Run the setup script:

```bash
cd ~
chmod +x tesla-nginx-setup.sh
./tesla-nginx-setup.sh
```

Copy the public key to the correct location:

```bash
cp ~/tesla_public_key.pem ~/tesla-api/well-known/appspecific/com.tesla.3p.public-key.pem
```

### 3. Get Your Public IP

On Proxmox:

```bash
curl -4 ifconfig.me
```

Note this IP address (e.g., `123.45.67.89`)

### 4. Configure DNS at EuroDNS

1. Log in to https://www.eurodns.com
2. Go to your domain `powell.at`
3. Add a new DNS record:
   - **Type**: A
   - **Name**: tesla
   - **Value**: [Your public IP from step 3]
   - **TTL**: 3600 (1 hour)
4. Save changes

DNS propagation may take a few minutes to a few hours.

### 5. Configure Router Port Forwarding

Access your router's admin panel and add these port forwarding rules:

- **External Port 80** → **Proxmox IP:80** (for Let's Encrypt verification)
- **External Port 443** → **Proxmox IP:443** (for HTTPS)

Example:
- External: 80 → Internal: 192.168.1.XXX:80
- External: 443 → Internal: 192.168.1.XXX:443

### 6. Start nginx (HTTP Only First)

On Proxmox:

```bash
cd ~/tesla-api
docker-compose up -d nginx
```

Verify it's running:

```bash
docker-compose ps
```

Test from your Mac:

```bash
curl http://tesla.powell.at/
# Should return: "Tesla Fleet API - OK"
```

### 7. Get SSL Certificate

On Proxmox, run certbot (replace YOUR_EMAIL):

```bash
cd ~/tesla-api
docker-compose run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d tesla.powell.at \
  --email YOUR_EMAIL@example.com \
  --agree-tos \
  --no-eff-email
```

If successful, restart nginx to load the certificate:

```bash
docker-compose restart nginx
```

### 8. Verify HTTPS Setup

Test from your Mac:

```bash
# Test HTTPS
curl https://tesla.powell.at/

# Test public key endpoint
curl https://tesla.powell.at/.well-known/appspecific/com.tesla.3p.public-key.pem
```

The second command should display your public key starting with `-----BEGIN PUBLIC KEY-----`

### 9. Update Tesla Developer Dashboard

1. Go to: https://developer.tesla.com/dashboard/app-details/4aa15211-345c-4369-a0f9-ac6046390160
2. Find "Allowed Origins" field
3. Add: `https://tesla.powell.at`
4. Save changes

### 10. Register with Tesla Fleet API

Back on your Mac:

```bash
cd ~/code/signage
python register_tesla.py
```

You should see: `✓ Registration successful!`

### 11. Test Tesla Integration

```bash
python ./generate_signage.py --source tesla --html
```

## Troubleshooting

### DNS not resolving
```bash
# Check DNS propagation
dig tesla.powell.at
nslookup tesla.powell.at
```

### Port forwarding not working
```bash
# Test from outside your network (use mobile hotspot or online tool)
curl http://[YOUR_PUBLIC_IP]
```

### Certificate issues
```bash
# Check nginx logs
docker-compose logs nginx

# Check certbot logs
docker-compose logs certbot
```

### Public key not accessible
```bash
# Verify file exists in container
docker exec tesla-nginx ls -la /usr/share/nginx/html/.well-known/appspecific/

# Check nginx config
docker exec tesla-nginx nginx -t
```

## Maintenance

### Certificate Auto-Renewal

The certbot container automatically renews certificates every 12 hours. No manual intervention needed!

### Check Certificate Expiry

```bash
echo | openssl s_client -servername tesla.powell.at -connect tesla.powell.at:443 2>/dev/null | openssl x509 -noout -dates
```

### Update Public Key

If you ever need to update the public key:

```bash
# On Proxmox
cd ~/tesla-api
cp /path/to/new_key.pem well-known/appspecific/com.tesla.3p.public-key.pem
# nginx will serve the updated file immediately
```

## Quick Reference

**nginx container**: `docker exec -it tesla-nginx sh`
**View logs**: `docker-compose logs -f nginx`
**Restart**: `docker-compose restart nginx`
**Stop**: `docker-compose down`
**Start**: `docker-compose up -d`


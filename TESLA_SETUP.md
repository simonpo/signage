# Tesla Fleet API Setup with Caddy

⚠️ **IMPORTANT**: Tesla **prohibits** using "tesla" in your domain name. Use a generic subdomain like `api`, `fleet`, or `ev` instead.

## Overview

We need to host your Tesla public key at `https://api.powell.at/.well-known/appspecific/com.tesla.3p.public-key.pem` for the Fleet API registration.

**Why Caddy?** Automatic HTTPS with Let's Encrypt - no manual certificate management needed!

## Prerequisites

- Proxmox server with Docker/Docker Compose
- Your public IP address
- Access to EuroDNS to configure DNS
- Access to OPNsense for port forwarding (see `TESLA_SETUP_OPNSENSE.md`)

## Step-by-Step Setup

### 1. Transfer Files to Proxmox

From your Mac, copy the setup script and public key to your Proxmox server:

```bash
# Get your Proxmox server IP (replace with actual IP)
PROXMOX_IP="192.168.1.XXX"

# Copy setup script
scp tesla-caddy-setup.sh root@$PROXMOX_IP:~/

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
chmod +x tesla-caddy-setup.sh
./tesla-caddy-setup.sh
```

### 3. Configure Your Domain in Caddyfile

Edit the Caddyfile to use your actual domain:

```bash
cd ~/tesla-api
nano Caddyfile
```

Replace `api.powell.at` with your actual domain (e.g., `api.yourdomain.com`).

⚠️ Remember: Do NOT use "tesla" in the domain name!

### 4. Copy Public Key

```bash
cp ~/tesla_public_key.pem ~/tesla-api/well-known/appspecific/com.tesla.3p.public-key.pem
```

### 5. Get Your Public IP

```bash
curl -4 ifconfig.me
```

Note this IP address (e.g., `123.45.67.89`)

### 6. Configure DNS at EuroDNS

1. Log in to https://www.eurodns.com
2. Go to your domain `powell.at`
3. Add a new DNS record:
   - **Type**: A
   - **Name**: api (⚠️ do NOT use "tesla" - prohibited by Tesla)
   - **Value**: [Your public IP from step 5]
   - **TTL**: 3600 (1 hour)
4. Save changes

DNS propagation may take 5-30 minutes.

### 7. Configure OPNsense Port Forwarding

Follow the detailed instructions in `TESLA_SETUP_OPNSENSE.md` to set up port forwarding for:
- Port 80 (HTTP) - for ACME challenges
- Port 443 (HTTPS) - for Tesla API

### 8. Start Caddy

```bash
cd ~/tesla-api
docker-compose up -d
```

Caddy will automatically:
- Start serving on ports 80 and 443
- Request an SSL certificate from Let's Encrypt
- Renew the certificate automatically

Check logs to ensure SSL cert was obtained:

```bash
docker-compose logs -f caddy
```

You should see: `certificate obtained successfully`

### 9. Test the Setup

```bash
# Test HTTP redirect
curl -I http://api.powell.at/
# Should return 301 or 308 redirect to HTTPS

# Test HTTPS endpoint
curl https://api.powell.at/
# Should return: "Tesla Fleet API - OK"

# Test public key endpoint
curl https://api.powell.at/.well-known/appspecific/com.tesla.3p.public-key.pem
# Should display your public key starting with -----BEGIN PUBLIC KEY-----
```

### 10. Update Tesla Developer Dashboard

1. Go to: https://developer.tesla.com/dashboard (your app details)
2. Find "Allowed Origins"
3. Add: `https://api.powell.at` (⚠️ do NOT use "tesla" in the domain - Tesla prohibits it)
4. Save changes

### 11. Register with Tesla Fleet API

Back on your Mac:

```bash
cd ~/code/signage
python register_tesla.py
```

You should see: `✓ Registration successful!`

### 12. Test Tesla Integration

```bash
python ./generate_signage.py --source tesla --html
```

## Troubleshooting

### DNS not resolving

```bash
# Check DNS propagation
dig api.powell.at
nslookup api.powell.at
```

### Port forwarding not working

```bash
# Test from outside your network (use mobile hotspot or online tool)
curl http://[YOUR_PUBLIC_IP]
```

### Caddy SSL certificate issues

```bash
# Check Caddy logs
docker-compose logs caddy

# Common issues:
# 1. DNS not propagated yet - wait 10-30 minutes
# 2. Ports 80/443 not forwarded correctly
# 3. Another service already using ports 80/443

# Restart Caddy
docker-compose restart caddy
```

### Can't access from inside network

This is likely a NAT hairpinning issue. Add a DNS override in OPNsense:
- Go to **Services → Unbound DNS → Overrides**
- Add Host Override:
  - Host: api
  - Domain: powell.at
  - IP: [Proxmox internal IP]

### Certificate not auto-renewing

Caddy automatically renews certificates. Check renewal status:

```bash
docker-compose logs caddy | grep renew
```

### Update Public Key

If you ever need to update the public key:

```bash
# On Proxmox
cd ~/tesla-api
cp /path/to/new_key.pem well-known/appspecific/com.tesla.3p.public-key.pem
# Caddy will serve the updated file immediately - no restart needed
```

## Maintenance

### View Caddy Logs

```bash
cd ~/tesla-api
docker-compose logs -f caddy
```

### Restart Caddy

```bash
cd ~/tesla-api
docker-compose restart caddy
```

### Stop Caddy

```bash
cd ~/tesla-api
docker-compose down
```

### Update Caddy

```bash
cd ~/tesla-api
docker-compose pull
docker-compose up -d
```

## Advantages of Caddy

✅ **Automatic HTTPS** - No certbot, no manual certificate management  
✅ **Auto-renewal** - Certificates renew automatically  
✅ **Simple configuration** - One Caddyfile instead of multiple nginx configs  
✅ **Secure by default** - Modern TLS settings out of the box  
✅ **No scripting** - Everything configured declaratively  

## Files Reference

- `TESLA_SETUP_OPNSENSE.md` - OPNsense port forwarding configuration
- `TESLA_SETUP_COMPARISON.md` - Comparison of different setup methods
- `tesla-caddy-setup.sh` - Automated setup script for Proxmox
- `tesla_public_key.pem` - Your public key (keep secure)
- `tesla_private_key.pem` - Your private key (NEVER share this)

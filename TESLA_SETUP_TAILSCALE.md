# Tesla Fleet API Setup with Tailscale Funnel (RECOMMENDED)

## Why Tailscale Funnel?

✅ **No port forwarding needed**
✅ **Automatic HTTPS certificate** (via Tailscale)
✅ **No router configuration**
✅ **No DNS setup at EuroDNS**
✅ **Simpler and more secure**

Tailscale Funnel exposes specific services to the public internet with automatic HTTPS.

## Prerequisites

- Proxmox server (or any Linux server/VM)
- Tailscale account (free tier is fine)

## Setup Steps

### 1. Install Tailscale on Proxmox

SSH into your Proxmox server:

```bash
ssh root@YOUR_PROXMOX_IP
```

Install Tailscale:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

Start Tailscale and authenticate:

```bash
tailscale up
```

This will give you a URL to visit in your browser to authenticate.

### 2. Enable HTTPS

Enable HTTPS for your Tailscale node:

```bash
tailscale cert $(tailscale status --json | jq -r '.Self.DNSName' | sed 's/\.$//')
```

Your node will get a certificate for a hostname like: `your-machine-name.tailXXXX.ts.net`

### 3. Create Simple nginx Setup

Create directory and files:

```bash
mkdir -p ~/tesla-api/well-known/appspecific
cd ~/tesla-api
```

Create `docker-compose.yml`:

```yaml
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
```

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-pem;

    server {
        listen 443 ssl http2;
        server_name _;

        # Tailscale automatically provides certs in /var/lib/tailscale/certs/
        ssl_certificate /etc/nginx/certs/YOUR_HOSTNAME.crt;
        ssl_certificate_key /etc/nginx/certs/YOUR_HOSTNAME.key;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

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
```

Replace `YOUR_HOSTNAME` with your actual Tailscale hostname:

```bash
HOSTNAME=$(tailscale status --json | jq -r '.Self.DNSName' | sed 's/\.$//')
echo "Your hostname is: $HOSTNAME"
sed -i "s/YOUR_HOSTNAME/$HOSTNAME/g" nginx.conf
```

### 4. Copy Public Key

From your Mac, copy the public key:

```bash
scp tesla_public_key.pem root@YOUR_PROXMOX_IP:~/tesla-api/well-known/appspecific/com.tesla.3p.public-key.pem
```

### 5. Start nginx

On Proxmox:

```bash
cd ~/tesla-api
docker-compose up -d
```

### 6. Enable Tailscale Funnel

Enable Funnel to expose port 8443 to the public internet:

```bash
tailscale funnel 8443
```

This creates a public HTTPS endpoint at `https://your-machine-name.tailXXXX.ts.net/`

### 7. Test Public Access

From your Mac (or any device NOT on Tailscale):

```bash
curl https://your-machine-name.tailXXXX.ts.net/
# Should return: "Tesla Fleet API - OK"

curl https://your-machine-name.tailXXXX.ts.net/.well-known/appspecific/com.tesla.3p.public-key.pem
# Should show your public key
```

### 8. Update Tesla Developer Dashboard

1. Go to: https://developer.tesla.com/dashboard/app-details/4aa15211-345c-4369-a0f9-ac6046390160
2. Find "Allowed Origins"
3. Add: `https://your-machine-name.tailXXXX.ts.net` (your actual hostname)
4. Save changes

### 9. Update Register Script

On your Mac, update the domain in register_tesla.py:

Change this line:
```python
payload = {"domain": "tesla.powell.at"}
```

To:
```python
payload = {"domain": "your-machine-name.tailXXXX.ts.net"}
```

### 10. Register with Tesla Fleet API

```bash
cd ~/code/signage
python register_tesla.py
```

Should see: `✓ Registration successful!`

### 11. Test Tesla Integration

```bash
python ./generate_signage.py --source tesla --html
```

## Advantages of Tailscale Funnel

- **Zero configuration** on router/firewall
- **Automatic HTTPS** - no Let's Encrypt setup
- **Automatic certificate renewal**
- **Built-in DDoS protection**
- **Can disable public access instantly** with `tailscale funnel --bg=false`
- **Works from anywhere** without VPN

## Troubleshooting

### Check Tailscale status
```bash
tailscale status
```

### Check Funnel status
```bash
tailscale funnel status
```

### View nginx logs
```bash
docker-compose logs -f nginx
```

### Disable Funnel (make private again)
```bash
tailscale funnel --bg=false 8443
```

### Re-enable Funnel
```bash
tailscale funnel --bg 8443
```

## Quick Reference

**Your public URL**: `https://$(tailscale status --json | jq -r '.Self.DNSName' | sed 's/\.$//')/`
**Enable Funnel**: `tailscale funnel 8443`
**Disable Funnel**: `tailscale funnel --bg=false 8443`
**Check status**: `tailscale funnel status`


# Tesla Fleet API HTTPS Setup - Method Comparison

## Quick Comparison

| Feature | Tailscale Funnel ⭐ | Traditional (OPNsense + Let's Encrypt) |
|---------|---------------------|----------------------------------------|
| **Setup Time** | ~15 minutes | ~45-60 minutes |
| **Complexity** | Low | Medium-High |
| **Port Forwarding** | Not needed | Required (80, 443) |
| **OPNsense Config** | None | NAT rules, firewall rules |
| **DNS Config** | None | Required (EuroDNS A record) |
| **SSL Certificate** | Automatic (Tailscale) | Manual (Let's Encrypt) |
| **Certificate Renewal** | Automatic | Automatic (certbot) |
| **Public IP Required** | No | Yes |
| **Security** | Excellent (Tailscale network) | Good (depends on config) |
| **Firewall Exposure** | Minimal | Ports 80 & 443 exposed |
| **Cost** | Free | Free |
| **Can disable quickly** | Yes (1 command) | No (requires firewall changes) |

## Recommendation: Use Tailscale Funnel

**Why?**
- ✅ Zero OPNsense configuration needed
- ✅ No port forwarding vulnerabilities
- ✅ Automatic HTTPS with no certificate management
- ✅ Can enable/disable public access instantly
- ✅ No DNS configuration at EuroDNS
- ✅ Works even if your ISP blocks ports 80/443

**When to use Traditional setup?**
- You want to use your own domain (tesla.powell.at)
- You don't want to depend on Tailscale
- You need more control over the web server

## Step-by-Step for Tailscale (Recommended)

Follow: `TESLA_SETUP_TAILSCALE.md`

**Summary:**
1. Install Tailscale on Proxmox (2 min)
2. Enable HTTPS certs (1 min)
3. Create nginx container (5 min)
4. Copy public key (2 min)
5. Enable Funnel (1 min)
6. Update Tesla dashboard (2 min)
7. Register and test (2 min)

**Total: ~15 minutes**

## Step-by-Step for Traditional Setup

Follow: `TESLA_SETUP_OPNSENSE.md` + `TESLA_SETUP.md`

**Summary:**
1. Configure OPNsense port forwarding (10 min)
2. Configure DNS at EuroDNS (5 min)
3. Wait for DNS propagation (10-30 min)
4. Set up nginx on Proxmox (10 min)
5. Get Let's Encrypt certificate (5 min)
6. Update Tesla dashboard (2 min)
7. Register and test (2 min)

**Total: ~45-60 minutes** (plus DNS wait time)

## Security Comparison

### Tailscale Funnel Security
- Only specific port exposed (8443)
- Traffic goes through Tailscale's infrastructure
- Built-in DDoS protection
- Can disable in 1 second if needed
- No attack surface on your home network

### Traditional Security
- Ports 80 & 443 exposed to internet
- Direct connection to your home network
- Requires OPNsense firewall hardening
- Potential attack vector if nginx misconfigured
- Rate limiting recommended

## My Recommendation

**For your use case (personal Tesla API access):**

→ **Use Tailscale Funnel**

Reasons:
1. You're only hosting a static public key file
2. You don't need the traffic to hit your home network
3. Setup is dramatically simpler
4. No OPNsense configuration needed
5. Can disable instantly if you ever want to
6. More secure (minimal exposure)

The only downside is you'll get a Tailscale hostname like `proxmox.tail12345.ts.net` instead of `tesla.powell.at`, but Tesla doesn't care - it just needs HTTPS access to the public key.

## Files You Need

### For Tailscale Setup:
- `TESLA_SETUP_TAILSCALE.md` - Complete guide
- `tesla_public_key.pem` - Your public key

### For Traditional Setup:
- `TESLA_SETUP_OPNSENSE.md` - OPNsense configuration
- `TESLA_SETUP.md` - nginx and Let's Encrypt setup
- `tesla-nginx-setup.sh` - Automated setup script
- `tesla_public_key.pem` - Your public key


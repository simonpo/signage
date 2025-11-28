# Tesla Fleet API Setup with OPNsense (RECOMMENDED)

This is the **recommended approach** for Tesla Fleet API OAuth2 authentication. It provides full control, uses your own domain, and is the most reliable solution for production use.

## Why OPNsense + Port Forwarding Works Best

✅ **OAuth2 Compatible** - Browsers can reach your callback URL  
✅ **Your Own Domain** - Use `tesla.powell.at` instead of random URLs  
✅ **Full Control** - No third-party dependencies  
✅ **Reliable** - No tunneling services that can go down  
✅ **Permanent** - Set it once, works forever  
✅ **Secure** - Enterprise-grade firewall protection  

## Prerequisites

- OPNsense firewall/router
- Public static IP (or dynamic DNS)
- Domain name (e.g., `powell.at`)
- Proxmox server (or any Linux server) for nginx

## Overview

1. Configure OPNsense to forward ports 80 & 443 to your Proxmox server
2. Set up DNS A record pointing to your public IP
3. Install nginx to serve the Tesla public key
4. Get Let's Encrypt SSL certificate
5. Test and register with Tesla

## OPNsense Port Forwarding Configuration

### Step 1: Access OPNsense Web Interface

1. Open browser and go to your OPNsense IP (e.g., `https://192.168.1.1`)
2. Log in with admin credentials

### Step 2: Configure Port Forward Rules

Navigate to: **Firewall → NAT → Port Forward**

#### Rule 1: HTTP (Port 80) - For Let's Encrypt

Click **Add** (+ icon) and configure:

- **Interface**: WAN
- **TCP/IP Version**: IPv4
- **Protocol**: TCP
- **Source**: any
- **Source Port**: any
- **Destination**: WAN address
- **Destination Port**: 80 (HTTP)
- **Redirect target IP**: [Your Proxmox IP, e.g., 192.168.1.50]
- **Redirect target port**: 80
- **Description**: Tesla API - Let's Encrypt (HTTP)
- **NAT reflection**: Enable
- **Filter rule association**: Add associated filter rule

Click **Save**

#### Rule 2: HTTPS (Port 443) - For Tesla API

Click **Add** (+ icon) and configure:

- **Interface**: WAN
- **TCP/IP Version**: IPv4
- **Protocol**: TCP
- **Source**: any
- **Source Port**: any
- **Destination**: WAN address
- **Destination Port**: 443 (HTTPS)
- **Redirect target IP**: [Your Proxmox IP, e.g., 192.168.1.50]
- **Redirect target port**: 443
- **Description**: Tesla API - HTTPS
- **NAT reflection**: Enable
- **Filter rule association**: Add associated filter rule

Click **Save**

### Step 3: Apply Changes

Click **Apply changes** at the top of the page

### Step 4: Verify Firewall Rules

Navigate to: **Firewall → Rules → WAN**

You should see two new rules:
- NAT Tesla API - Let's Encrypt (HTTP) - Port 80
- NAT Tesla API - HTTPS - Port 443

Both should be **enabled** (green checkmark)

## DNS Configuration at EuroDNS

1. Log in to https://www.eurodns.com
2. Select your domain `powell.at`
3. Go to DNS settings
4. Add new A record:
   - **Type**: A
   - **Name**: tesla
   - **Value**: [Your public IP - get with `curl -4 ifconfig.me`]
   - **TTL**: 3600
5. Save changes

Wait 5-10 minutes for DNS propagation

## Verify Setup

### Test Port Forwarding

From outside your network (mobile hotspot or https://www.yougetsignal.com/tools/open-ports/):

```bash
# Check if port 80 is open
telnet YOUR_PUBLIC_IP 80

# Check if port 443 is open
telnet YOUR_PUBLIC_IP 443
```

### Test DNS Resolution

```bash
dig tesla.powell.at
# Should return your public IP

nslookup tesla.powell.at
# Should return your public IP
```

## Continue with nginx Setup

Once port forwarding and DNS are working, follow the main guide: `TESLA_SETUP.md`

Starting from Step 6: "Start nginx (HTTP Only First)"

## Troubleshooting OPNsense

### Port forward not working

1. **Check WAN interface**:
   - Go to **Interfaces → WAN**
   - Ensure interface is up and has public IP

2. **Check firewall logs**:
   - Go to **Firewall → Log Files → Live View**
   - Look for blocked connections on ports 80/443

3. **Disable packet filtering on bridge** (if using VLANs):
   - Go to **System → Settings → Tunables**
   - Find `net.link.bridge.pfil_bridge`
   - Set to `0`
   - Reboot OPNsense

4. **Check NAT reflection**:
   - Go to **Firewall → Settings → Advanced**
   - Ensure "Reflection for port forwards" is enabled

5. **Check associated filter rules**:
   - Go to **Firewall → Rules → WAN**
   - Ensure auto-created rules for NAT are **above** any block rules

### DNS not resolving

1. **Check DNS propagation**:
   ```bash
   # Use Google DNS
   nslookup tesla.powell.at 8.8.8.8
   
   # Use Cloudflare DNS
   nslookup tesla.powell.at 1.1.1.1
   ```

2. **Clear local DNS cache** (on Mac):
   ```bash
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```

### Can't access from inside network

This is NAT hairpinning/loopback issue. Enable **NAT reflection** in the port forward rules.

Or add a DNS override in OPNsense:
- Go to **Services → Unbound DNS → Overrides**
- Add Host Override:
  - **Host**: tesla
  - **Domain**: powell.at
  - **IP**: [Proxmox internal IP, e.g., 192.168.1.50]

## Security Considerations

### Firewall Rules Best Practices

1. **Limit source IPs** (if you know Tesla's IP ranges):
   - Edit port forward rules
   - Set **Source** to specific IP ranges instead of "any"
   - Tesla uses AWS - check their IP ranges

2. **Enable intrusion detection**:
   - Go to **Services → Intrusion Detection**
   - Enable IDS/IPS
   - Select "ET open" ruleset

3. **Monitor logs regularly**:
   - Go to **Firewall → Log Files**
   - Check for unusual access patterns

### Rate Limiting (Optional)

To prevent abuse:

1. Go to **Firewall → Shaper**
2. Create pipe for Tesla API traffic
3. Set bandwidth limits
4. Apply to WAN rules

## Quick Reference - OPNsense Commands

**Restart firewall**:
```bash
# SSH to OPNsense
/etc/rc.filter_configure
```

**View active states**:
```bash
pfctl -s state | grep ":443"
```

**View NAT rules**:
```bash
pfctl -s nat
```

**Test from OPNsense**:
```bash
# Test outbound (from OPNsense to internet)
curl -I https://tesla.powell.at

# Test port forward (from OPNsense to Proxmox)
nc -zv [PROXMOX_IP] 443
```


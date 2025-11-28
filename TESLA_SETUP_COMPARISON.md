# Tesla Fleet API HTTPS Setup - Method Comparison

⚠️ **IMPORTANT**: Tesla **prohibits** using "tesla" in your domain name per their [Brand Guidelines](https://www.tesla.com/brand-guidelines). Use generic subdomains like `api`, `fleet`, or `ev` instead.

## Why OAuth Callbacks Require Public Access

Tesla's OAuth2 authentication flow has a critical requirement: **Tesla's servers must be able to redirect your browser to your callback URL**. This means:

1. Your redirect URI must be **publicly accessible** from the internet
2. The URL must work in a **browser context** (not just API calls)
3. Tesla's authorization server needs to send the OAuth code to your endpoint

❌ **This rules out:**
- Tailscale Funnel (browsers can't reach Tailscale URLs without Tailscale installed)
- Any private network solution
- Localhost/127.0.0.1
- VPN-only endpoints

✅ **What actually works:**
- Public IP with port forwarding (OPNsense setup)
- Cloudflare Tunnel
- ngrok or similar tunneling services
- Public VPS with reverse proxy

## Quick Comparison

| Feature | OPNsense + Let's Encrypt ⭐ | Cloudflare Tunnel | ngrok (Free) | Public VPS |
|---------|----------------------------|-------------------|--------------|------------|
| **Works with OAuth** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Setup Time** | ~45-60 minutes | ~20 minutes | ~5 minutes | ~60 minutes |
| **Complexity** | Medium-High | Medium | Low | High |
| **Port Forwarding** | Required (80, 443) | Not needed | Not needed | Not needed |
| **Router Config** | Required | None | None | None |
| **DNS Config** | Required (EuroDNS) | Required | Auto (random URL) | Required |
| **SSL Certificate** | Manual setup | Automatic | Automatic | Manual |
| **Cost** | Free | Free | Free (with limits) | $5-20/month |
| **Permanent URL** | Yes (your domain) | Yes (your domain) | No (changes) | Yes (your domain) |
| **Reliability** | Excellent | Excellent | Good | Excellent |
| **Your Control** | Full | Limited | None | Full |

## Recommendation: OPNsense + Let's Encrypt (Current Setup)

**Why this is the best for your use case:**

✅ **You already have it working** - No need to change  
✅ **Uses your own domain** - `api.powell.at` (⚠️ Tesla prohibits "tesla" in domain names)  
✅ **Full control** - All traffic stays in your network  
✅ **No third-party dependencies** - Doesn't rely on Cloudflare/ngrok  
✅ **Permanent setup** - Set it and forget it  
✅ **OPNsense security** - Enterprise-grade firewall protection  

**The only downsides:**
- Initial setup complexity (but you've already done it)
- Exposes ports 80 & 443 (but that's standard for any web service)

## Alternative Options (If You Want to Change)

### Option 1: Cloudflare Tunnel (Zero Trust)

**Pros:**
- No port forwarding needed
- Free SSL certificate
- DDoS protection included
- Can use your domain

**Cons:**
- Depends on Cloudflare service
- More complex DNS setup
- Traffic goes through Cloudflare's network

**Setup time:** ~20 minutes

### Option 2: ngrok (Temporary/Testing)

**Pros:**
- Extremely fast setup
- No router configuration
- Good for testing

**Cons:**
- Free tier changes URL on restart
- Not reliable for production
- Rate limits on free tier
- Requires ngrok running 24/7

**Setup time:** ~5 minutes

### Option 3: Public VPS (Advanced)

**Pros:**
- Full control
- No home network exposure
- Can run other services

**Cons:**
- Monthly cost ($5-20)
- Requires VPS management
- More complexity
- Reverse proxy setup needed

**Setup time:** ~60 minutes

## What Doesn't Work for OAuth

### ❌ Tailscale Funnel
**Problem:** Browsers can't reach Tailscale URLs without Tailscale client installed. Tesla's OAuth redirect happens in the browser, which doesn't have Tailscale.

**Why it seemed like it would work:** Tailscale Funnel *does* create a public HTTPS endpoint, but it's only accessible if you have Tailscale. The OAuth flow fails because:
1. Tesla redirects browser to `https://your-machine.tail12345.ts.net/callback`
2. Browser tries to resolve `*.ts.net` → fails (no Tailscale DNS)
3. OAuth flow breaks

### ❌ VPN Solutions
Same problem - requires client software to access the endpoint.

### ❌ Localhost Tunnels (Basic)
Without a service like ngrok, localhost isn't publicly routable.

## Files You Need

### For OPNsense Setup (Recommended):
- `TESLA_SETUP_OPNSENSE.md` - OPNsense port forwarding configuration
- `TESLA_SETUP.md` - Caddy and automatic HTTPS setup
- `tesla-caddy-setup.sh` - Automated setup script
- `tesla_public_key.pem` - Your public key

### For Alternative Setups:
- See respective service documentation (Cloudflare, ngrok, VPS providers)

## Bottom Line

**Your current OPNsense + Let's Encrypt setup is the right choice.** 

It's battle-tested, reliable, uses your own domain, and gives you full control. The setup complexity was a one-time cost, and now it just works.

If you ever need to change it, Cloudflare Tunnel would be the next best option (no port forwarding, still uses your domain), but there's no compelling reason to switch from what you have.


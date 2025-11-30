# Docker Deployment Guide

This guide covers running the Samsung Frame TV Signage system using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/signage.git
cd signage

# 2. Configure environment
cp .env.example .env
nano .env  # Add your API keys and configuration

# 3. Start the service
docker-compose up -d

# 4. View logs
docker-compose logs -f

# 5. Check status
docker-compose ps
```

## Installation on Different Platforms

### Proxmox LXC (Recommended)

```bash
# 1. Create Ubuntu 22.04 LXC container in Proxmox UI
# 2. Enable "Features → Nesting" in container options
# 3. Start container and connect via console

# 4. Install Docker
apt update && apt install -y docker.io docker-compose git

# 5. Enable Docker service
systemctl enable docker
systemctl start docker

# 6. Clone and configure
git clone https://github.com/yourusername/signage.git
cd signage
cp .env.example .env
nano .env  # Configure your API keys

# 7. Start service
docker-compose up -d
```

### Proxmox VM

```bash
# Same as LXC, but create a full Ubuntu VM instead
# No need to enable nesting feature
```

### Raspberry Pi

```bash
# Install Docker (one-time setup)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker pi

# Logout and login again, then:
cd signage
docker-compose up -d
```

### Synology NAS

1. Install "Container Manager" package from Package Center
2. Enable SSH and connect to NAS
3. Clone repository to a shared folder
4. Use Container Manager UI or SSH to run `docker-compose up -d`

## Directory Structure

```
signage/
├── .env                    # Your configuration (not in git)
├── docker-compose.yml      # Service definition
├── Dockerfile             # Image definition
├── art_folder/            # Generated images (mounted volume)
├── backgrounds/           # Background images (mounted read-only)
└── .cache/               # API cache (mounted volume)
```

## Configuration

### Environment Variables

All configuration is done via `.env` file (not committed to git):

```bash
# Required
WEATHER_API_KEY=your_openweather_key
WEATHER_CITY=Seattle,US

# Optional data sources
TESLA_CLIENT_ID=your_client_id
TESLA_CLIENT_SECRET=your_client_secret
STOCK_SYMBOL=AAPL
STOCK_API_KEY=your_alphavantage_key

# System settings
TIMEZONE=US/Pacific
LOG_LEVEL=INFO
ENABLE_DAEMON_MODE=true
```

### Volumes

Docker Compose mounts these directories:

- `./art_folder` → Generated signage images (persistent)
- `./backgrounds` → Your background images (read-only)
- `./.cache` → API response cache (persistent)

### Resource Limits

By default, no resource limits are set. To add limits, uncomment the `deploy` section in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## Common Operations

### View Logs

```bash
# Follow logs in real-time
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# View logs for specific time
docker-compose logs --since 30m
```

### Restart Service

```bash
# Restart container
docker-compose restart

# Stop and remove container
docker-compose down

# Start fresh
docker-compose up -d
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# View new logs
docker-compose logs -f
```

### Run One-Time Generation

```bash
# Generate Tesla signage once
docker-compose run --rm signage python generate_signage.py --source tesla

# Generate all signage (non-daemon)
docker-compose run --rm signage python generate_signage.py --source all
```

### Access Container Shell

```bash
# Open bash shell in running container
docker-compose exec signage bash

# Run commands inside container
docker-compose exec signage python --version
docker-compose exec signage ls -la /app/art_folder
```

## Monitoring

### Health Checks

Docker automatically monitors container health:

```bash
# Check health status
docker-compose ps

# View health check logs
docker inspect signage-generator | jq '.[0].State.Health'
```

Healthy container shows:
```
NAME                  IMAGE            STATUS
signage-generator     signage:latest   Up 2 hours (healthy)
```

### Resource Usage

```bash
# View resource usage
docker stats signage-generator

# Shows: CPU%, MEM USAGE / LIMIT, MEM %, NET I/O, BLOCK I/O
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs

# Check if ports are already in use
docker-compose ps

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Missing API Keys

```bash
# Validate .env file
docker-compose config

# Check environment variables in container
docker-compose exec signage env | grep -E '(TESLA|WEATHER|STOCK)'
```

### Permission Issues

```bash
# Fix ownership of mounted directories
sudo chown -R $USER:$USER art_folder backgrounds .cache

# Restart container
docker-compose restart
```

### Image Generation Not Working

```bash
# Check if daemon mode is enabled
docker-compose exec signage env | grep ENABLE_DAEMON_MODE

# Run manual generation
docker-compose exec signage python generate_signage.py --source all

# Check for errors
docker-compose logs --tail=50
```

### High Resource Usage

```bash
# Check resource consumption
docker stats signage-generator

# Add resource limits (see Configuration section)
# Reduce update frequency in .env
```

## Advanced Usage

### Custom Command

Override the default daemon command:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  signage:
    command: python generate_signage.py --source tesla --html
```

### Development Mode

Mount source code as volume for live editing:

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  signage:
    volumes:
      - ./src:/app/src:ro
      - ./generate_signage.py:/app/generate_signage.py:ro
```

Run with: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`

### Multiple Instances

Run separate instances for different TVs:

```bash
# TV 1 (living room)
docker-compose -f docker-compose.yml -p signage-living up -d

# TV 2 (bedroom)
docker-compose -f docker-compose.bedroom.yml -p signage-bedroom up -d
```

## Backup and Restore

### Backup

```bash
# Backup generated images
tar -czf signage-backup-$(date +%Y%m%d).tar.gz art_folder/

# Backup configuration
cp .env .env.backup
```

### Restore

```bash
# Restore images
tar -xzf signage-backup-20241129.tar.gz

# Restore configuration
cp .env.backup .env
docker-compose restart
```

## Uninstall

```bash
# Stop and remove containers
docker-compose down

# Remove images
docker rmi signage:latest

# Remove volumes (WARNING: deletes generated images)
docker volume prune

# Remove directories
cd ..
rm -rf signage/
```

## Getting Help

- Check logs: `docker-compose logs -f`
- Validate config: `docker-compose config`
- GitHub Issues: https://github.com/yourusername/signage/issues
- Docker docs: https://docs.docker.com/

## Performance Tips

1. **Use LXC instead of VM** on Proxmox for better performance
2. **Enable nesting** in LXC container features
3. **Add resource limits** to prevent runaway processes
4. **Use SSD storage** for art_folder if possible
5. **Reduce update frequency** for less active data sources
6. **Monitor logs** for slow API calls

## Security Notes

- `.env` file contains secrets - never commit to git
- Container runs as root by default (isolated from host)
- Background images are mounted read-only
- No ports are exposed (output-only service)
- Health checks don't expose sensitive data

## Next Steps

After Docker deployment is working:
- Configure automatic backups
- Set up monitoring/alerting
- Tune resource limits
- Optimize update schedules
- Add additional data sources

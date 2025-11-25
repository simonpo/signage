#!/bin/bash
# Setup cron jobs for signage generation

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up signage cron jobs...${NC}"

# Detect project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Project directory: $PROJECT_DIR"

# Detect Python executable (prefer venv if it exists)
if [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/venv/bin/python"
    echo "Using virtual environment Python"
elif command -v python3 &> /dev/null; then
    PYTHON=$(command -v python3)
elif command -v python &> /dev/null; then
    PYTHON=$(command -v python)
else
    echo "Error: Python not found"
    exit 1
fi

echo "Python executable: $PYTHON"

# Log file
LOG_FILE="$PROJECT_DIR/signage.log"

# Remove old signage cron jobs
echo -e "${YELLOW}Removing old signage cron jobs...${NC}"
crontab -l 2>/dev/null | grep -v "generate_signage.py" | crontab - || true

# Prepare new cron jobs
CRON_JOBS=$(mktemp)

# Keep existing cron jobs
crontab -l 2>/dev/null > "$CRON_JOBS" || true

# Add new signage jobs
echo "" >> "$CRON_JOBS"
echo "# Signage generation jobs" >> "$CRON_JOBS"

# Weather: Every 30 minutes
echo "*/30 * * * * cd $PROJECT_DIR && $PYTHON generate_signage.py --source weather >> $LOG_FILE 2>&1" >> "$CRON_JOBS"

# Tesla: Every 15 minutes
echo "*/15 * * * * cd $PROJECT_DIR && $PYTHON generate_signage.py --source tesla >> $LOG_FILE 2>&1" >> "$CRON_JOBS"

# Stock: Every 5 minutes during market hours (6 AM - 1 PM Pacific, Mon-Fri)
echo "*/5 6-13 * * 1-5 cd $PROJECT_DIR && $PYTHON generate_signage.py --source stock >> $LOG_FILE 2>&1" >> "$CRON_JOBS"

# Ferry: Every 5 minutes
echo "*/5 * * * * cd $PROJECT_DIR && $PYTHON generate_signage.py --source ferry >> $LOG_FILE 2>&1" >> "$CRON_JOBS"

# Sports: Twice daily (8 AM and 8 PM)
echo "0 8,20 * * * cd $PROJECT_DIR && $PYTHON generate_signage.py --source sports >> $LOG_FILE 2>&1" >> "$CRON_JOBS"

# NFL live updates: Every 10 minutes on game days (Thu/Sun/Mon evenings 5 PM - 11 PM)
echo "*/10 17-23 * * 4,0,1 cd $PROJECT_DIR && $PYTHON generate_signage.py --source nfl >> $LOG_FILE 2>&1" >> "$CRON_JOBS"

# Whales: Every hour
echo "0 * * * * cd $PROJECT_DIR && $PYTHON generate_signage.py --source whales >> $LOG_FILE 2>&1" >> "$CRON_JOBS"

echo "" >> "$CRON_JOBS"

# Install new crontab
crontab "$CRON_JOBS"
rm "$CRON_JOBS"

echo -e "${GREEN}✓ Cron jobs installed successfully${NC}"
echo ""
echo "Installed jobs:"
crontab -l | grep "generate_signage.py"
echo ""
echo "Logs will be written to: $LOG_FILE"
echo ""
echo -e "${YELLOW}Note: For continuous live updates, consider running daemon mode instead:${NC}"
echo "  $PYTHON generate_signage.py --daemon"

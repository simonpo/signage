# Signage System Roadmap

## Current Status
✅ Core refactoring complete - modular architecture implemented
✅ Real WSDOT Ferry API integration working
✅ Virtual environment setup automation

## Planned Improvements

### Ferry Display Enhancement
- [ ] Refine ferry information layout and formatting
  - Consider adding crossing time from annotations
  - Display ETA information for vessels in transit
  - Show vessel status (At Dock / In Transit / In Service)
  - Explore real-time vessel position mapping
  - Optimize font sizes and spacing for better readability
  - Review two-column layout for better visual balance

### API Integrations (Stubs)
- [ ] Implement WSDOT Ferry API (vessel tracking endpoints)
- [ ] Implement Whale Tracker web scraping
- [ ] Implement Football API integration (Premier League)
- [ ] Implement Rugby API integration
- [ ] Implement Cricket API integration

### Features
- [ ] Add caching layer for slow APIs
- [ ] Implement graceful fallback when APIs are unavailable
- [ ] Add configuration validation on startup
- [ ] Create health check endpoint for daemon mode
- [ ] Revise layout engine architecture
  - Allow topic-specific custom layouts beyond current 5 types
  - Enable per-topic spacing, font size, and positioning control
  - Support mixed layouts (e.g., title centered, body left-aligned)
  - Add layout composition for complex displays
  - Consider template-based approach for maximum flexibility

### Performance
- [ ] Optimize background image loading
- [ ] Add parallel API fetching where possible
- [ ] Implement response caching with TTL

### Documentation
- [ ] Add API setup guides for each service
- [ ] Document background image best practices
- [ ] Create troubleshooting guide
- [ ] Add examples for each signage type

## Completed
- ✅ Modular architecture refactoring (12 phases)
- ✅ WSDOT Ferry API integration (schedule endpoint)
- ✅ Virtual environment automation
- ✅ Date-based filename generation
- ✅ 7-day file retention
- ✅ Multiple background providers with fallback
- ✅ Live sports detection for dynamic scheduling

# Signage System Roadmap

## Current Status
✅ Core refactoring complete - modular architecture implemented
✅ Real WSDOT Ferry API integration working
✅ Virtual environment setup automation
✅ Weather display enhanced with comprehensive API data (Nov 2025)
✅ HTML rendering system with modern layouts
✅ Nighttime detection for ambient weather displays

## Planned Improvements

### Ferry Display Enhancement
- [ ] Refine ferry information layout and formatting
  - Consider adding crossing time from annotations
  - Display ETA information for vessels in transit
  - Show vessel status (At Dock / In Transit / In Service)
  - Explore real-time vessel position mapping
  - Optimize font sizes and spacing for better readability
  - Review two-column layout for better visual balance

### API Integrations
- [x] OpenWeatherMap full integration (current weather with all available fields)
- [x] WSDOT Ferry API (schedule and vessel tracking)
- [x] Football API integration (Premier League via football-data.org)
- [x] Ambient Weather personal station API
- [ ] Rugby API integration
- [ ] Cricket API integration
- [ ] Investigate Kitsap Transit Fast Ferry API/data source
  - Check for GTFS feed availability
  - Contact transit agency about API access
  - Consider web scraping kttracker.com as fallback
  - Note: May only need static schedule display vs. live tracking

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
- ✅ Weather display comprehensive enhancement (Nov 2025)
  - Added 7 new OpenWeatherMap API fields (cloudiness, pressure, sunrise/sunset, wind gust, rain)
  - Modern two-column dashboard layout with glass-morphism cards
  - Smart weather icon selection based on conditions
  - Sunrise/sunset times with emoji icons
- ✅ Ambient weather nighttime detection using solar radiation
- ✅ Ferry map static filename for cleaner TV rotation
- ✅ Removed non-functional features (marine traffic, whale tracker)

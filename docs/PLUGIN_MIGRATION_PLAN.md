# Plugin Migration Plan: app → app_new

## Status Overview
- ✅ **Completed**: 2 plugins
- 🔧 **In Progress**: 1 plugin (needs fix)
- 📋 **Planned**: 5 plugins

## Completed Plugins

### 1. Hello World Plugin ✅
- **Status**: Active and working
- **Purpose**: Example/template plugin
- **Endpoints**: `/hello`, `/status`, `/reset`
- **File**: `plugins/hello_world/plugin.py`

### 2. System Monitor Plugin ✅
- **Status**: Active and working  
- **Purpose**: Real-time system resource monitoring
- **Endpoints**: `/info`, `/cpu`, `/memory`, `/disk`, `/network`, `/all`, `/stats`
- **Dependencies**: `psutil`
- **File**: `plugins/system_monitor/plugin.py`

## In Progress

### 3. Stocks Plugin 🔧
- **Status**: Needs import path fix (FIXED - awaiting reload)
- **Purpose**: Stock price tracking, alerts, predictions
- **Original Features**:
  - Real-time price monitoring with Finnhub/Alpha Vantage APIs
  - Price alerts (above/below thresholds)
  - Multi-notification support (SMS/Telegram/Discord)
  - Linear regression predictions
  - Showcase table with key symbols
  - Latest prices caching
- **Tables**: `stocks`, `alerts`, `latest_prices`, `predictions`
- **File**: `plugins/stocks/plugin.py`
- **TODO**: 
  - Fix import path (DONE)
  - Test endpoints
  - Add notification integration
  - Add API key configuration

## Planned Plugins

### 4. Journal Plugin 📋
- **Purpose**: Daily journal with calendar view and image uploads
- **Original Features**:
  - Calendar-based entries (date, time, location, notes)
  - Image/file uploads attached to entries
  - Gallery view
  - Timeline view
- **Tables**: `journal_entries`, `journal_images`
- **Endpoints**:
  - `GET /entries` - List all entries
  - `POST /entries` - Create entry
  - `GET /entries/{id}` - Get specific entry
  - `PUT /entries/{id}` - Update entry
  - `DELETE /entries/{id}` - Delete entry
  - `POST /entries/{id}/images` - Upload images
  - `GET /calendar/{year}/{month}` - Calendar view
- **UI Components**:
  - Calendar widget
  - Entry editor with rich text
  - Image uploader and gallery
  - Search/filter by date range

### 5. Notepad Plugin 📋
- **Purpose**: Multi-tab text editor/scratchpad
- **Original Features**:
  - Multiple named tabs
  - Auto-save
  - Full-text editing
  - Tab management (create/rename/delete)
- **Tables**: `pad_tabs` (migrated from legacy `pad` table)
- **Endpoints**:
  - `GET /tabs` - List all tabs
  - `POST /tabs` - Create new tab
  - `GET /tabs/{name}` - Get tab content
  - `PUT /tabs/{name}` - Update tab content
  - `DELETE /tabs/{name}` - Delete tab
  - `PUT /tabs/{name}/rename` - Rename tab
- **UI Components**:
  - Tab bar with switching
  - Code/text editor (Monaco or CodeMirror)
  - Auto-save indicator
  - Tab context menu

### 6. Surf Plugin 📋
- **Purpose**: Surf spot wave condition monitoring
- **Original Features**:
  - Multiple surf spot tracking
  - Wave height, period, direction
  - Open-Meteo API integration
  - Cached forecasts with refresh intervals
- **Tables**: `surf_spots`, `surf_cache`
- **Endpoints**:
  - `GET /spots` - List all surf spots
  - `POST /spots` - Add new spot
  - `GET /spots/{id}` - Get spot details
  - `GET /spots/{id}/conditions` - Get current conditions
  - `PUT /spots/{id}` - Update spot
  - `DELETE /spots/{id}` - Delete spot
  - `GET /forecast/{id}` - Get forecast data
- **UI Components**:
  - Spot cards with current conditions
  - Wave height graphs
  - Wind/swell direction compass
  - Map integration (optional)

### 7. TradingView Widget Plugin 📋
- **Purpose**: Financial charts and market data visualization
- **Original Features**:
  - Customizable symbol list
  - TradingView embedded widgets
  - Real-time price charts
  - Multiple chart types (candlestick, line, etc.)
- **Tables**: `tv_symbols`
- **Endpoints**:
  - `GET /symbols` - List configured symbols
  - `POST /symbols` - Add symbol
  - `DELETE /symbols/{symbol}` - Remove symbol
  - `GET /widget/{symbol}` - Get widget embed code
- **UI Components**:
  - TradingView widget iframe
  - Symbol selector
  - Chart customization options

### 8. Notes Plugin 📋
- **Purpose**: Quick timestamped notes/thoughts
- **Original Features**:
  - Simple chronological note list
  - Timestamps on all notes
  - Quick add/delete
  - Search/filter
- **Tables**: `notes`
- **Endpoints**:
  - `GET /notes` - List all notes
  - `POST /notes` - Create note
  - `GET /notes/{id}` - Get specific note
  - `DELETE /notes/{id}` - Delete note
  - `GET /notes/search` - Search notes
- **UI Components**:
  - Timeline/list view
  - Quick add input
  - Note cards with timestamps
  - Search bar

## Migration Strategy

### Phase 1: Foundation (DONE)
- ✅ Plugin architecture working
- ✅ Example plugins (Hello World, System Monitor)
- ✅ Plugin detail pages with testing UI
- ✅ Dark theme UI

### Phase 2: Core Features (CURRENT)
- 🔧 Fix and test Stocks plugin
- 📋 Implement Notepad plugin (most used)
- 📋 Implement Journal plugin (high value)

### Phase 3: Additional Features
- 📋 Implement Notes plugin
- 📋 Implement Surf plugin
- 📋 Implement TradingView widget

### Phase 4: Polish & Integration
- 📋 Dashboard widgets for all plugins
- 📋 Cross-plugin integration (e.g., link notes to journal entries)
- 📋 Unified search across all plugins
- 📋 Export/import functionality
- 📋 Mobile-responsive UI improvements

## Technical Notes

### Database Migration
- Original app uses single SQLite database (`data/app.db`)
- New app uses separate database (`data/cameronpad_dev.db`)
- Each plugin can have its own tables
- Consider migration script to copy data from old to new

### API Design
- All plugin endpoints under `/api/v1/plugins/{plugin_name}/`
- RESTful conventions
- JSON responses
- Authentication via JWT middleware

### Configuration
- Each plugin has `config.yaml` for settings
- Environment variables for sensitive data (API keys, tokens)
- Plugin-specific settings in config
- Global settings in app config

### Dependencies
- Track plugin dependencies in `PluginMetadata`
- Add to main `requirements.txt` or plugin-specific requirements
- Current external deps: `psutil`, API clients (finnhub, etc.)

## Next Steps

1. **Immediate**: Test fixed Stocks plugin
2. **Short-term**: Build Notepad plugin (weekend project)
3. **Medium-term**: Build Journal plugin (week project)
4. **Long-term**: Complete remaining plugins
5. **Future**: Data migration tool from app → app_new

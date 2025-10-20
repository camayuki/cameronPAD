# Copilot Instructions for CameronPAD Repository

Welcome to the CameronPAD repository! This document provides essential guidelines for AI coding agents to be productive in this codebase.

## Project Overview
CameronPAD is a modular web application platform with plugin support for various tools and services. Key features include:
- **Stock Monitoring**: Real-time stock price tracking.
- **Notes & Notepad**: Quick note-taking capabilities.
- **Journal**: Daily journaling with file uploads.
- **Surf Tracker**: Custom surf condition monitoring.
- **System Monitor**: Server resource monitoring.
- **TradingView Integration**: Embedded charts and analysis.
- **Plugin System**: Easily extendable with custom plugins.

## Architecture
The project is structured into the following major components:
- **Core**: Contains foundational modules like authentication, caching, and database integration.
- **API**: Implements RESTful endpoints, organized by functionality (e.g., `auth.py`, `router.py`).
- **Plugins**: Modular extensions that add specific features (e.g., `hello_world`, `stocks`).
- **Templates**: HTML templates for the web interface.
- **Docs**: Comprehensive documentation for developers.

### Data Flow
1. **Frontend**: HTML templates render dynamic content using data from the backend.
2. **Backend**: API endpoints process requests, interact with the database, and return responses.
3. **Plugins**: Extend functionality by integrating with the core API and database.

### Key Files
- `app_new/main.py`: Entry point for the application.
- `core/database.py`: Database connection and ORM setup.
- `plugins/`: Directory for all plugins.
- `templates/`: HTML templates for the web interface.

## Developer Workflows
### Setup
- **Windows**:
  ```powershell
  .\setup.ps1
  py -m uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
  ```
- **Linux/macOS**:
  ```bash
  chmod +x setup.sh
  ./setup.sh
  uvicorn app_new.main:app --reload --host 127.0.0.1 --port 8000
  ```

### Testing
- Run all tests:
  ```bash
  pytest tests/
  ```
- Test specific functionality:
  ```bash
  pytest tests/test_server.py
  ```

### Debugging
- Use `dev_server.py` for a simplified development server.
- Check logs in `logs/` for error details.

## Project-Specific Conventions
- **Plugin Development**:
  - Follow the structure in `docs/PLUGIN_TEMPLATE.md`.
  - Use `core/database.py` for database interactions.
- **API Design**:
  - Use RESTful principles.
  - Place endpoints in `api/v1/`.
- **Styling**:
  - Use `templates/base.html` as the base template.

## Integration Points
- **External APIs**:
  - Stock data: Finnhub, Alpha Vantage.
  - Surf data: Custom APIs.
- **Database**:
  - SQLite database located in `sqlite+aio/data/`.
- **Plugins**:
  - Communicate with the core API and database.

## Examples
### Adding a New Plugin
1. Copy the template from `docs/PLUGIN_TEMPLATE.md`.
2. Implement API endpoints in `plugins/<plugin_name>/`.
3. Register the plugin in `plugins/manager.py`.

### Debugging a Plugin
1. Check the plugin's logs in `logs/`.
2. Use the `status` endpoint to verify health.

---

For more details, refer to `docs/COMPLETE_GUIDE.md` and `docs/QUICK_REFERENCE.md`. Happy coding!
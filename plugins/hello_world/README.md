# Hello World Plugin

A simple example plugin for CameronPAD that demonstrates basic plugin functionality.

## Features

- **Simple API Endpoints**: 
  - `GET /hello` - Say hello (with optional `name` parameter)
  - `GET /status` - Get plugin status
  - `POST /reset` - Reset the greeting counter

- **Menu Integration**: Adds items to the web interface menu
- **Dashboard Widgets**: Shows plugin statistics
- **Health Checks**: Reports plugin health status

## Installation

This plugin is included by default. No additional installation required.

## Usage

### API Examples

**Say Hello:**
```bash
curl http://localhost:8000/api/v1/plugins/hello_world/hello
curl http://localhost:8000/api/v1/plugins/hello_world/hello?name=Cameron
```

**Check Status:**
```bash
curl http://localhost:8000/api/v1/plugins/hello_world/status
```

**Reset Counter:**
```bash
curl -X POST http://localhost:8000/api/v1/plugins/hello_world/reset
```

## Configuration

Edit `plugin.yaml` to configure:
- `greeting_style`: Style of greeting (friendly, formal, casual)
- `max_greetings`: Maximum number of greetings before auto-reset
- `custom_message`: Custom welcome message

## Development

This plugin serves as a template for creating new plugins. Key components:

1. `plugin.py` - Main plugin implementation
2. `plugin.yaml` - Plugin configuration
3. `__init__.py` - Plugin package initialization

To create your own plugin, copy this structure and modify as needed!

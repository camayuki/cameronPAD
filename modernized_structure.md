# CameronPAD - Modern Architecture

## Recommended Directory Structure

```
cameronpad/
├── app/                          # Core application
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── core/                     # Core framework
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration management
│   │   ├── database.py           # Database setup & migrations
│   │   ├── auth.py               # Authentication & authorization
│   │   ├── middleware.py         # Custom middleware
│   │   ├── exceptions.py         # Exception handlers
│   │   ├── logger.py             # Logging configuration
│   │   └── cache.py              # Caching layer
│   ├── api/                      # API layer
│   │   ├── __init__.py
│   │   ├── router.py             # Main API router
│   │   ├── deps.py               # Dependencies
│   │   ├── middleware.py         # API middleware
│   │   └── v1/                   # API versioning
│   │       ├── __init__.py
│   │       └── admin.py          # Admin API endpoints
│   ├── plugins/                  # Plugin system
│   │   ├── __init__.py
│   │   ├── manager.py            # Plugin manager
│   │   ├── base.py               # Base plugin class
│   │   ├── registry.py           # Plugin registry
│   │   ├── loader.py             # Plugin loader
│   │   └── config.py             # Plugin configuration
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   ├── base.py               # Base model classes
│   │   └── user.py               # User models
│   ├── services/                 # Business logic
│   │   ├── __init__.py
│   │   ├── user.py               # User service
│   │   └── notification.py       # Notification service
│   ├── utils/                    # Utilities
│   │   ├── __init__.py
│   │   ├── security.py           # Security utilities
│   │   ├── validators.py         # Input validation
│   │   └── helpers.py            # General helpers
│   └── templates/                # Jinja2 templates
│       ├── base.html
│       ├── admin/
│       │   ├── dashboard.html
│       │   └── plugins.html
│       └── components/
│           └── plugin_widget.html
├── plugins/                      # Available plugins
│   ├── stocks/                   # Stock tracking plugin
│   │   ├── __init__.py
│   │   ├── plugin.py             # Plugin definition
│   │   ├── models.py             # Stock models
│   │   ├── services.py           # Stock services
│   │   ├── api.py                # Stock API routes
│   │   ├── templates/
│   │   │   └── stocks.html
│   │   ├── static/
│   │   │   ├── css/
│   │   │   └── js/
│   │   ├── migrations/
│   │   │   └── 001_create_stocks.sql
│   │   ├── tests/
│   │   │   ├── test_models.py
│   │   │   ├── test_services.py
│   │   │   └── test_api.py
│   │   └── config.yaml           # Plugin configuration
│   ├── notes/                    # Notes plugin
│   │   ├── __init__.py
│   │   ├── plugin.py
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── api.py
│   │   ├── templates/
│   │   ├── migrations/
│   │   ├── tests/
│   │   └── config.yaml
│   ├── journal/                  # Journal plugin
│   │   └── ...
│   └── surf/                     # Surf conditions plugin
│       └── ...
├── config/                       # Configuration files
│   ├── app.yaml                  # Main app configuration
│   ├── database.yaml             # Database configuration
│   ├── plugins.yaml              # Plugin configuration
│   ├── environments/
│   │   ├── development.yaml
│   │   ├── staging.yaml
│   │   └── production.yaml
│   └── logging.yaml              # Logging configuration
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── unit/                     # Unit tests
│   │   ├── test_core/
│   │   ├── test_api/
│   │   └── test_plugins/
│   ├── integration/              # Integration tests
│   │   ├── test_api_integration.py
│   │   └── test_plugin_integration.py
│   └── fixtures/                 # Test fixtures
│       ├── data/
│       └── config/
├── migrations/                   # Database migrations
│   ├── versions/
│   └── alembic.ini
├── static/                       # Static assets
│   ├── css/
│   ├── js/
│   └── img/
├── data/                         # Data directory
│   ├── uploads/
│   └── cache/
├── scripts/                      # Utility scripts
│   ├── setup.py                  # Setup script
│   ├── migrate.py                # Migration script
│   └── deploy.py                 # Deployment script
├── docker/                       # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   ├── docker-compose.dev.yaml
│   └── docker-compose.prod.yaml
├── .github/                      # GitHub Actions
│   └── workflows/
│       ├── ci.yaml
│       ├── security.yaml
│       └── deploy.yaml
├── docs/                         # Documentation
│   ├── README.md
│   ├── API.md
│   ├── PLUGINS.md
│   ├── DEVELOPMENT.md
│   └── DEPLOYMENT.md
├── requirements/                 # Python dependencies
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── testing.txt
├── .env.example                  # Environment template
├── .gitignore
├── pyproject.toml                # Python project configuration
├── docker-compose.yml
└── README.md
```

## Key Architectural Principles

1. **Separation of Concerns**: Clear boundaries between core, API, business logic, and plugins
2. **Plugin Architecture**: Modular plugins with standardized interfaces
3. **Configuration Management**: Hierarchical configuration with environment overrides
4. **Testing Strategy**: Comprehensive testing at all levels
5. **Security First**: Authentication, authorization, and input validation
6. **Performance**: Caching, async operations, and monitoring
7. **Maintainability**: Clear code organization and documentation
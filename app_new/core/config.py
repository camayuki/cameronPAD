"""
Configuration management for CameronPAD application.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///data/app.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False
    migrate_on_startup: bool = True


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    password_min_length: int = 8
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_requests: int = 100
    rate_limit_period: int = 60


@dataclass
class CacheConfig:
    """Cache configuration."""
    backend: str = "memory"  # memory, redis
    redis_url: Optional[str] = None
    default_ttl: int = 300
    max_keys: int = 1000


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class PluginConfig:
    """Plugin system configuration."""
    plugins_dir: str = "plugins"
    config_dir: str = "config"
    auto_load: bool = True
    enable_hot_reload: bool = False


@dataclass
class APIConfig:
    """API configuration."""
    title: str = "CameronPAD API"
    description: str = "Personal productivity and tracking application"
    version: str = "2.0.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    enable_docs: bool = True


@dataclass
class AppConfig:
    """Main application configuration."""
    debug: bool = False
    environment: str = "production"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Sub-configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    # Additional settings
    upload_dir: str = "data/uploads"
    max_upload_size: int = 10485760  # 10MB
    allowed_file_types: List[str] = field(default_factory=lambda: [
        ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".txt", ".md"
    ])


class ConfigManager:
    """Configuration manager with environment overrides and validation."""
    
    def __init__(self, config_dir: str = "config", environment: Optional[str] = None):
        self.config_dir = Path(config_dir)
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self._config: Optional[AppConfig] = None
    
    def load_config(self) -> AppConfig:
        """Load configuration from files and environment variables."""
        if self._config is not None:
            return self._config
        
        # Start with default configuration
        config_data = {}
        
        # Load base configuration
        base_config_file = self.config_dir / "app.yaml"
        if base_config_file.exists():
            config_data.update(self._load_yaml_file(base_config_file))
        
        # Load environment-specific configuration
        env_config_file = self.config_dir / "environments" / f"{self.environment}.yaml"
        if env_config_file.exists():
            env_config = self._load_yaml_file(env_config_file)
            config_data = self._deep_merge(config_data, env_config)
        
        # Apply environment variable overrides
        self._apply_env_overrides(config_data)
        
        # Create configuration object
        self._config = self._create_config_object(config_data)
        
        # Validate configuration
        self._validate_config(self._config)
        
        logger.info(f"Loaded configuration for environment: {self.environment}")
        return self._config
    
    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading config file {file_path}: {e}")
            return {}
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> None:
        """Apply environment variable overrides."""
        # Database
        if db_url := os.getenv("DATABASE_URL"):
            config_data.setdefault("database", {})["url"] = db_url
        
        # Security
        if secret_key := os.getenv("SECRET_KEY"):
            config_data.setdefault("security", {})["secret_key"] = secret_key
        
        # Cache
        if redis_url := os.getenv("REDIS_URL"):
            config_data.setdefault("cache", {})["redis_url"] = redis_url
            config_data.setdefault("cache", {})["backend"] = "redis"
        
        # App settings
        if debug := os.getenv("DEBUG"):
            config_data["debug"] = debug.lower() in ("true", "1", "yes", "on")
        
        if host := os.getenv("HOST"):
            config_data["host"] = host
        
        if port := os.getenv("PORT"):
            try:
                config_data["port"] = int(port)
            except ValueError:
                logger.warning(f"Invalid PORT value: {port}")
        
        # Logging
        if log_level := os.getenv("LOG_LEVEL"):
            config_data.setdefault("logging", {})["level"] = log_level.upper()
        
        if log_file := os.getenv("LOG_FILE"):
            config_data.setdefault("logging", {})["file_path"] = log_file
        
        # Plugins
        if plugins_dir := os.getenv("PLUGINS_DIR"):
            config_data.setdefault("plugins", {})["plugins_dir"] = plugins_dir
        
        if config_dir := os.getenv("CONFIG_DIR"):
            config_data.setdefault("plugins", {})["config_dir"] = config_dir
    
    def _create_config_object(self, config_data: Dict[str, Any]) -> AppConfig:
        """Create AppConfig object from configuration data."""
        # Extract sub-configurations
        database_config = DatabaseConfig(**config_data.get("database", {}))
        security_config = SecurityConfig(**config_data.get("security", {}))
        cache_config = CacheConfig(**config_data.get("cache", {}))
        logging_config = LoggingConfig(**config_data.get("logging", {}))
        plugins_config = PluginConfig(**config_data.get("plugins", {}))
        api_config = APIConfig(**config_data.get("api", {}))
        
        # Remove sub-config data from main config
        main_config_data = config_data.copy()
        for key in ["database", "security", "cache", "logging", "plugins", "api"]:
            main_config_data.pop(key, None)
        
        # Create main config
        return AppConfig(
            **main_config_data,
            database=database_config,
            security=security_config,
            cache=cache_config,
            logging=logging_config,
            plugins=plugins_config,
            api=api_config
        )
    
    def _validate_config(self, config: AppConfig) -> None:
        """Validate configuration."""
        errors = []
        
        # Validate secret key
        if not config.security.secret_key:
            if config.environment == "production":
                errors.append("SECRET_KEY is required in production")
            else:
                # Generate a random secret key for development
                import secrets
                config.security.secret_key = secrets.token_urlsafe(32)
                logger.warning("Generated random SECRET_KEY for development")
        
        # Validate upload directory
        upload_dir = Path(config.upload_dir)
        try:
            upload_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"Cannot create upload directory {upload_dir}: {e}")
        
        # Validate Redis URL if using Redis cache
        if config.cache.backend == "redis" and not config.cache.redis_url:
            errors.append("REDIS_URL is required when using Redis cache backend")
        
        if errors:
            raise ValueError("Configuration validation failed: " + "; ".join(errors))
    
    def get_config(self) -> AppConfig:
        """Get current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> AppConfig:
        """Reload configuration from files."""
        self._config = None
        return self.load_config()


# Global configuration instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get current application configuration."""
    return get_config_manager().get_config()
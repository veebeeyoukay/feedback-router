"""Configuration loader for environment variables and YAML files."""

import os
from typing import Optional, Dict, Any
import yaml
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    echo: bool = False


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str
    port: int = 6379
    db: int = 0
    password: Optional[str] = None


@dataclass
class SlackConfig:
    """Slack configuration."""
    bot_token: str
    signing_secret: str
    app_token: str
    monitored_channels: list


@dataclass
class WebhookConfig:
    """Webhook configuration."""
    website_secret: Optional[str] = None
    rate_limit: int = 100
    rate_limit_window: int = 60


@dataclass
class AppConfig:
    """Application configuration."""
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "development"
    database: Optional[DatabaseConfig] = None
    redis: Optional[RedisConfig] = None
    slack: Optional[SlackConfig] = None
    webhook: Optional[WebhookConfig] = None


class ConfigLoader:
    """Loads configuration from environment and YAML files."""

    ENV_PREFIX = "FEEDBACK_ROUTER_"

    def __init__(self, config_dir: str = "config"):
        """Initialize config loader.

        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = config_dir
        self._config: Optional[AppConfig] = None

    @lru_cache(maxsize=1)
    def load(self) -> AppConfig:
        """Load configuration.

        Returns:
            AppConfig instance
        """
        if self._config:
            return self._config

        # Load from environment first
        config_dict = self._load_from_env()

        # Load from YAML files if they exist
        yaml_config = self._load_from_yaml()
        if yaml_config:
            config_dict.update(yaml_config)

        self._config = self._build_config(config_dict)
        return self._config

    def _load_from_env(self) -> Dict[str, Any]:
        """Load configuration from environment variables.

        Returns:
            Configuration dictionary
        """
        config = {
            "debug": os.getenv(f"{self.ENV_PREFIX}DEBUG", "False").lower() == "true",
            "log_level": os.getenv(f"{self.ENV_PREFIX}LOG_LEVEL", "INFO"),
            "environment": os.getenv(f"{self.ENV_PREFIX}ENVIRONMENT", "development"),
        }

        # Database config
        db_url = os.getenv(f"{self.ENV_PREFIX}DATABASE_URL")
        if db_url:
            config["database"] = {
                "url": db_url,
                "pool_size": int(os.getenv(f"{self.ENV_PREFIX}DATABASE_POOL_SIZE", "10")),
                "max_overflow": int(os.getenv(f"{self.ENV_PREFIX}DATABASE_MAX_OVERFLOW", "20")),
                "echo": os.getenv(f"{self.ENV_PREFIX}DATABASE_ECHO", "False").lower() == "true",
            }

        # Redis config
        redis_host = os.getenv(f"{self.ENV_PREFIX}REDIS_HOST")
        if redis_host:
            config["redis"] = {
                "host": redis_host,
                "port": int(os.getenv(f"{self.ENV_PREFIX}REDIS_PORT", "6379")),
                "db": int(os.getenv(f"{self.ENV_PREFIX}REDIS_DB", "0")),
                "password": os.getenv(f"{self.ENV_PREFIX}REDIS_PASSWORD"),
            }

        # Slack config
        slack_token = os.getenv(f"{self.ENV_PREFIX}SLACK_BOT_TOKEN")
        if slack_token:
            config["slack"] = {
                "bot_token": slack_token,
                "signing_secret": os.getenv(f"{self.ENV_PREFIX}SLACK_SIGNING_SECRET", ""),
                "app_token": os.getenv(f"{self.ENV_PREFIX}SLACK_APP_TOKEN", ""),
                "monitored_channels": os.getenv(
                    f"{self.ENV_PREFIX}SLACK_MONITORED_CHANNELS", "feedback"
                ).split(","),
            }

        # Webhook config
        config["webhook"] = {
            "website_secret": os.getenv(f"{self.ENV_PREFIX}WEBHOOK_SECRET"),
            "rate_limit": int(os.getenv(f"{self.ENV_PREFIX}WEBHOOK_RATE_LIMIT", "100")),
            "rate_limit_window": int(os.getenv(f"{self.ENV_PREFIX}WEBHOOK_RATE_LIMIT_WINDOW", "60")),
        }

        return config

    def _load_from_yaml(self) -> Optional[Dict[str, Any]]:
        """Load configuration from YAML files.

        Returns:
            Configuration dictionary or None
        """
        # Try environment-specific config first
        env = os.getenv(f"{self.ENV_PREFIX}ENVIRONMENT", "development")
        env_config_path = os.path.join(self.config_dir, f"{env}.yaml")

        if os.path.exists(env_config_path):
            with open(env_config_path, 'r') as f:
                return yaml.safe_load(f)

        # Fall back to default config
        default_config_path = os.path.join(self.config_dir, "config.yaml")
        if os.path.exists(default_config_path):
            with open(default_config_path, 'r') as f:
                return yaml.safe_load(f)

        return None

    def _build_config(self, config_dict: Dict[str, Any]) -> AppConfig:
        """Build AppConfig from dictionary.

        Args:
            config_dict: Configuration dictionary

        Returns:
            AppConfig instance
        """
        database_config = None
        if config_dict.get("database"):
            db = config_dict["database"]
            database_config = DatabaseConfig(
                url=db.get("url", ""),
                pool_size=db.get("pool_size", 10),
                max_overflow=db.get("max_overflow", 20),
                echo=db.get("echo", False),
            )

        redis_config = None
        if config_dict.get("redis"):
            r = config_dict["redis"]
            redis_config = RedisConfig(
                host=r.get("host", "localhost"),
                port=r.get("port", 6379),
                db=r.get("db", 0),
                password=r.get("password"),
            )

        slack_config = None
        if config_dict.get("slack"):
            s = config_dict["slack"]
            slack_config = SlackConfig(
                bot_token=s.get("bot_token", ""),
                signing_secret=s.get("signing_secret", ""),
                app_token=s.get("app_token", ""),
                monitored_channels=s.get("monitored_channels", []),
            )

        webhook_config = None
        if config_dict.get("webhook"):
            w = config_dict["webhook"]
            webhook_config = WebhookConfig(
                website_secret=w.get("website_secret"),
                rate_limit=w.get("rate_limit", 100),
                rate_limit_window=w.get("rate_limit_window", 60),
            )

        return AppConfig(
            debug=config_dict.get("debug", False),
            log_level=config_dict.get("log_level", "INFO"),
            environment=config_dict.get("environment", "development"),
            database=database_config,
            redis=redis_config,
            slack=slack_config,
            webhook=webhook_config,
        )

    def get_config(self) -> AppConfig:
        """Get loaded configuration.

        Returns:
            AppConfig instance
        """
        return self.load()


# Global config instance
_config_loader: Optional[ConfigLoader] = None


def get_config(config_dir: str = "config") -> AppConfig:
    """Get application configuration.

    Args:
        config_dir: Configuration directory

    Returns:
        AppConfig instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_dir)
    return _config_loader.get_config()

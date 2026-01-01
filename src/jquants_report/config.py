"""Configuration management for J-Quants Daily Report System."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class JQuantsConfig:
    """J-Quants API configuration."""

    email: str
    password: str
    refresh_token: str | None = None
    base_url: str = "https://api.jquants.com/v1"


@dataclass
class AppConfig:
    """Application configuration."""

    report_output_dir: Path = field(default_factory=lambda: Path("./reports"))
    cache_dir: Path = field(default_factory=lambda: Path("./data"))
    log_level: str = "INFO"


@dataclass
class Config:
    """Main configuration class."""

    jquants: JQuantsConfig
    app: AppConfig


def load_config() -> Config:
    """Load configuration from environment variables.

    Returns:
        Config: The loaded configuration object.

    Raises:
        ValueError: If required environment variables are missing.
    """
    load_dotenv()

    email = os.getenv("JQUANTS_EMAIL")
    password = os.getenv("JQUANTS_PASSWORD")

    if not email or not password:
        raise ValueError("JQUANTS_EMAIL and JQUANTS_PASSWORD environment variables are required")

    jquants_config = JQuantsConfig(
        email=email,
        password=password,
        refresh_token=os.getenv("JQUANTS_REFRESH_TOKEN"),
    )

    app_config = AppConfig(
        report_output_dir=Path(os.getenv("REPORT_OUTPUT_DIR", "./reports")),
        cache_dir=Path(os.getenv("CACHE_DIR", "./data")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

    return Config(jquants=jquants_config, app=app_config)

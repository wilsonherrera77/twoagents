#!/usr/bin/env python3
"""
Configuration module.
"""

import os
from typing import Any


class Config:
    """Application configuration."""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return getattr(cls, key, default)


config = Config()

"""
Pydantic schemas for YAML configuration validation.
"""

import os
import re
from typing import Any, Literal

from croniter import croniter  # type: ignore[import-untyped]
from pydantic import BaseModel, Field, field_validator


class RenderingConfig(BaseModel):
    """Rendering configuration for a source."""

    layout: str = "default"
    mode: Literal["pil", "html"] | None = None
    background: Literal["local", "unsplash", "pexels", "gradient"] = "local"
    background_query: str | None = None


class RetryConfig(BaseModel):
    """Retry configuration."""

    enabled: bool = True
    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_seconds: list[int] = Field(default=[1, 2, 4])


class FallbackConfig(BaseModel):
    """Fallback configuration."""

    use_cached: bool = False
    max_age_hours: int = Field(default=24, ge=1, le=168)  # Max 1 week


class SourceConfig(BaseModel):
    """Configuration for a single source instance."""

    id: str = Field(..., description="Unique identifier")
    type: str = Field(..., description="Source type (e.g., 'weather')")
    enabled: bool = True
    schedule: str = Field(..., description="Cron expression")
    timeout: int = Field(default=30, ge=1, le=300)  # 1s to 5min
    config: dict[str, Any] = Field(default_factory=dict)
    rendering: RenderingConfig = Field(default_factory=RenderingConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("ID must contain only letters, numbers, underscores, and hyphens")
        return v

    @field_validator("schedule")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Basic cron expression validation."""
        try:
            # Use croniter to validate the expression
            croniter(v)
        except Exception as e:
            raise ValueError(f"Invalid cron expression '{v}': {e}") from e
        return v

    def expand_env_vars(self) -> "SourceConfig":
        """Expand ${VAR} references in config values."""
        expanded_config = {}
        for key, value in self.config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                expanded_value = os.getenv(env_var)
                if expanded_value is None:
                    raise ValueError(f"Environment variable {env_var} not set")
                expanded_config[key] = expanded_value
            else:
                expanded_config[key] = value

        self.config = expanded_config
        return self


class SourcesConfig(BaseModel):
    """Top-level configuration schema."""

    sources: list[SourceConfig]

    @field_validator("sources")
    @classmethod
    def validate_unique_ids(cls, v: list[SourceConfig]) -> list[SourceConfig]:
        """Ensure all source IDs are unique."""
        ids = [source.id for source in v]
        duplicates = [id for id in ids if ids.count(id) > 1]
        if duplicates:
            raise ValueError(f"Duplicate source IDs found: {set(duplicates)}")
        return v

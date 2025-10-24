"""V10 autonomous multi-agent system package."""

from importlib.metadata import version, PackageNotFoundError

__all__ = ["__version__"]

try:
    __version__ = version("v10")
except PackageNotFoundError:  # pragma: no cover - local development fallback
    __version__ = "0.1.0"

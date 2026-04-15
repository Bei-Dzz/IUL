"""
Actuarial Calculation Engine - A modular Python engine for actuarial calculations.
"""

from .core.base import (
    AbstractCalculationModule,
    RepositoryReader,
    OutputWriter,
    CalculationStatus,
    OutputFormat,
    DataType
)
from .core.exceptions import (
    EngineError,
    ConfigurationError,
    InputError,
    OutputError,
    CalculationError,
    ModuleLoadError,
    ValidationError
)
from .core.config import (
    ConfigLoader,
    EngineConfig,
    ModuleConfig,
    InputConfig,
    OutputConfig,
    OutputDestination,
    CashFlowProjectionConfig,
    RunSettings
)
from .core.logging import setup_logging, logger

__version__ = "0.1.0"
__all__ = [
    # Base classes
    "AbstractCalculationModule",
    "RepositoryReader",
    "OutputWriter",

    # Enums
    "CalculationStatus",
    "OutputFormat",
    "DataType",

    # Exceptions
    "EngineError",
    "ConfigurationError",
    "InputError",
    "OutputError",
    "CalculationError",
    "ModuleLoadError",
    "ValidationError",

    # Configuration
    "ConfigLoader",
    "EngineConfig",
    "ModuleConfig",
    "InputConfig",
    "OutputConfig",
    "OutputDestination",
    "CashFlowProjectionConfig",
    "RunSettings",

    # Logging
    "setup_logging",
    "logger"
]
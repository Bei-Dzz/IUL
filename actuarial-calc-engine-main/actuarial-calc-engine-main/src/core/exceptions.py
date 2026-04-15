"""
Custom exception classes for the actuarial calculation engine.
"""


class EngineError(Exception):
    """Base exception for engine-related errors."""
    pass


class ConfigurationError(EngineError):
    """Raised when there's an error in configuration."""
    pass


class InputError(EngineError):
    """Raised when there's an error reading input data."""
    pass


class OutputError(EngineError):
    """Raised when there's an error writing output data."""
    pass


class CalculationError(EngineError):
    """Raised when there's an error in calculation logic."""
    pass


class ModuleLoadError(EngineError):
    """Raised when a calculation module cannot be loaded."""
    pass


class ValidationError(EngineError):
    """Raised when data validation fails."""
    pass
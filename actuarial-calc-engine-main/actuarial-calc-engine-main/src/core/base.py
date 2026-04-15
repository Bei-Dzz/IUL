"""
Core base classes and abstract interfaces for the actuarial calculation engine.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import pandas as pd


class CalculationStatus(Enum):
    """Status of a calculation module execution."""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


class OutputFormat(Enum):
    """Supported output formats."""
    CSV = "csv"
    JSON = "json"
    POSTGRESQL = "postgresql"


class DataType(Enum):
    """Data types for input/output."""
    DATAFRAME = "dataframe"
    DICT = "dict"
    SCALAR = "scalar"


class RepositoryReader(ABC):
    """Abstract base class for input data repositories."""

    @abstractmethod
    def read_data(self, key: str) -> Union[pd.DataFrame, Dict[str, Any], Any]:
        """
        Read data from the repository by key.

        Args:
            key: Identifier for the data to read

        Returns:
            Data in appropriate format (DataFrame, dict, or scalar)
        """
        pass

    @abstractmethod
    def list_available_keys(self) -> List[str]:
        """
        List all available data keys in the repository.

        Returns:
            List of available data keys
        """
        pass


class OutputWriter(ABC):
    """Abstract base class for output writers."""

    @abstractmethod
    def write(self, key: str, data: Union[pd.DataFrame, Dict[str, Any], Any]) -> None:
        """
        Write data to the output destination.

        Args:
            key: Identifier for the output data
            data: Data to write (DataFrame, dict, or scalar)
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close any open connections or files."""
        pass


class AbstractCalculationModule(ABC):
    """
    Abstract base class for all calculation modules.

    Users should inherit from this class and implement the execute() method.
    """

    def __init__(self, name: str, input_handler: 'InputHandler', output_handler: 'OutputHandler', config: 'EngineConfig'):
        """
        Initialize the calculation module.

        Args:
            name: Name of the module
            input_handler: Handler for accessing input data
            output_handler: Handler for writing output data
            config: Engine configuration
        """
        self.name = name
        self.input_handler = input_handler
        self.output_handler = output_handler
        self.config = config
        self.status = CalculationStatus.SKIPPED
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @abstractmethod
    def execute(self) -> None:
        """
        Execute the calculation logic.

        This method should:
        1. Request data from input_handler
        2. Perform calculations
        3. Write results to output_handler
        4. Update status and log errors/warnings
        """
        pass

    def get_results(self) -> Dict[str, Any]:
        """
        Get execution results and status.

        Returns:
            Dictionary with execution status, errors, warnings, and metadata
        """
        return {
            "module_name": self.name,
            "status": self.status.value,
            "errors": self.errors,
            "warnings": self.warnings,
            "execution_timestamp": pd.Timestamp.now()
        }

    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.errors.append(message)
        self.status = CalculationStatus.ERROR

    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.warnings.append(message)
        if self.status != CalculationStatus.ERROR:
            self.status = CalculationStatus.WARNING

    def log_success(self) -> None:
        """Mark execution as successful."""
        if self.status != CalculationStatus.ERROR and self.status != CalculationStatus.WARNING:
            self.status = CalculationStatus.SUCCESS
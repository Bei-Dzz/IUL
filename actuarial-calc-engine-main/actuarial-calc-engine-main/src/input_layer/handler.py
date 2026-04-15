"""
Input handler for managing data access from various repositories.
"""

from typing import Any, Dict, List, Union
import pandas as pd

from ..core.base import RepositoryReader
from ..core.exceptions import InputError
from ..core.logging import logger
from .repository import ExcelRepository, PostgreSQLRepository


class InputHandler:
    """
    Handler for accessing input data from repositories with caching.

    Provides a unified interface for accessing data by key, with lazy loading
    and caching within a single calculation run.
    """

    def __init__(self, repository: RepositoryReader):
        """
        Initialize input handler.

        Args:
            repository: The repository to read data from
        """
        self.repository = repository
        self._cache: Dict[str, Union[pd.DataFrame, Dict[str, Any], Any]] = {}

    def get_data(self, key: str) -> Union[pd.DataFrame, Dict[str, Any], Any]:
        """
        Get data by key, loading from repository if not cached.

        Args:
            key: Data identifier

        Returns:
            Data in appropriate format
        """
        if key not in self._cache:
            logger.debug(f"Loading data for key: {key}")
            try:
                data = self.repository.read_data(key)
                self._cache[key] = data
            except Exception as e:
                raise InputError(f"Failed to load data for key '{key}': {e}")

        return self._cache[key]

    def read_data(self, key: str) -> Union[pd.DataFrame, Dict[str, Any], Any]:
        """
        Alias for get_data method for backward compatibility.

        Args:
            key: Data identifier

        Returns:
            Data in appropriate format
        """
        return self.get_data(key)

    def get_dataframe(self, key: str) -> pd.DataFrame:
        """
        Get data as DataFrame, with type checking.

        Args:
            key: Data identifier

        Returns:
            Data as pandas DataFrame

        Raises:
            InputError: If data is not a DataFrame
        """
        data = self.get_data(key)
        if not isinstance(data, pd.DataFrame):
            raise InputError(f"Data for key '{key}' is not a DataFrame")
        return data

    def get_dict(self, key: str) -> Dict[str, Any]:
        """
        Get data as dictionary, with type checking.

        Args:
            key: Data identifier

        Returns:
            Data as dictionary

        Raises:
            InputError: If data is not a dictionary
        """
        data = self.get_data(key)
        if not isinstance(data, dict):
            raise InputError(f"Data for key '{key}' is not a dictionary")
        return data

    def list_available_keys(self) -> List[str]:
        """
        List all available data keys.

        Returns:
            List of available keys
        """
        return self.repository.list_available_keys()

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self._cache.clear()
        logger.debug("Input cache cleared")

    def is_cached(self, key: str) -> bool:
        """
        Check if data for key is cached.

        Args:
            key: Data identifier

        Returns:
            True if data is cached
        """
        return key in self._cache


def create_input_handler(input_config) -> InputHandler:
    """
    Factory function to create appropriate input handler based on configuration.

    Args:
        input_config: InputConfig object

    Returns:
        Configured InputHandler

    Raises:
        InputError: If repository cannot be created
    """
    if input_config.source == 'excel':
        if not input_config.file_path:
            raise InputError("Excel input requires file_path")
        repository = ExcelRepository(input_config.file_path)

    elif input_config.source == 'postgresql':
        if not input_config.connection_string:
            raise InputError("PostgreSQL input requires connection_string")
        repository = PostgreSQLRepository(
            input_config.connection_string,
            input_config.table_mappings
        )

    else:
        raise InputError(f"Unsupported input source: {input_config.source}")

    return InputHandler(repository)
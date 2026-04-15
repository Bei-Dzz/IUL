"""
Output handler for managing data writing to various destinations.
"""

from typing import Any, Dict, List, Union
import pandas as pd

from ..core.base import OutputWriter, OutputFormat
from ..core.exceptions import OutputError
from ..core.logging import logger
from .writer import CSVWriter, JSONWriter, PostgreSQLWriter


class OutputHandler:
    """
    Handler for writing output data to multiple destinations.

    Manages multiple output writers and routes data to appropriate destinations.
    """

    def __init__(self, writers: List[OutputWriter]):
        """
        Initialize output handler.

        Args:
            writers: List of output writers
        """
        self.writers = writers

    def write(self, key: str, data: Union[pd.DataFrame, Dict[str, Any], Any]) -> None:
        """
        Write data to all configured output destinations.

        Args:
            key: Data identifier
            data: Data to write
        """
        if not self.writers:
            logger.warning("No output writers configured")
            return

        errors = []
        for writer in self.writers:
            try:
                writer.write(key, data)
            except Exception as e:
                error_msg = f"Failed to write to {type(writer).__name__}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)

        if errors:
            raise OutputError(f"Output errors occurred: {errors}")

    def write_batch(self, results: Dict[str, Union[pd.DataFrame, Dict[str, Any], Any]]) -> None:
        """
        Write multiple results in batch.

        Args:
            results: Dictionary of key -> data mappings
        """
        for key, data in results.items():
            self.write(key, data)

    def close(self) -> None:
        """Close all output writers."""
        for writer in self.writers:
            try:
                writer.close()
            except Exception as e:
                logger.error(f"Error closing {type(writer).__name__}: {e}")


def create_output_handler(output_config) -> OutputHandler:
    """
    Factory function to create output handler with configured writers.

    Args:
        output_config: OutputConfig object

    Returns:
        Configured OutputHandler

    Raises:
        OutputError: If writers cannot be created
    """
    writers = []

    for dest in output_config.destinations:
        if dest.format == OutputFormat.CSV.value:
            if not dest.path:
                raise OutputError("CSV output requires path")
            writers.append(CSVWriter(dest.path))

        elif dest.format == OutputFormat.JSON.value:
            if not dest.path:
                raise OutputError("JSON output requires path")
            writers.append(JSONWriter(dest.path))

        elif dest.format == OutputFormat.POSTGRESQL.value:
            if not dest.connection_string:
                raise OutputError("PostgreSQL output requires connection_string")
            writers.append(PostgreSQLWriter(dest.connection_string, dest.table_name))

        else:
            raise OutputError(f"Unsupported output format: {dest.format}")

    return OutputHandler(writers)
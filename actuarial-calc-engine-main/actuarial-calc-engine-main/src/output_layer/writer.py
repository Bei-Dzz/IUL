"""
Output writer implementations for CSV, JSON, and PostgreSQL destinations.
"""

import json
import pandas as pd
from sqlalchemy import create_engine, text
from typing import Any, Dict, Union
from pathlib import Path

from ..core.base import OutputWriter
from ..core.exceptions import OutputError
from ..core.logging import logger


class CSVWriter(OutputWriter):
    """Writer for CSV file output."""

    def __init__(self, file_path: str):
        """
        Initialize CSV writer.

        Args:
            file_path: Path to the output CSV file
        """
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, key: str, data: Union[pd.DataFrame, Dict[str, Any], Any]) -> None:
        """
        Write data to CSV file.

        Args:
            key: Data identifier (used as filename suffix if needed)
            data: Data to write
        """
        try:
            if isinstance(data, pd.DataFrame):
                # For DataFrames, write directly to CSV
                output_path = self.file_path
                if key != 'default':
                    # If key is not default, append to filename
                    stem = self.file_path.stem
                    suffix = self.file_path.suffix
                    output_path = self.file_path.parent / f"{stem}_{key}{suffix}"

                data.to_csv(output_path, index=False)
                logger.debug(f"Wrote DataFrame to CSV: {output_path}")

            elif isinstance(data, dict):
                # For dictionaries, convert to DataFrame first
                df = pd.DataFrame([data])
                output_path = self.file_path.parent / f"{key}.csv"
                df.to_csv(output_path, index=False)
                logger.debug(f"Wrote dictionary to CSV: {output_path}")

            else:
                # For other types, create single-value DataFrame
                df = pd.DataFrame({'value': [data]})
                output_path = self.file_path.parent / f"{key}.csv"
                df.to_csv(output_path, index=False)
                logger.debug(f"Wrote scalar to CSV: {output_path}")

        except Exception as e:
            raise OutputError(f"Failed to write CSV for key '{key}': {e}")

    def close(self) -> None:
        """No cleanup needed for CSV files."""
        pass


class JSONWriter(OutputWriter):
    """Writer for JSON file output."""

    def __init__(self, file_path: str):
        """
        Initialize JSON writer.

        Args:
            file_path: Path to the output JSON file
        """
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, key: str, data: Union[pd.DataFrame, Dict[str, Any], Any]) -> None:
        """
        Write data to JSON file.

        Args:
            key: Data identifier
            data: Data to write
        """
        try:
            output_path = self.file_path
            if key != 'default':
                stem = self.file_path.stem
                suffix = self.file_path.suffix
                output_path = self.file_path.parent / f"{stem}_{key}{suffix}"

            if isinstance(data, pd.DataFrame):
                # Convert DataFrame to list of dictionaries
                payload = data.to_dict('records')
            elif isinstance(data, dict):
                payload = data
            else:
                # For scalars, wrap in a dictionary
                payload = {'value': data}

            with open(output_path, 'w') as f:
                json.dump(payload, f, indent=2, default=str)

            logger.debug(f"Wrote JSON file: {output_path}")

        except Exception as e:
            raise OutputError(f"Failed to write JSON for key '{key}': {e}")

    def close(self) -> None:
        """No cleanup needed for JSON files."""
        pass


class PostgreSQLWriter(OutputWriter):
    """Writer for PostgreSQL database output."""

    def __init__(self, connection_string: str, table_name: str = None):
        """
        Initialize PostgreSQL writer.

        Args:
            connection_string: Database connection string
            table_name: Default table name (can be overridden per write)
        """
        self.connection_string = connection_string
        self.default_table_name = table_name or 'calculation_results'
        self._engine = None

        try:
            self._engine = create_engine(connection_string)
            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except Exception as e:
            raise OutputError(f"Failed to connect to PostgreSQL database: {e}")

    def write(self, key: str, data: Union[pd.DataFrame, Dict[str, Any], Any]) -> None:
        """
        Write data to PostgreSQL table.

        Args:
            key: Data identifier (used as table name suffix if needed)
            data: Data to write
        """
        if not self._engine:
            raise OutputError("Database connection not established")

        # Determine table name
        table_name = self.default_table_name
        if key != 'default':
            table_name = f"{self.default_table_name}_{key}"

        try:
            if isinstance(data, pd.DataFrame):
                # Write DataFrame directly to table
                data.to_sql(table_name, self._engine, if_exists='replace', index=False)
                logger.debug(f"Wrote DataFrame to PostgreSQL table: {table_name}")

            elif isinstance(data, dict):
                # Convert dict to DataFrame first
                df = pd.DataFrame([data])
                df.to_sql(table_name, self._engine, if_exists='replace', index=False)
                logger.debug(f"Wrote dictionary to PostgreSQL table: {table_name}")

            else:
                # For scalars, create single-row table
                df = pd.DataFrame({'value': [data], 'key': [key]})
                df.to_sql(table_name, self._engine, if_exists='replace', index=False)
                logger.debug(f"Wrote scalar to PostgreSQL table: {table_name}")

        except Exception as e:
            raise OutputError(f"Failed to write to PostgreSQL table '{table_name}': {e}")

    def close(self) -> None:
        """Close database connection."""
        if self._engine:
            self._engine.dispose()
            logger.debug("PostgreSQL connection closed")
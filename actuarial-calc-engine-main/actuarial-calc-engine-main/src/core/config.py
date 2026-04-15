"""
Configuration loading and validation for the actuarial calculation engine.
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .exceptions import ConfigurationError


@dataclass
class ModuleConfig:
    """Configuration for a calculation module."""
    name: str
    class_path: str
    enabled: bool = True
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class InputConfig:
    """Configuration for input sources."""
    source: str  # "excel" or "postgresql"
    file_path: Optional[str] = None
    connection_string: Optional[str] = None
    table_mappings: Optional[Dict[str, str]] = None


@dataclass
class OutputDestination:
    """Configuration for an output destination."""
    format: str  # "csv", "json", or "postgresql"
    path: Optional[str] = None
    connection_string: Optional[str] = None
    table_name: Optional[str] = None


@dataclass
class OutputConfig:
    """Configuration for output destinations."""
    destinations: List[OutputDestination]


@dataclass
class CashFlowProjectionConfig:
    """Configuration for cash flow projection."""
    projection_horizon_years: int = 100
    time_step_per_year: int = 12  # Number of time steps per year (12=monthly, 4=quarterly, 2=semi-annual, 1=annual)


@dataclass
class RunSettings:
    """Run-time settings for calculations."""
    modules: List[ModuleConfig] = field(default_factory=list)
    input: InputConfig = field(default_factory=lambda: InputConfig(source="excel"))
    output: OutputConfig = field(default_factory=lambda: OutputConfig(destinations=[]))
    cash_flow_projection: CashFlowProjectionConfig = field(default_factory=CashFlowProjectionConfig)
    assumption_table_name: str = None


@dataclass
class EngineConfig:
    """Main engine configuration."""
    log_level: str = "INFO"
    log_file: Optional[str] = None
    run_settings: RunSettings = field(default_factory=RunSettings)


class ConfigLoader:
    """Loads and validates configuration from YAML files."""

    @staticmethod
    def load_run_settings(run_settings_path: str) -> RunSettings:
        """
        Load run settings from a YAML file.

        Args:
            run_settings_path: Path to the run settings YAML file

        Returns:
            Parsed RunSettings

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            with open(run_settings_path, 'r') as f:
                run_settings_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Run settings file not found: {run_settings_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in run settings file: {e}")

        return ConfigLoader._parse_run_settings(run_settings_data)
    
    @staticmethod
    def load_engine_config(config_path: str) -> EngineConfig:
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file

        Returns:
            Parsed and validated EngineConfig

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {config_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")

        return ConfigLoader._parse_config(config_data)

    @staticmethod
    def _parse_run_settings(run_settings_data: Dict[str, Any]) -> RunSettings:
        """
        Parse run settings dictionary into RunSettings object.

        Args:
            run_settings_data: Raw run settings dictionary

        Returns:
            Parsed RunSettings

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Parse modules
            modules_data = run_settings_data.get('modules', [])
            modules = []
            for module_data in modules_data:
                module = ModuleConfig(
                    name=module_data['name'],
                    class_path=module_data['class'],
                    enabled=module_data.get('enabled', True),
                    parameters=module_data.get('parameters')
                )
                modules.append(module)

            # Parse input
            input_data = run_settings_data.get('input', {})
            input_config = InputConfig(
                source=input_data['source'],
                file_path=input_data.get('file_path'),
                connection_string=input_data.get('connection_string'),
                table_mappings=input_data.get('table_mappings')
            )

            # Parse output
            output_data = run_settings_data.get('output', {})
            destinations_data = output_data.get('destinations', [])
            destinations = []
            for dest_data in destinations_data:
                dest = OutputDestination(
                    format=dest_data['format'],
                    path=dest_data.get('path'),
                    connection_string=dest_data.get('connection_string'),
                    table_name=dest_data.get('table_name')
                )
                destinations.append(dest)

            output_config = OutputConfig(destinations=destinations)

            # Parse cash flow projection
            projection_data = run_settings_data.get('cash_flow_projection')
            if projection_data is not None and 'projection_horizon_years' not in projection_data:
                raise ConfigurationError("projection_horizon_years must be specified when cash_flow_projection config is present")
            cash_flow_projection_config = CashFlowProjectionConfig(
                projection_horizon_years=projection_data.get('projection_horizon_years', 100) if projection_data else 100,
                time_step_per_year=projection_data.get('time_step_per_year', 12) if projection_data else 12
            )

            # Parse assumption table name
            assumption_table_name = run_settings_data.get('assumption_table_name', "202512 BE assumptions")

            return RunSettings(
                modules=modules,
                input=input_config,
                output=output_config,
                cash_flow_projection=cash_flow_projection_config,
                assumption_table_name=assumption_table_name
            )

        except KeyError as e:
            raise ConfigurationError(f"Missing required run settings key: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error parsing run settings: {e}")

    @staticmethod
    def _parse_config(config_data: Dict[str, Any]) -> EngineConfig:
        """
        Parse configuration dictionary into EngineConfig object.

        Args:
            config_data: Raw configuration dictionary

        Returns:
            Parsed EngineConfig

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Parse engine settings
            engine_data = config_data.get('engine', {})
            log_level = engine_data.get('log_level', 'INFO')
            log_file = engine_data.get('log_file')

            return EngineConfig(
                log_level=log_level,
                log_file=log_file
            )

        except Exception as e:
            raise ConfigurationError(f"Error parsing configuration: {e}")

    @staticmethod
    def validate_config(config: EngineConfig) -> None:
        """
        Validate the parsed configuration.

        Args:
            config: EngineConfig to validate

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate run settings
        run_settings = config.run_settings

        # Validate input source
        if run_settings.input.source not in ['excel', 'postgresql']:
            raise ConfigurationError(f"Invalid input source: {run_settings.input.source}")

        if run_settings.input.source == 'excel' and not run_settings.input.file_path:
            raise ConfigurationError("Excel input source requires file_path")

        if run_settings.input.source == 'postgresql' and not run_settings.input.connection_string:
            raise ConfigurationError("PostgreSQL input source requires connection_string")

        # Validate output destinations
        for dest in run_settings.output.destinations:
            if dest.format not in ['csv', 'json', 'postgresql']:
                raise ConfigurationError(f"Invalid output format: {dest.format}")

            if dest.format in ['csv', 'json'] and not dest.path:
                raise ConfigurationError(f"{dest.format} output requires path")

            if dest.format == 'postgresql' and not dest.connection_string:
                raise ConfigurationError("PostgreSQL output requires connection_string")

        # Validate modules
        if not run_settings.modules:
            raise ConfigurationError("At least one module must be configured")

        module_names = [m.name for m in run_settings.modules]
        if len(module_names) != len(set(module_names)):
            raise ConfigurationError("Module names must be unique")

        if run_settings.cash_flow_projection.projection_horizon_years <= 0:
            raise ConfigurationError("projection_horizon_years must be positive")
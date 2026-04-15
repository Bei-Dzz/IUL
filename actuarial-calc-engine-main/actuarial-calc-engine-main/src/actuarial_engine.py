"""
Command-line interface for the actuarial calculation engine.
"""

import click
import sys
from pathlib import Path

from .core.config import ConfigLoader
from .core.logging import setup_logging
from .calculation_layer.engine import CalculationEngine

ENGINE_CONFIG_PATH = Path("config/engine_config.yaml")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Actuarial Calculation Engine - Modular calculation framework."""
    pass


@cli.command()
@click.argument('run_settings_file', type=click.Path(exists=True))
@click.option('--log-level', default=None, help='Logging level override (DEBUG, INFO, WARNING, ERROR)')
@click.option('--log-file', type=click.Path(), help='Optional log file path')
def run(run_settings_file, log_level, log_file):
    """
    Run calculations using the specified configuration file.

    RUN_SETTINGS_FILE: Path to run settings YAML file
    """
    try:
        # Load engine configuration from fixed path
        config_loader = ConfigLoader()
        config = config_loader.load_engine_config(str(ENGINE_CONFIG_PATH))

        # Apply engine config logging by default, with CLI overrides when provided
        effective_log_level = log_level or config.log_level
        effective_log_file = log_file or config.log_file

        # Set up logging
        logger = setup_logging(effective_log_level, effective_log_file)

        # Load run settings from command argument
        run_settings = config_loader.load_run_settings(run_settings_file)

        config.run_settings = run_settings

        config_loader.validate_config(config)

        logger.info(f"Loaded engine config from {ENGINE_CONFIG_PATH}")
        logger.info(f"Loaded run settings from {run_settings_file}")
        logger.debug(f"Using log level: {effective_log_level}")
        if effective_log_file:
            logger.debug(f"Using log file: {effective_log_file}")

        # Initialize and run engine
        engine = CalculationEngine(config)
        engine.initialize()

        results = engine.run()

        # Print summary
        summary = engine.get_execution_summary()
        click.echo("\nExecution Summary:")
        click.echo(f"Total modules: {summary['total_modules']}")
        click.echo(f"Successful: {summary['successful']}")
        click.echo(f"Warnings: {summary['warnings']}")
        click.echo(f"Errors: {summary['errors']}")

        # Exit with error code if there were failures
        if summary['errors'] > 0:
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('run_settings_file', type=click.Path(exists=True))
def validate(run_settings_file):
    """
    Validate configuration file without running calculations.

    RUN_SETTINGS_FILE: Path to run settings YAML file
    """
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_engine_config(str(ENGINE_CONFIG_PATH))
        config.run_settings = config_loader.load_run_settings(run_settings_file)
        config_loader.validate_config(config)

        click.echo(f"Configuration is valid")
        click.echo(f"Engine config: {ENGINE_CONFIG_PATH}")
        click.echo(f"Run settings: {run_settings_file}")
        click.echo(f"Modules configured: {len(config.run_settings.modules)}")
        click.echo(f"Input source: {config.run_settings.input.source}")
        click.echo(f"Output destinations: {len(config.run_settings.output.destinations)}")

    except Exception as e:
        click.echo(f"Configuration validation failed: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('run_settings_file', type=click.Path(exists=True))
def list_modules(run_settings_file):
    """
    List all modules defined in the configuration file.

    RUN_SETTINGS_FILE: Path to run settings YAML file
    """
    try:
        config_loader = ConfigLoader()
        config = config_loader.load_engine_config(str(ENGINE_CONFIG_PATH))
        config.run_settings = config_loader.load_run_settings(run_settings_file)

        click.echo("Configured Modules:")
        for module in config.run_settings.modules:
            status = "enabled" if module.enabled else "disabled"
            click.echo(f"  - {module.name} ({module.class_path}) [{status}]")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI application."""
    cli()


if __name__ == '__main__':
    main()
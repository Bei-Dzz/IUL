"""
Tests for CLI functionality.
"""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch

from src.actuarial_engine import cli, run, validate, list_modules


class TestCLI:
    """Test CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner."""
        return CliRunner()

    def test_cli_main(self, runner):
        """Test main CLI entry point."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Actuarial Calculation Engine' in result.output

    def test_validate_command(self, runner, tmp_path):
        """Test validate command."""
        # Create a valid config file
        config_content = """
engine:
  log_level: INFO
modules:
  - name: test_module
    class: test.module.TestModule
    enabled: true
input:
  source: excel
  file_path: test.xlsx
output:
  destinations:
    - format: csv
      path: output.csv
"""
        config_file = tmp_path / 'test_config.yaml'
        config_file.write_text(config_content)

        result = runner.invoke(validate, [str(config_file)])
        assert result.exit_code == 0
        assert 'is valid' in result.output

    def test_validate_invalid_config(self, runner, tmp_path):
        """Test validate command with invalid config."""
        # Create invalid config (missing required fields)
        config_content = """
engine:
  log_level: INFO
"""
        config_file = tmp_path / 'invalid_config.yaml'
        config_file.write_text(config_content)

        result = runner.invoke(validate, [str(config_file)])
        assert result.exit_code == 1  # Should fail
        assert 'validation failed' in result.output.lower()

    def test_list_modules_command(self, runner, tmp_path):
        """Test list-modules command."""
        config_content = """
engine:
  log_level: INFO
modules:
  - name: module1
    class: test.Module1
    enabled: true
  - name: module2
    class: test.Module2
    enabled: false
input:
  source: excel
  file_path: test.xlsx
output:
  destinations:
    - format: csv
      path: output.csv
"""
        config_file = tmp_path / 'test_config.yaml'
        config_file.write_text(config_content)

        result = runner.invoke(list_modules, [str(config_file)])
        assert result.exit_code == 0
        assert 'module1' in result.output
        assert 'module2' in result.output
        assert 'enabled' in result.output
        assert 'disabled' in result.output

    @patch('src.calculation_layer.engine.CalculationEngine')
    @patch('src.core.config.ConfigLoader')
    def test_run_command_success(self, mock_config_loader, mock_engine_class, runner, tmp_path):
        """Test successful run command."""
        # Mock the configuration loader
        mock_config = Mock()
        mock_config.log_level = 'INFO'
        mock_config.modules = []
        mock_config.input = Mock()
        mock_config.output = Mock()

        mock_config_loader.return_value.load_from_file.return_value = mock_config
        mock_config_loader.return_value.validate_config.return_value = None

        # Mock the engine
        mock_engine_instance = Mock()
        mock_engine_instance.initialize.return_value = None
        mock_engine_instance.run.return_value = [{
            'module_name': 'test_module',
            'status': 'success',
            'errors': [],
            'warnings': []
        }]
        mock_engine_instance.get_execution_summary.return_value = {
            'total_modules': 1,
            'successful': 1,
            'warnings': 0,
            'errors': 0
        }
        mock_engine_class.return_value = mock_engine_instance

        # Create config file
        config_file = tmp_path / 'run_config.yaml'
        config_file.write_text("engine: {log_level: INFO}\nmodules: []\ninput: {source: excel, file_path: test.xlsx}\noutput: {destinations: [{format: csv, path: output.csv}]}")

        result = runner.invoke(run, [str(config_file)])
        assert result.exit_code == 0
        assert 'Execution Summary:' in result.output
        assert 'Successful: 1' in result.output

    @patch('src.calculation_layer.engine.CalculationEngine')
    @patch('src.core.config.ConfigLoader')
    def test_run_command_with_errors(self, mock_config_loader, mock_engine_class, runner, tmp_path):
        """Test run command when execution has errors."""
        # Similar setup but with errors
        mock_config = Mock()
        mock_config.log_level = 'INFO'
        mock_config.modules = []
        mock_config.input = Mock()
        mock_config.output = Mock()

        mock_config_loader.return_value.load_from_file.return_value = mock_config

        mock_engine_instance = Mock()
        mock_engine_instance.initialize.return_value = None
        mock_engine_instance.run.return_value = [{
            'module_name': 'test_module',
            'status': 'error',
            'errors': ['Test error'],
            'warnings': []
        }]
        mock_engine_instance.get_execution_summary.return_value = {
            'total_modules': 1,
            'successful': 0,
            'warnings': 0,
            'errors': 1
        }
        mock_engine_class.return_value = mock_engine_instance

        config_file = tmp_path / 'error_config.yaml'
        config_file.write_text("engine: {log_level: INFO}\nmodules: []\ninput: {source: excel, file_path: test.xlsx}\noutput: {destinations: [{format: csv, path: output.csv}]}")

        result = runner.invoke(run, [str(config_file)])
        assert result.exit_code == 1  # Should exit with error
        assert 'Errors: 1' in result.output
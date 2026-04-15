"""
Integration tests for the actuarial calculation engine.
"""

import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path

from src.core.config import ConfigLoader
from src.calculation_layer.engine import CalculationEngine


class TestIntegration:
    """Integration tests for end-to-end functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_config(self, temp_dir):
        """Create sample configuration for testing."""
        config_data = {
            'engine': {
                'log_level': 'DEBUG'
            },
            'modules': [{
                'name': 'sample_product_cf',
                'class': 'examples.modules.sample_product_cf_module.SampleProductCFModule',
                'enabled': True
            }],
            'input': {
                'source': 'excel',
                'file_path': 'examples/data/sample_data.xlsx'
            },
            'output': {
                'destinations': [{
                    'format': 'csv',
                    'path': str(temp_dir / 'results.csv')
                }, {
                    'format': 'json',
                    'path': str(temp_dir / 'results.json')
                }]
            }
        }
        return config_data

    def test_config_loading(self, sample_config):
        """Test configuration loading and validation."""
        loader = ConfigLoader()

        # This would normally load from file, but we'll test the parsing
        config = loader._parse_config(sample_config)
        loader.validate_config(config)

        assert config.log_level == 'DEBUG'
        assert len(config.modules) == 1
        assert config.modules[0].name == 'sample_product_cf'
        assert config.input.source == 'excel'
        assert len(config.output.destinations) == 2

    def test_engine_initialization(self, sample_config, temp_dir):
        """Test engine initialization with sample config."""
        # Create a temporary config file
        config_file = temp_dir / 'test_config.yaml'
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(sample_config, f)

        # Load and initialize engine
        loader = ConfigLoader()
        config = loader.load_from_file(str(config_file))

        engine = CalculationEngine(config)

        # This should not raise an error
        engine.initialize()

        # Check that handlers were created
        assert engine.input_handler is not None
        assert engine.output_handler is not None

        # Check that module was loaded
        assert 'sample_product_cf' in engine.registry._modules

    def test_end_to_end_calculation(self, temp_dir):
        """Test complete end-to-end calculation (requires sample data file)."""
        # This test requires the sample Excel file to exist
        excel_file = Path('examples/data/sample_data.xlsx')
        if not excel_file.exists():
            pytest.skip("Sample Excel file not found - run generate_sample_data.xlsx first")

        # Create config
        config_data = {
            'engine': {'log_level': 'INFO'},
            'modules': [{
                'name': 'sample_product_cf',
                'class': 'examples.modules.sample_product_cf_module.SampleProductCFModule',
                'enabled': True
            }],
            'input': {
                'source': 'excel',
                'file_path': str(excel_file)
            },
            'output': {
                'destinations': [{
                    'format': 'csv',
                    'path': str(temp_dir / 'sample_product_cf_results.csv')
                }]
            }
        }

        config_file = temp_dir / 'integration_config.yaml'
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config_data, f)

        # Run calculation
        loader = ConfigLoader()
        config = loader.load_from_file(str(config_file))

        engine = CalculationEngine(config)
        engine.initialize()
        results = engine.run()

        # Check results
        assert len(results) == 1  # One module
        assert results[0]['status'] == 'success'
        assert results[0]['module_name'] == 'sample_product_cf'

        # Check output file was created
        output_file = temp_dir / 'sample_product_cf_results.csv'
        assert output_file.exists()

        # Check output content
        output_df = pd.read_csv(output_file)
        assert len(output_df) > 0
        assert 'model_point_id' in output_df.columns
        assert 'product_name' in output_df.columns
        assert 'present_value_discounted_premium_cash_flow' in output_df.columns

    def test_multiple_output_formats(self, temp_dir):
        """Test output to multiple formats."""
        # Similar to above but check both CSV and JSON outputs
        excel_file = Path('examples/data/sample_data.xlsx')
        if not excel_file.exists():
            pytest.skip("Sample Excel file not found")

        config_data = {
            'engine': {'log_level': 'INFO'},
            'modules': [{
                'name': 'sample_product_cf',
                'class': 'examples.modules.sample_product_cf_module.SampleProductCFModule',
                'enabled': True
            }],
            'input': {
                'source': 'excel',
                'file_path': str(excel_file)
            },
            'output': {
                'destinations': [
                    {'format': 'csv', 'path': str(temp_dir / 'results.csv')},
                    {'format': 'json', 'path': str(temp_dir / 'results.json')}
                ]
            }
        }

        config_file = temp_dir / 'multi_output_config.yaml'
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config_data, f)

        loader = ConfigLoader()
        config = loader.load_from_file(str(config_file))

        engine = CalculationEngine(config)
        engine.initialize()
        engine.run()

        # Check both output files exist
        assert (temp_dir / 'results.csv').exists()
        assert (temp_dir / 'results.json').exists()

        # Check JSON content
        import json
        with open(temp_dir / 'results.json', 'r') as f:
            json_data = json.load(f)

        assert 'sample_product_cf_results' in json_data
        assert len(json_data['sample_product_cf_results']) > 0
# Actuarial Calculation Engine

A modular Python engine for actuarial calculations with configurable input/output layers and plug-in calculation modules.

The current sample implementation reads model data from Excel and writes results to CSV and JSON.

## Features

- **Modular Architecture**: 6-layer design with input, calculation, and output layers
- **Flexible Input**: Excel workbooks or PostgreSQL databases
- **Multiple Outputs**: CSV, JSON, and PostgreSQL
- **Extensible Modules**: User-created calculation modules inherit from abstract base class
- **Actuarial Libraries**: Common functions like cash flow discounting
- **CLI Interface**: Command-line execution with YAML configuration
- **Testing**: Comprehensive unit and integration tests

## Quick Start

### 1. Prerequisites

- Python 3.11+
- pip

### 2. Create and Activate a Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate Sample Input Data

```bash
python examples/data/generate_sample_data.py
```

### 5. Run the Engine

Recommended (works directly from source):

```bash
python -m src.actuarial_engine run config/run_settings.yaml
```

### 6. Check Results

Results will be saved to the path specified in the run settings.

## Architecture

### Layers

1. **Input Repository**: Excel files or PostgreSQL tables
2. **Input Layer**: InputHandler encapsulates data access
3. **Calculation Layer**: CalculationEngine orchestrates modules
4. **Calculation Modules**: User-created modules inheriting AbstractCalculationModule
5. **Actuarial Libraries**: Common functions (e.g., cash flow discounting)
6. **Output Layer**: OutputHandler manages result storage

### Example Module

See `examples/modules/sample_product_cf_module.py` for a complete working example that:

- Loads model point and assumption data
- Projects life decrements and premium cash flows
- Outputs results to CSV/JSON/PostgreSQL

## Model run configuration

Example `config/run_settings.yaml`:

```yaml
modules:
  - name: sample_product_cf
    class: examples.modules.sample_product_cf_module.SampleProductCFModule
    enabled: true

input:
  source: excel
  file_path: examples/data/sample_data.xlsx

output:
  destinations:
    - format: csv
      path: output/sample_product_cf_results.csv
    - format: json
      path: output/sample_product_cf_results.json

cash_flow_projection:
  projection_horizon_years: 100
  time_step_per_year: 12

assumption_table_name: "202512 BE assumptions"
```

## CLI Commands

Available command group:

```bash
python -m src.actuarial_engine --help
```

Working command:

```bash
python -m src.actuarial_engine run config/run_settings.yaml
```

Note: `engine_config.yaml` is loaded from a fixed path in the program (`config/engine_config.yaml`), while `run_settings.yaml` is provided as the command argument.

The project also declares a console script named actuarial-engine in pyproject.toml.
If your environment installs the package successfully, you can run:

```bash
# Run calculations
actuarial-engine run config/run_settings.yaml

# Validate configuration
actuarial-engine validate config/run_settings.yaml

# List configured modules
actuarial-engine list-modules config/run_settings.yaml

# Show help
actuarial-engine --help
```

## Logging

The engine uses Python logging and writes logs to console by default. Log settings are loaded from `config/engine_config.yaml` and can be overridden from the command line.

Example `config/engine_config.yaml`:

```yaml
engine:
  log_level: DEBUG
  log_file: logs/engine.log
```

Run using the log settings from engine config:

```bash
python -m src.actuarial_engine run config/run_settings.yaml
```

Override log settings from CLI (takes precedence over engine config):

```bash
python -m src.actuarial_engine run config/run_settings.yaml --log-level INFO --log-file logs/custom.log
```

PowerShell commands to inspect logs:

```powershell
# Print file contents
Get-Content logs/engine.log

# Tail logs in real time
Get-Content logs/engine.log -Wait
```

Note: If the configured log directory does not exist, it is created automatically.

### Log Levels

- `DEBUG`: Detailed diagnostic events (module registration, data loading, internal calculation steps). Best for troubleshooting.
- `INFO`: High-level progress events (engine start, module execution, completion summary). Recommended for routine runs.
- `WARNING`: Non-fatal issues that need attention, but the run can continue.
- `ERROR`: Failures in part of the workflow (for example, module or output write errors).
- `CRITICAL`: Severe failures indicating the process may not continue safely.

Only events at or above the selected level are emitted. For example, `INFO` includes INFO/WARNING/ERROR/CRITICAL but excludes DEBUG.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_cash_flow_utility.py

# Run with coverage
pytest --cov=src --cov-report=html
```

### Creating Custom Modules

1. Inherit from AbstractCalculationModule in src/core/base.py.
2. Implement execute(self).
3. Read inputs via self.input_handler.get_data(...) or self.input_handler.get_dataframe(...).
4. Write outputs via self.output_handler.write(key, data).
5. Set status with self.log_success(), self.log_warning(...), or self.log_error(...).

Minimal example:

```python
from src.core.base import AbstractCalculationModule


class MyModule(AbstractCalculationModule):
    def execute(self):
        df = self.input_handler.get_dataframe("model_point")
        self.output_handler.write("my_results", df.head(10))
        self.log_success()
```

## Project Structure

```text
actuarial-calculation-engine/
|-- src/
|   |-- actuarial_engine.py
|   |-- calculation_layer/
|   |-- core/
|   |-- input_layer/
|   |-- output_layer/
|   |-- libraries/
|-- config/
|   |-- engine_config.yaml
|   |-- run_settings.yaml
|-- examples/
|   |-- configs/
|   |-- data/
|   |-- modules/
|   `-- output/
|-- logs/
|-- output/
|-- spec/
|-- tests/
|-- validation/
|-- .gitignore
|-- original_plan.md
|-- requirements.txt
|-- pyproject.toml
|-- setup.py
`-- README.md
```

## License

This project is provided as-is for educational and demonstration purposes.

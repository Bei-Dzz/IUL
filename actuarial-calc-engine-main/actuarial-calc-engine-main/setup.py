#!/usr/bin/env python3
"""
Setup script for the Actuarial Calculation Engine.

This script helps set up the development environment and generates sample data.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(e.stderr)
        return None

def main():
    """Main setup function."""
    print("Actuarial Calculation Engine Setup")
    print("=" * 40)

    project_root = Path(__file__).parent

    # Check Python version
    if sys.version_info < (3, 11):
        print(f"✗ Python 3.11+ required. Current version: {sys.version}")
        sys.exit(1)

    print(f"✓ Python version: {sys.version}")

    # Create virtual environment
    venv_path = project_root / "venv"
    if not venv_path.exists():
        run_command(f'python -m venv "{venv_path}"', "Creating virtual environment")
    else:
        print("✓ Virtual environment already exists")

    # Activate virtual environment and install dependencies
    pip_path = venv_path / "Scripts" / "pip" if os.name == 'nt' else venv_path / "bin" / "pip"
    python_path = venv_path / "Scripts" / "python" if os.name == 'nt' else venv_path / "bin" / "python"

    requirements_file = project_root / "requirements.txt"
    if requirements_file.exists():
        run_command(f'"{python_path}" -m pip install -r "{requirements_file}"',
                   "Installing dependencies")
    else:
        print("✗ requirements.txt not found")

    # Generate sample data
    data_script = project_root / "examples" / "data" / "generate_sample_data.py"
    if data_script.exists():
        run_command(f'"{python_path}" "{data_script}"', "Generating sample data")
    else:
        print("✗ Sample data generation script not found")

    # Run basic tests
    run_command(f'"{python_path}" -m pytest tests/test_cash_flow_utility.py -v',
               "Running basic tests")

    print("\nSetup completed successfully!")
    print("\nTo activate the virtual environment:")
    if os.name == 'nt':
        print(f'    venv\\Scripts\\activate')
    else:
        print(f'    source venv/bin/activate')
    print("\nTo run the engine:")
    print("    actuarial-engine run config/engine_config.yaml")
    print("\nTo run tests:")
    print("    pytest")

if __name__ == '__main__':
    main()
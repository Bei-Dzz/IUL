"""
Calculation engine and module management.
"""

import importlib
import pandas as pd
from typing import Any, Dict, List, Type
from pathlib import Path

from ..core.base import AbstractCalculationModule
from ..core.config import EngineConfig, ModuleConfig
from ..core.exceptions import ModuleLoadError, CalculationError
from ..core.logging import logger
from ..input_layer.handler import InputHandler
from ..output_layer.handler import OutputHandler


class ModuleRegistry:
    """Registry for managing calculation modules."""

    def __init__(self):
        self._modules: Dict[str, Type[AbstractCalculationModule]] = {}

    def register(self, name: str, module_class: Type[AbstractCalculationModule]) -> None:
        """
        Register a module class.

        Args:
            name: Module name
            module_class: Module class (must inherit from AbstractCalculationModule)
        """
        if not issubclass(module_class, AbstractCalculationModule):
            raise ModuleLoadError(f"Module class {module_class} must inherit from AbstractCalculationModule")

        self._modules[name] = module_class
        logger.debug(f"Registered module: {name}")

    def get(self, name: str) -> Type[AbstractCalculationModule]:
        """
        Get a registered module class.

        Args:
            name: Module name

        Returns:
            Module class

        Raises:
            ModuleLoadError: If module not found
        """
        if name not in self._modules:
            available = list(self._modules.keys())
            raise ModuleLoadError(f"Module '{name}' not found. Available: {available}")
        return self._modules[name]

    def list_modules(self) -> List[str]:
        """List all registered module names."""
        return list(self._modules.keys())


class ModuleLoader:
    """Loader for dynamically importing and registering modules."""

    def __init__(self, registry: ModuleRegistry):
        """
        Initialize module loader.

        Args:
            registry: Module registry to populate
        """
        self.registry = registry

    def load_from_config(self, modules_config: List[ModuleConfig]) -> None:
        """
        Load modules from configuration.

        Args:
            modules_config: List of module configurations
        """
        for module_config in modules_config:
            if not module_config.enabled:
                logger.debug(f"Skipping disabled module: {module_config.name}")
                continue

            try:
                module_class = self._import_class(module_config.class_path)
                self.registry.register(module_config.name, module_class)
                logger.info(f"Loaded module: {module_config.name} ({module_config.class_path})")
            except Exception as e:
                raise ModuleLoadError(f"Failed to load module '{module_config.name}': {e}")

    def _import_class(self, class_path: str) -> Type[AbstractCalculationModule]:
        """
        Import a class from a dotted path.

        Args:
            class_path: Dotted path to the class (e.g., 'examples.modules.BondPricingModule')

        Returns:
            The imported class

        Raises:
            ModuleLoadError: If import fails
        """
        try:
            module_path, class_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)

            if not isinstance(cls, type) or not issubclass(cls, AbstractCalculationModule):
                raise ModuleLoadError(f"Class {class_path} is not a subclass of AbstractCalculationModule")

            return cls

        except (ImportError, AttributeError, ValueError) as e:
            raise ModuleLoadError(f"Failed to import class {class_path}: {e}")


class CalculationEngine:
    """
    Main calculation engine that orchestrates module execution.

    Loads modules from configuration, creates input/output handlers,
    and executes calculations in sequence.
    """

    def __init__(self, config: EngineConfig):
        """
        Initialize calculation engine.

        Args:
            config: Engine configuration
        """
        self.config = config
        self.registry = ModuleRegistry()
        self.loader = ModuleLoader(self.registry)
        self.input_handler = None
        self.output_handler = None
        self.execution_results: List[Dict[str, Any]] = []

    def initialize(self) -> None:
        """
        Initialize the engine components.

        Loads modules, creates input/output handlers.
        """
        logger.info("Initializing calculation engine...")

        # Load modules
        self.loader.load_from_config(self.config.run_settings.modules)

        # Create input handler
        from ..input_layer.handler import create_input_handler
        self.input_handler = create_input_handler(self.config.run_settings.input)

        # Create output handler
        from ..output_layer.handler import create_output_handler
        self.output_handler = create_output_handler(self.config.run_settings.output)

        logger.info("Engine initialization complete")

    def run(self) -> List[Dict[str, Any]]:
        """
        Execute all enabled calculation modules.

        Returns:
            List of execution results for each module
        """
        if not self.input_handler or not self.output_handler:
            raise CalculationError("Engine not initialized. Call initialize() first.")

        logger.info("Starting calculation execution...")

        self.execution_results = []

        for module_config in self.config.run_settings.modules:
            if not module_config.enabled:
                continue

            try:
                logger.info(f"Executing module: {module_config.name}")

                # Get module class and instantiate
                module_class = self.registry.get(module_config.name)
                module = module_class(
                    name=module_config.name,
                    input_handler=self.input_handler,
                    output_handler=self.output_handler,
                    config=self.config
                )

                # Execute module
                module.execute()

                # Get results
                results = module.get_results()
                self.execution_results.append(results)

                status = results.get('status', 'unknown')
                logger.info(f"Module {module_config.name} completed with status: {status}")

            except Exception as e:
                error_result = {
                    "module_name": module_config.name,
                    "status": "error",
                    "errors": [str(e)],
                    "warnings": [],
                    "execution_timestamp": pd.Timestamp.now()
                }
                self.execution_results.append(error_result)
                logger.error(f"Module {module_config.name} failed: {e}")

        # Close output handlers
        if self.output_handler:
            self.output_handler.close()

        logger.info("Calculation execution complete")
        return self.execution_results

    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of execution results.

        Returns:
            Summary dictionary with counts by status
        """
        if not self.execution_results:
            return {"total_modules": 0, "executed": 0, "successful": 0, "warnings": 0, "errors": 0}

        total = len(self.execution_results)
        successful = sum(1 for r in self.execution_results if r.get('status') == 'success')
        warnings = sum(1 for r in self.execution_results if r.get('status') == 'warning')
        errors = sum(1 for r in self.execution_results if r.get('status') == 'error')

        return {
            "total_modules": total,
            "executed": total,
            "successful": successful,
            "warnings": warnings,
            "errors": errors
        }
## Plan: Actuarial Calculation Engine (Python) — REVISED WITH SAMPLE MODULE

**TL;DR**
Build a modular Python calculation engine for actuarial calculations (life insurance, investment modeling) with a 6-layer architecture. Greenfield project targeting Python 3.11+. Support Excel/PostgreSQL inputs, output to PostgreSQL/CSV/JSON. Implement as a library with CLI interface, using explicit YAML config for module registration. Use venv for environment, all dependencies in requirements.txt.

### Steps (Grouped by Implementation Phase)

**PHASE 1: Core Infrastructure & Environment Setup** *(can run in parallel - A & B)*

*A. Project Structure & Python Environment*
1. Create project directory structure with src layout
2. Initialize venv: `python -m venv venv`
3. Create `requirements.txt` with all dependencies:
   - pandas
   - sqlalchemy
   - openpyxl
   - pyyaml
   - click (for CLI)
   - pytest (testing)
4. Define shared utilities: custom exceptions, logging config, enum types (OutputFormat, CalculationStatus)

*B. Configuration & CLI Framework*
1. Design YAML config schema for module registration, input source, output destinations
2. Create ConfigLoader to parse/validate config files
3. Create CLI entry point (Click library) with commands: `run`, `list-modules`, `validate`

**PHASE 2: Input Layer** *(depends on Phase 1)*
1. Create abstract `RepositoryReader` base class
2. Implement `ExcelRepository` (openpyxl-based) and `PostgreSQLRepository` (SQLAlchemy-based)
3. Implement `InputHandler` class with lazy-load by key and caching

**PHASE 3: Output Layer** *(depends on Phase 1)*
1. Create abstract `OutputWriter` base class
2. Implement `CSVWriter`, `JSONWriter`, `PostgreSQLWriter`
3. Implement `OutputHandler` class routing to appropriate writers

**PHASE 4: Calculation Module Framework** *(depends on Phase 1, 2, 3)*
1. Create `AbstractCalculationModule` base class with template methods
2. Implement `ModuleRegistry` and `ModuleLoader` (loads from YAML config)
3. Implement `CalculationEngine` orchestrator

**PHASE 5: Sample Actuarial Library** *(depends on Phase 1)*
- Create `cash_flow_projection_utility.py` with one sample function: `discount_cash_flows(flows, discount_rate_curve, times)`
- Template showing how users structure utility libraries with docstrings and clear extensibility comments

**PHASE 6: Sample Calculation Module** *(depends on Phase 4, 5)*

Create **`BondPricingModule`** calculation module (concrete working example):

*Purpose*: Calculate bond prices using cash flow projections and discount rates

*Inherits from*: AbstractCalculationModule

*Functionality*:
1. Retrieve bond data from input handler (bond_id, coupon_rate, maturity_years, face_value, frequency)
2. Retrieve discount rate curves from input handler
3. Generate bond cash flows (coupons at each period + principal at maturity)
4. Call `discount_cash_flows()` from `cash_flow_projection_utility` library
5. Calculate bond price (NPV of cash flows) and effective duration
6. Write results (bond_id, price, duration) to output handler

*Example Usage*: Load sample bonds from Excel, calculate prices with discount curves, output to CSV/JSON/PostgreSQL

Supporting materials:
- `examples/data/sample_bonds.xlsx` — test data with bond parameters and discount rates
- `examples/configs/bond_pricing_config.yaml` — YAML config registering BondPricingModule
- `tests/test_bond_pricing_module.py` — unit tests with mock inputs

**PHASE 7: Testing & Validation** *(depends on all phases)*
1. Unit tests for each layer
2. Integration test: Excel input → BondPricingModule → output to all 3 formats
3. CLI test: `actuarial-engine run config.yaml` produces correct output
4. Performance tests

### Relevant Files

**Environment & Dependencies**
- `requirements.txt` — all Python dependencies

**Core & Configuration**
- `src/core/base.py` — abstract classes
- `src/core/config.py` — ConfigLoader class
- `src/core/exceptions.py` — custom exception types
- `src/core/logging.py` — logging setup

**Input Layer**
- `src/input_layer/repository.py` — ExcelRepository, PostgreSQLRepository
- `src/input_layer/handler.py` — InputHandler class

**Output Layer**
- `src/output_layer/writer.py` — CSVWriter, JSONWriter, PostgreSQLWriter
- `src/output_layer/handler.py` — OutputHandler class

**Calculation**
- `src/calculation_layer/engine.py` — CalculationEngine, ModuleRegistry, ModuleLoader
- `src/calculation_layer/module.py` — AbstractCalculationModule

**Libraries**
- `src/libraries/cash_flow_projection_utility.py` — sample library with `discount_cash_flows()` function

**CLI & Config**
- `src/cli.py` — CLI entry point
- `config/engine_config.yaml` — example config with BondPricingModule

**Examples & Tests**
- `examples/modules/bond_pricing_module.py` — BondPricingModule implementation
- `examples/data/sample_bonds.xlsx` — sample Excel with bond data and discount curves
- `examples/configs/bond_pricing_config.yaml` — example config
- `tests/test_cash_flow_utility.py` — library function tests
- `tests/test_bond_pricing_module.py` — module unit tests
- `tests/test_calculation_engine.py` — integration tests
- `tests/test_cli.py` — CLI tests

### Sample Module Detail: BondPricingModule

**Input Data Expected** (from input handler):
- `bond_data`: DataFrame with [bond_id, coupon_rate, maturity_years, face_value, frequency]
- `discount_rates`: DataFrame with [tenor_years, discount_rate] for yield curve

**Calculation Logic**:
1. For each bond, generate cash flows (coupons + principal)
2. Interpolate discount rates to match cash flow dates
3. Call utility: `discount_cash_flows(cash_flows, interpolated_rates, time_periods)`
4. Calculate effective duration using NPV derivative

**Output** (to output handler):
- DataFrame: [bond_id, bond_price, effective_duration, calculation_timestamp]

**Error Handling**: Module logs warnings for invalid data, continues with valid records

### Verification

1. **Unit Tests** — cash_flow_projection_utility function, BondPricingModule logic with mock inputs
2. **Integration Test** — End-to-end: sample_bonds.xlsx → module → CSV/JSON/PostgreSQL outputs match
3. **CLI Test** — `actuarial-engine run bond_pricing_config.yaml` produces all output formats
4. **Manual Test** — Verify bond prices match Excel/Bloomberg benchmarks
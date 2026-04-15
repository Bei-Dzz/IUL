"""
Cash Flow Projection Utility Library

This library provides common actuarial functions for cash flow projections and discounting.
Users can import and use these functions in their custom calculation modules.

Example usage in a calculation module:
    from src.libraries.cash_flow_projection_utility import discount_cash_flows

    # In execute() method:
    discounted_values = discount_cash_flows(cash_flows, discount_rates, time_periods)
"""

import numpy as np
import pandas as pd
from typing import List, Union, Optional

from ..core.exceptions import CalculationError
from ..core.logging import logger


def discount_cash_flows(
    cash_flows: Union[List[float], np.ndarray, pd.Series],
    discount_rate_curve: Union[List[float], np.ndarray, pd.Series, float],
    time_periods: Union[List[float], np.ndarray, pd.Series, Optional[int]] = None,
    time_step_per_year: int = 1,
    rate_type: str = 'spot',
    cf_timing: str = 'end'
) -> float:
    """
    Discount a series of cash flows using a discount rate curve.

    This function calculates the present value of a sequence of cash flows.
    The discount_rate_curve is assumed to contain annual rates, and rates are
    converted to the appropriate period rate using time_step_per_year.

    Args:
        cash_flows: Array of cash flow amounts
        discount_rate_curve: Annual discount rates (can be single rate or curve)
        time_periods: Time periods for each cash flow in years (if None, assumes 1, 2, ... in the chosen time unit)
        time_step_per_year: Number of time steps per year (1=annual, 2=semi-annual,
                           4=quarterly, 12=monthly, etc.). Default is 1 (annual).
        rate_type: Indicates whether the supplied rates are 'spot' rates or 'forward' rates.
                   Default is 'spot'.
        cf_timing: Indicates whether cash flows occur at 'end' or 'beginning' of period.
                   Default is 'end'. Beginning-of-period flows are discounted one period less.

    Returns:
        Present value of the cash flows as a single float.

    Raises:
        CalculationError: If inputs are invalid

    Example:
        # Monthly cash flows with annual discount rates
        cash_flows = [100] * 12
        annual_rates = [0.05] * 12
        time_periods = np.arange(1/12, 1 + 1/12, 1/12)
        pv = discount_cash_flows(cash_flows, annual_rates, time_periods, time_step_per_year=12)

        # Annual cash flows (default)
        cash_flows = [100, 100, 1100]
        pv = discount_cash_flows(cash_flows, 0.05)
    """
    try:
        cf = np.asarray(cash_flows, dtype=float)

        if np.isscalar(discount_rate_curve):
            rates = np.full(len(cf), discount_rate_curve)
        else:
            rates = np.asarray(discount_rate_curve, dtype=float)

        if len(cf) != len(rates):
            raise CalculationError(
                f"Cash flows ({len(cf)}) and discount rates ({len(rates)}) must have same length"
            )

        if len(cf) == 0:
            return 0.0

        if time_step_per_year <= 0:
            raise CalculationError("time_step_per_year must be positive")

        if time_step_per_year != 1:
            rates = np.power(1.0 + rates, 1.0 / time_step_per_year) - 1.0

        if time_periods is None:
            periods = np.arange(1, len(cf) + 1, dtype=float)
        elif np.isscalar(time_periods):
            periods = np.arange(time_periods, time_periods * (len(cf) + 1), time_periods)[1:]
        else:
            periods = np.asarray(time_periods, dtype=float)

        if len(periods) != len(cf):
            raise CalculationError(
                f"Time periods ({len(periods)}) must match cash flows ({len(cf)})"
            )

        if time_step_per_year != 1:
            periods = periods * time_step_per_year

        cf_timing = cf_timing.lower()
        if cf_timing not in ['end', 'beginning']:
            raise CalculationError("cf_timing must be 'end' or 'beginning'")

        if cf_timing == 'beginning':
            # Beginning-of-period cash flows are discounted one time step less
            periods = np.maximum(periods - 1.0, 0.0)

        rate_type = rate_type.lower()
        if rate_type not in ['spot', 'forward']:
            raise CalculationError("rate_type must be 'spot' or 'forward'")

        if rate_type == 'spot':
            discount_factors = 1.0 / np.power(1.0 + rates, periods)
        else:
            # Treat the provided rates as forward rates for each interval.
            # Forward rates are applied sequentially to build the discount factor
            # for each cash flow.
            interval_lengths = np.diff(np.concatenate([[0.0], periods]))
            if len(interval_lengths) != len(rates):
                raise CalculationError(
                    f"Forward rates ({len(rates)}) must match cash flow intervals ({len(interval_lengths)})"
                )
            cumulative_factors = np.cumprod(np.power(1.0 + rates, interval_lengths))
            discount_factors = 1.0 / cumulative_factors

        discounted_cf = cf * discount_factors
        present_value = float(np.sum(discounted_cf))

        logger.debug(f"Discounted {len(cf)} cash flows to present value using time_step_per_year={time_step_per_year}")
        return present_value

    except Exception as e:
        raise CalculationError(f"Error in discount_cash_flows: {e}")


def life_decrement_projection(
    projection_horizon_years: int,
    product_name: str,
    product_variation: str,
    issue_age: int,
    sex: str,
    initial_duration_months: int,
    initial_policies: float,
    mortality_table: dict,  # {(age: int, sex: str): float}
    lapse_table: dict  # {(product_name: str, product_variation: str, policy_year: int): float}
) -> pd.DataFrame:
    """
    Project life decrements (survivorship) using mortality and lapse rates.

    This function performs monthly projections of policy inforce, deaths, and lapses
    based on the specified actuarial assumptions and model point data.

    Args:
        projection_horizon_years: Projection horizon in years
        product_name: Name of the product
        product_variation: Product variation (e.g., '5-pay')
        issue_age: Issue age of the insured
        sex: Sex of the insured ('M' or 'F')
        initial_duration_months: Initial policy duration in months
        initial_policies: Initial number of policies (can be fractional)
        mortality_table: Dictionary with keys (age, sex) mapping to annual mortality rates
        lapse_table: Dictionary with keys (product_name, product_variation, policy_year) mapping to annual lapse rates

    Returns:
        DataFrame with columns:
        - month: Month number (0 to total_months)
        - inforce_end: Number of policies inforce at end of month
        - deaths: Number of deaths in the month
        - lapses: Number of lapses in the month

    Raises:
        CalculationError: If inputs are invalid or required rates not found

    Example:
        mortality_table = {(30, 'M'): 0.001, (31, 'M'): 0.0012, ...}
        lapse_table = {('Term Life', '10-pay', 1): 0.05, ...}
        result = life_decrement_projection(10, 'Term Life', '10-pay', 30, 'M', 0, 1000, mortality_table, lapse_table)
    """
    try:
        # Input validation
        if projection_horizon_years <= 0:
            raise CalculationError("Projection horizon must be positive")
        if initial_policies < 0:
            raise CalculationError("Initial policies cannot be negative")
        if sex not in ['M', 'F']:
            raise CalculationError("Sex must be 'M' or 'F'")

        total_months = projection_horizon_years * 12
        inforce = np.zeros(total_months + 1)
        deaths = np.zeros(total_months + 1)
        lapses = np.zeros(total_months + 1)

        inforce[0] = initial_policies

        for month in range(1, total_months + 1):
            current_duration_months = initial_duration_months + month
            # Policy year: years since issue, starting from 1
            policy_year = (current_duration_months - 1) // 12 + 1
            # Attained age is based on policy year
            attained_age = issue_age + policy_year - 1

            # Look up mortality rate
            mort_key = (attained_age, sex)
            if mort_key not in mortality_table:
                raise CalculationError(f"Mortality rate not found for age {attained_age}, sex {sex}")
            mort_rate = mortality_table[mort_key]

            # Look up lapse rate
            lapse_key = (product_name, product_variation, policy_year)
            if lapse_key not in lapse_table:
                raise CalculationError(f"Lapse rate not found for {product_name}, {product_variation}, year {policy_year}")
            lapse_rate = lapse_table[lapse_key]

            # Calculate deaths: inforce * (1 - (1 - annual_mort)^(1/12))
            deaths[month] = inforce[month - 1] * (1 - np.power(1 - mort_rate, 1/12))

            # Calculate lapses: only at end of policy year (last month of current policy year)
            if current_duration_months % 12 == 0:
                # Lapses applied to (inforce_previous - deaths)
                lapses[month] = (inforce[month - 1] - deaths[month]) * lapse_rate
            else:
                lapses[month] = 0

            # Update inforce
            inforce[month] = inforce[month - 1] - deaths[month] - lapses[month]

        # Create output DataFrame
        df = pd.DataFrame({
            'month': np.arange(total_months + 1),
            'inforce': inforce,
            'deaths': deaths,
            'lapses': lapses
        })

        logger.debug(f"Projected life decrements for {total_months} months")
        return df

    except Exception as e:
        raise CalculationError(f"Error in life_decrement_projection: {e}")


# Example extension points for users:
"""
To extend this library with your own actuarial functions:

1. Add your function following the pattern above
2. Include proper type hints and docstrings
3. Add input validation
4. Use logger for debugging information
5. Raise CalculationError for invalid inputs
6. Add unit tests in tests/test_cash_flow_utility.py

Example custom function template:

def my_actuarial_function(param1: float, param2: List[float]) -> float:
    '''
    Description of what the function does.

    Args:
        param1: Description of parameter
        param2: Description of parameter

    Returns:
        Description of return value
    '''
    try:
        # Input validation
        if param1 <= 0:
            raise CalculationError("param1 must be positive")

        # Calculation logic
        result = param1 * sum(param2)

        logger.debug(f"Calculated result: {result}")
        return result

    except Exception as e:
        raise CalculationError(f"Error in my_actuarial_function: {e}")
"""
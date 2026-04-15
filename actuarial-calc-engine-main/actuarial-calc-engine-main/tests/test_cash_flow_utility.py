"""
Unit tests for cash flow projection utility functions.
"""

import pytest
import numpy as np
import pandas as pd

from src.libraries.cash_flow_projection_utility import discount_cash_flows
from src.core.exceptions import CalculationError


class TestDiscountCashFlows:
    """Test discount_cash_flows function."""

    def test_single_discount_rate(self):
        """Test with single discount rate."""
        cash_flows = [100, 100, 1100]
        discount_rate = 0.05
        result = discount_cash_flows(cash_flows, discount_rate)

        # Expected present value: 100/1.05 + 100/1.05^2 + 1100/1.05^3
        expected = 100 / 1.05 + 100 / (1.05 ** 2) + 1100 / (1.05 ** 3)

        assert pytest.approx(result, rel=1e-9) == expected

    def test_discount_rate_curve(self):
        """Test with discount rate curve."""
        cash_flows = [100, 100, 1100]
        rates = [0.03, 0.04, 0.05]
        result = discount_cash_flows(cash_flows, rates)

        expected = 100 / 1.03 + 100 / (1.04 ** 2) + 1100 / (1.05 ** 3)

        assert pytest.approx(result, rel=1e-9) == expected

    def test_forward_rate_curve(self):
        """Test discounting with forward rates."""
        cash_flows = [100, 100, 1100]
        forward_rates = [0.03, 0.04, 0.05]

        result = discount_cash_flows(cash_flows, forward_rates, rate_type='forward')

        expected = (
            100 / 1.03
            + 100 / (1.03 * 1.04)
            + 1100 / (1.03 * 1.04 * 1.05)
        )

        assert pytest.approx(result, rel=1e-9) == expected

    def test_custom_time_periods(self):
        """Test with custom time periods."""
        cash_flows = [100, 1100]
        rates = [0.05, 0.05]
        time_periods = [0.5, 2.0]  # 6 months and 2 years

        result = discount_cash_flows(cash_flows, rates, time_periods)

        expected = 100 / (1.05 ** 0.5) + 1100 / (1.05 ** 2.0)

        assert pytest.approx(result, rel=1e-9) == expected

    def test_beginning_of_period_cash_flows(self):
        """Test discounting with beginning-of-period cash flows."""
        cash_flows = [100, 100, 100]
        rate = 0.05
        time_step_per_year = 12  # Monthly

        # End-of-period discounting (default) at periods 1, 2, 3 months
        result_end = discount_cash_flows(
            cash_flows, rate, time_step_per_year=time_step_per_year, cf_timing='end'
        )

        # Beginning-of-period discounting (periods 0, 1, 2 months - one time step earlier)
        result_beginning = discount_cash_flows(
            cash_flows, rate, time_step_per_year=time_step_per_year, cf_timing='beginning'
        )

        # Beginning-of-period should be higher (less discounting)
        assert result_beginning > result_end

        # Verify exact calculation with monthly compounding
        monthly_rate = (1.05 ** (1/12)) - 1
        expected_end = 100 / (1 + monthly_rate) + 100 / ((1 + monthly_rate) ** 2) + 100 / ((1 + monthly_rate) ** 3)
        expected_beginning = 100 + 100 / (1 + monthly_rate) + 100 / ((1 + monthly_rate) ** 2)

        assert pytest.approx(result_end, rel=1e-9) == expected_end
        assert pytest.approx(result_beginning, rel=1e-9) == expected_beginning

    def test_empty_inputs(self):
        """Test with empty inputs."""
        result = discount_cash_flows([], [])
        assert result == 0.0

    def test_mismatched_lengths(self):
        """Test error handling for mismatched input lengths."""
        with pytest.raises(CalculationError):
            discount_cash_flows([100, 100], [0.05])  # Different lengths

    def test_pandas_inputs(self):
        """Test with pandas Series inputs."""
        cash_flows = pd.Series([100, 100, 1100])
        rates = pd.Series([0.05, 0.05, 0.05])

        result = discount_cash_flows(cash_flows, rates)
        assert isinstance(result, float)
        assert result == pytest.approx(100 / 1.05 + 100 / (1.05 ** 2) + 1100 / (1.05 ** 3), rel=1e-9)



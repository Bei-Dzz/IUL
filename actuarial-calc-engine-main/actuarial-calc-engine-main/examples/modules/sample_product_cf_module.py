"""
Sample Product Cash Flow Module

Calculates cash flows for a sample product based on life decrement projections.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any

from src.core.base import AbstractCalculationModule
from src.libraries.cash_flow_projection_utility import life_decrement_projection, discount_cash_flows


class SampleProductCFModule(AbstractCalculationModule):
    """
    Calculation module for sample product cash flow projection.

    Projects life decrements and calculates premium cash flows with discounting.
    """

    def execute(self) -> None:
        """
        Execute the sample product cash flow calculation.
        """
        try:
            # Read input data
            model_point_df = self.input_handler.read_data('model_point')

            # Get configuration
            projection_horizon_years = self.config.run_settings.cash_flow_projection.projection_horizon_years

            # Initialize list to collect results for all model points
            all_results = []

            # Loop through each model point
            for idx, model_point in model_point_df.iterrows():
                # Extract model point information
                product_name = model_point['product_name']
                product_variation = model_point['product_variation']
                issue_age = model_point['issue_age']
                sex = model_point['sex']
                initial_duration_months = model_point['initial_policy_duration_months']
                initial_policies = model_point['initial_number_of_policies']
                ap = model_point['annualised_premium']

                # Read product parameters for this model point
                product_parameters = self.input_handler.read_data('Product parameters')

                # Get product parameters
                premium_payment_term = product_parameters.loc[
                    (product_parameters['product_name'] == product_name) &
                    (product_parameters['product_variation'] == product_variation),
                    'premium_payment_term_years'
                ].iloc[0]

                # Read assumption index for this model point
                assumption_index = self.input_handler.read_data(self.config.run_settings.assumption_table_name)

                # Get assumption table names
                assumptions = assumption_index.loc[
                    assumption_index['product_name'] == product_name
                ].iloc[0]

                mortality_table_name = assumptions['mortality_table']
                lapse_table_name = assumptions['lapse_table']
                discount_table_name = assumptions['discount_table']

                # Read assumption tables for this model point
                mortality_df = self.input_handler.read_data(mortality_table_name)
                lapse_df = self.input_handler.read_data(lapse_table_name)
                discount_df = self.input_handler.read_data(discount_table_name)

                # Convert tables to dictionaries
                mortality_table = {
                    (row['age'], row['sex']): row['rate']
                    for _, row in mortality_df.iterrows()
                }

                lapse_table = {
                    (row['product_name'], row['product_variation'], row['policy_year']): row['rate']
                    for _, row in lapse_df.iterrows()
                }

                discount_rates = {
                    row['year']: row['rate']
                    for _, row in discount_df.iterrows()
                }

                # Project life decrements
                decrement_df = life_decrement_projection(
                    projection_horizon_years=projection_horizon_years,
                    product_name=product_name,
                    product_variation=product_variation,
                    issue_age=issue_age,
                    sex=sex,
                    initial_duration_months=initial_duration_months,
                    initial_policies=initial_policies,
                    mortality_table=mortality_table,
                    lapse_table=lapse_table
                )

                # Calculate premium cash flows
                total_months = projection_horizon_years * 12
                premium_cf = np.zeros(total_months + 1)

                for month in range(1, total_months + 1):
                    current_duration_months = initial_duration_months + month
                    policy_year = (current_duration_months - 1) // 12 + 1

                    # Premium paid at beginning of policy year, within payment term
                    if current_duration_months % 12 == 1 and policy_year <= premium_payment_term:
                        premium_cf[month] = ap * decrement_df.loc[month - 1, 'inforce']

                # Create discount rate array for each month
                discount_rate_array = np.array([
                    discount_rates.get((month - 1) // 12 + 1, 0.0)
                    for month in range(1, total_months + 1)
                ])

                # For each month, calculate the present value of all future premium cash flows
                # This means for month m, PV all cash flows from month m to end of projection
                pv_future_cf = np.zeros(total_months + 1)

                for month_idx in range(total_months + 1):
                    # Cash flows from current month to end (starting from month_idx + 1)
                    future_cf = premium_cf[month_idx + 1:]
                    future_rates = discount_rate_array[month_idx:]
                    
                    # Time periods in years, relative to the current month (beginning of period)
                    time_periods = np.arange(1, len(future_cf) + 1) / 12.0
                    
                    if len(future_cf) > 0 and np.sum(future_cf) > 0:
                        # Discount future cash flows
                        pv_future_cf[month_idx] = discount_cash_flows(
                            cash_flows=future_cf,
                            discount_rate_curve=future_rates,
                            time_periods=time_periods,
                            time_step_per_year=self.config.run_settings.cash_flow_projection.time_step_per_year,
                            cf_timing='beginning'
                        )
                    else:
                        pv_future_cf[month_idx] = 0.0

                # Create output DataFrame for this model point
                model_point_results = pd.DataFrame({
                    'model_point_id': idx + 1,  # 1-based index
                    'product_name': product_name,
                    'product_variation': product_variation,
                    'issue_age': issue_age,
                    'sex': sex,
                    'month': np.arange(0, total_months + 1),
                    'premium_cash_flow': premium_cf,
                    'total_discounted_value_future_premium_cf': pv_future_cf
                })

                all_results.append(model_point_results)

            # Combine all model point results
            if all_results:
                output_df = pd.concat(all_results, ignore_index=True)
            else:
                output_df = pd.DataFrame()

            # Write output
            self.output_handler.write('sample_product_cf', output_df)

            self.log_success()

        except Exception as e:
            self.log_error(f"Error in sample product CF calculation: {str(e)}")
            raise
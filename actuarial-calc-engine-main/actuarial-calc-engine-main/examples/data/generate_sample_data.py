"""
Script to generate sample bond data and discount rates for testing.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def generate_sample_bond_data():
    """Generate sample bond data."""
    np.random.seed(42)  # For reproducible results

    bonds = []
    for i in range(10):
        bond = {
            'bond_id': f'BOND_{i+1:03d}',
            'coupon_rate': np.random.uniform(0.02, 0.08),  # 2% to 8%
            'maturity_years': np.random.randint(5, 30),    # 5 to 30 years
            'face_value': np.random.choice([1000, 5000, 10000]),  # Common face values
            'frequency': np.random.choice([1, 2, 4])       # Annual, semi-annual, quarterly
        }
        bonds.append(bond)

    return pd.DataFrame(bonds)

def generate_sample_discount_rates():
    """Generate sample discount rate curve."""
    # Create a yield curve with some realistic shape
    tenors = np.arange(0.5, 30.5, 0.5)  # 0.5, 1, 1.5, ..., 30 years

    # Base rates with term structure
    base_rates = 0.03 + 0.02 * np.exp(-tenors/10) + 0.001 * tenors

    # Add some noise
    np.random.seed(123)
    rates = base_rates + np.random.normal(0, 0.002, len(tenors))

    # Ensure rates are reasonable
    rates = np.clip(rates, 0.005, 0.10)

    discount_data = pd.DataFrame({
        'tenor_years': tenors,
        'discount_rate': rates
    })

    return discount_data

def main():
    """Generate and save sample data."""
    # Create output directory
    output_dir = Path('examples/data')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate data
    bond_data = generate_sample_bond_data()
    discount_data = generate_sample_discount_rates()

    # Save to Excel
    excel_path = output_dir / 'sample_bonds.xlsx'
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        bond_data.to_excel(writer, sheet_name='bond_data', index=False)
        discount_data.to_excel(writer, sheet_name='discount_rates', index=False)

    print(f"Sample data saved to {excel_path}")
    print(f"Bond data shape: {bond_data.shape}")
    print(f"Discount data shape: {discount_data.shape}")

    # Also save as CSV for reference
    bond_data.to_csv(output_dir / 'sample_bonds_bond_data.csv', index=False)
    discount_data.to_csv(output_dir / 'sample_bonds_discount_rates.csv', index=False)

if __name__ == '__main__':
    main()
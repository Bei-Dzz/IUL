# Cash flow projection for a sample product

This specification outlines the cash flow projection for a sample product.

## Input

### Model point information
1. Product name
2. Product variation (e.g. 5-pay)
3. Issue age of the insured
4. Sex of the insured (M/F)
5. Initial policy duration expressed in month
6. Initial number of policies (can be fractional number)
7. Annualised premium ("AP")

### Parameter table
Table "Product parameters" from the data source, indexed by product name and product variation, which specifies the following:
1. Premium payment term expressed in year

### Assumption index table
Table "202512 BE assumptions" from the data source, indexed by product name, which specifies the following:
1. The table name for the mortality rate table
2. The table name for the lapse rate table
3. The table name for the discount rate table

## Calculation
1. Calculate at monthly time step, over the projection horizon specified in the config.
2. Project the life decrement
3. Starting from month 1 to the end of projection horizon, perform the following calculation:
    1. Calculate the current policy duration in month by incrementing the initial policy duration along the monthly time steps. The current policy year can be calculated by expressing the current policy duration in year.
    2. The premium cash flow in each month is calculated by AP x number of policies inforce at the end of the previous month, only if it is the first month in each policy year within the premium payment term.
4. For each month, calculate the total discounted value of all future premium cash flows with the discount rate assumption. Note that the premium cash flows occur at the beginning of the period.

## Output
- A table containing the projected premium cash flows and the discounted values of the premium cash flows.
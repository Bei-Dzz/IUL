# Life Decrement Model

The life decrement model projects the survivorship (lx) commonly used in the actuarial cash flow projection.

## Input

### from engine config
1. Projection horizon expressed in year

### Model point information
1. Product name
2. Product variation (e.g. 5-pay)
3. Issue age of the insured
4. Sex of the insured (M/F)
5. Initial policy duration expressed in month
6. Initial number of policies (can be fractional number)

### Actuarial assumptions
1. Mortality rate table
2. Lapse rate table

##

## Calculation
1. The calculation is performed at monthly time step.
    *Example*
    *If the projection horizon obtained from the engine config is 100 years, there will be 1200 months to project (i.e. 12 months x 100 years).*
2. At month zero (i.e. initial duration), the number of policies inforce is the initial number of policies.
3. Starting from month 1 to the end of projection horizon, perform the following calculation recursively:
    1. Calculate the current policy duration in month by incrementing the initial policy duration along the monthly time steps. The current policy year can be calculated by expressing the current policy duration in year.
    2. Calculate the attained age by using the issue age and the current policy duration.
    3. Use the attained age and sex to look up the mortality rate for the current year from the mortality rate table.
    4. Use the product name, product variation and current policy year to look up the lapse rate for the current year from the lapse rate table.
    5. Number of deaths in the current month = Number of policies inforce at the end of the previous month x (1-(1 - current year mortality rate)^(1/12))
    6. Number of lapses in the current month:
        - If it is not the last month of the current policy year, then set it to zero.
        - If it is the last month of the current policy year, set it to (Number of policies inforce at the end of the previous month - Number of deaths in the current month) x current year lapse rate
    7. Number of policies inforce at the end of the current month = Number of policies inforce at the end of the previous month - Number of deaths in the current month - Number of lapses in the current month

## Output
The output should be a table containing:
1. projected number of policies inforce at the end of each month over the specified projection horizon (including month zero).
2. projected number of deaths in each month over the specified projection horizon.
3. projected number of lapses in each month over the specified projection horizon.
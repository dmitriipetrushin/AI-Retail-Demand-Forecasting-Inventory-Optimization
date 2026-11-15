# Business case and modeled financial outcomes

Decision question: is further operational validation justified, given forecast performance and scenario sensitivity? This is a fictional retailer, with no measured real-world savings or actual stakeholder participation.

# Business impact analysis (simulation only)

Observed transaction sales are the realized demand proxy, not proof of unconstrained customer demand. All inventory, supplier, purchasing cost, holding and shortage inputs below are **assumptions**. No orders or financial transactions are executed.

## Fixed experiment

25 identical products; 2011-11-11–2011-12-08 inclusive. All strategies start from identical stock, with no initial pipeline, and see only the same recorded history through the day before each review. A uses the expanding historical average; B uses the development-selected auto_ets; both allocate budget by ascending product code. C uses the same forecast as B and an OR-Tools integer-pack allocation. Every strategy obeys the same review budget. Product-code FIFO is simple but arbitrary, so C's improvement must not be attributed solely to predictive AI.

Receipts occur at the start of the day, then the review/order, then realized sales and end-of-day holding. A lead L order arrives at day t+L. Unmet proxy sales are lost, not backlogged. Forecasts update at weekly reviews using actual recorded sales, even when the simulated strategy could not fill them; this assumes all strategies observe the same exogenous sales proxy. The static final-holdout forecast evaluation remains separate from this updating policy simulation.

## Exact cost and inventory assumptions

Purchase price = max(£0.01, round(training-only median retail price × 0.50, to pennies)); **retail prices are not observed supplier costs**. Initial units = ceil(latest 28-day training mean × cover days). Safety stock = z × sample standard deviation of latest 28 recorded daily sales × sqrt(lead + review days). This is an illustrative independence/normal-style buffer, not a calibrated service-level guarantee. Inventory position = on hand + outstanding orders; target = forecast demand over lead + review days + safety. Round positive need up to pack size and MOQ. No capacity cap or supplier delay distribution is assumed.

|              |   lead_days |   review_days |   safety_z |   initial_cover_days |   budget_per_review |   purchase_price_fraction |   annual_holding_rate |   shortage_cost_multiple |   pack_size |   moq |
|:-------------|------------:|--------------:|-----------:|---------------------:|--------------------:|--------------------------:|----------------------:|-------------------------:|------------:|------:|
| base         |           7 |             7 |       1.28 |                    7 |                3000 |                       0.5 |                  0.25 |                        2 |           6 |    12 |
| tight_budget |           7 |             7 |       1.28 |                    7 |                1500 |                       0.5 |                  0.25 |                        2 |           6 |    12 |
| slow_supply  |          14 |             7 |       1.65 |                    7 |                3000 |                       0.5 |                  0.35 |                        3 |           6 |    12 |

Daily holding = end-of-day units × assumed unit purchase cost × annual holding rate / 365. Shortage cost = unfilled sales-proxy units × assumed purchase cost × shortage multiple. Total modeled operating cost = purchasing expenditure + holding + shortage. Unit turnover = fulfilled units / mean daily total closing inventory, over these 28 days only, undefined when average stock is zero. Initial stock is not an order expenditure. Purchases due beyond the horizon are included in expenditure and separately reported as outstanding assets.

## Measured simulation outputs

| scenario     | strategy   |   purchase_expenditure |   average_inventory |   holding_cost |   shortage_cost |   unmet_units |   period_unit_turnover |   total_operating_cost |   cost_reduction_vs_A |
|:-------------|:-----------|-----------------------:|--------------------:|---------------:|----------------:|--------------:|-----------------------:|-----------------------:|----------------------:|
| base         | A          |              11995.080 |            4672.250 |         64.407 |       63637.900 |     26271.000 |                  4.999 |              75697.387 |                 0.000 |
| base         | B          |              11989.680 |            4874.750 |         67.791 |       64624.620 |     27309.000 |                  4.578 |              76682.091 |                -0.013 |
| base         | C          |              11995.440 |            3907.107 |         66.033 |       65419.660 |     30109.000 |                  4.995 |              77481.133 |                -0.024 |
| tight_budget | A          |               5995.800 |            3013.179 |         46.501 |       71541.420 |     33531.000 |                  5.342 |              77583.721 |                 0.000 |
| tight_budget | B          |               5998.200 |            2938.821 |         46.997 |       71544.820 |     33495.000 |                  5.489 |              77590.017 |                -0.000 |
| tight_budget | C          |               5995.560 |            3047.321 |         41.785 |       68943.980 |     28800.000 |                  6.834 |              74981.325 |                 0.034 |
| slow_supply  | A          |              11994.000 |            3948.714 |         82.896 |      109661.010 |     35021.000 |                  3.699 |             121737.906 |                 0.000 |
| slow_supply  | B          |              11995.680 |            4017.786 |         82.985 |      109688.730 |     35039.000 |                  3.631 |             121767.395 |                -0.000 |
| slow_supply  | C          |              11991.480 |            3586.500 |         80.494 |      104822.490 |     31621.000 |                  5.020 |             116894.464 |                 0.040 |

Under the stated **base** simulation assumptions, Strategy B produced **1.30% higher modeled operating costs** than Strategy A; Strategy C produced **2.36% higher modeled operating costs** than Strategy A. Base costs: A **£75,697.39**, B **£76,682.09**, C **£77,481.13**. These are not verified real-world savings. Base fill rates are A 47.1%, B 45.0%, C 39.3%; the assumed budget/initial stock are insufficient for good service. The base scenario does not support replacing the baseline policy.

## Terminal assets and alternative accounting

The primary cash-plus-penalties comparison can favor policies that buy less and penalize policies with useful closing inventory. Therefore also report asset-adjusted cost = total modeled operating cost + initial inventory value − terminal on-hand value − in-transit value. This values units at assumed purchase cost, without salvage discount; it is still a model, not profit. No revenue, margin, discounting, tax, financing or implementation costs are measured.

| scenario     | strategy   |   initial_inventory_value |   terminal_inventory_value |   outstanding_order_value |   asset_adjusted_cost |   fill_rate |
|:-------------|:-----------|--------------------------:|---------------------------:|--------------------------:|----------------------:|------------:|
| base         | A          |                 10646.590 |                   1846.240 |                  2997.840 |             81499.897 |       0.471 |
| base         | B          |                 10646.590 |                   2334.080 |                  2997.960 |             81996.641 |       0.450 |
| base         | C          |                 10646.590 |                   2737.360 |                  2997.960 |             82392.403 |       0.393 |
| tight_budget | A          |                 10646.590 |                   1298.840 |                  1497.720 |             85433.751 |       0.324 |
| tight_budget | B          |                 10646.590 |                   1301.140 |                  1499.520 |             85435.947 |       0.325 |
| tight_budget | C          |                 10646.590 |                      0.000 |                  1497.600 |             84130.315 |       0.420 |
| slow_supply  | A          |                 10646.590 |                   3582.280 |                  5995.440 |            122806.776 |       0.294 |
| slow_supply  | B          |                 10646.590 |                   3589.480 |                  5999.160 |            122825.345 |       0.294 |
| slow_supply  | C          |                 10646.590 |                   1964.880 |                  5997.480 |            119578.694 |       0.363 |

## Sensitivity and failure conditions

Measured cases where a proposed strategy has **higher** total modeled cost than A:

| scenario     | strategy   |   cost_reduction_vs_A |
|:-------------|:-----------|----------------------:|
| base         | B          |               -0.0130 |
| base         | C          |               -0.0236 |
| tight_budget | B          |               -0.0001 |
| slow_supply  | B          |               -0.0002 |

The optimizer minimizes a single-review target shortage/excess surrogate and does not optimize the full realized 28-day cost. It can underfund a product, carry unusable excess, miss lead-time sales, or lose to FIFO when forecasts are wrong. Longer lead times and a tighter budget reveal exposure; low shortage penalties can make buying less look financially attractive while service degrades. Bulk orders and holiday shifts are not forecastable from these inputs. The final period lacks terminal demand, and changing terminal valuation can change rankings. A cost decrease alone is insufficient: inspect fill rates, unmet units and working capital as well.

Every review budget, nonnegative integer order, pack multiple, MOQ and stock-conservation check is validated at runtime and in tests. `simulation-orders.csv` and `simulation-ledger.csv` contain reproducible evidence. This sensitivity analysis is descriptive; no parameter was selected to maximize the final-holdout benefit.


## Investment and ROI boundary

No real implementation expenditure, license invoice, labor rate, supplier cost or realized margin was collected. Therefore an observed ROI or payback period cannot be calculated. The differences above are modeled operating-cost differences, not cash benefits available to fund the project.

For a future pilot, Finance would validate costs and terminal valuation; Operations would collect stock/availability and lead-time data. A valid future ROI = (verified attributable benefit − full implementation and operating cost) / full implementation and operating cost. Do not annualize this 28-day period through the Christmas peak. Approval should depend on out-of-sample operational evidence and adoption, not a hypothetical ROI multiple.

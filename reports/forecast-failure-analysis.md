# Forecast failure analysis

Selected model: auto_ets. **6 of 25** products have higher final-holdout WAPE than seasonal naive. All 25 remain in evaluation. This analysis is descriptive and does not retune or remove products.

## Highest product-level WAPE (selected model)

| product_id   |       mae |      rmse |    wape |     bias |    mase |   naive_wape |
|:-------------|----------:|----------:|--------:|---------:|--------:|-------------:|
| 22386        |  80.41221 |  96.93161 | 1.56466 |  0.84858 | 1.18879 |      1.54343 |
| 22077        |  41.44075 |  45.34523 | 1.42199 |  1.18069 | 1.58935 |      0.65931 |
| 82482        |  22.44966 |  27.59867 | 0.91100 |  0.41714 | 0.86690 |      2.02899 |
| 21080        |  28.69076 |  44.66023 | 0.86474 | -0.20065 | 0.76424 |      0.87944 |
| 47566        |  25.95860 |  62.92271 | 0.83163 | -0.24930 | 0.58577 |      0.75973 |
| 85099B       | 109.40082 | 143.62898 | 0.77826 |  0.25450 | 0.82227 |      1.92734 |
| 20728        |  22.90202 |  42.89390 | 0.75089 | -0.08301 | 0.77270 |      0.81733 |
| 21212        |  49.91897 |  64.27654 | 0.74785 |  0.49601 | 0.41784 |      0.72071 |
| 22727        |  41.14559 | 123.40721 | 0.73568 | -0.39462 | 2.05151 |      0.78416 |
| 22457        |  35.87731 | 120.94815 | 0.70102 | -0.56595 | 1.72497 |      0.77530 |

## Products where seasonal naive is better

| product_id   |    wape |   naive_wape |   wape_difference_vs_naive |
|:-------------|--------:|-------------:|---------------------------:|
| 20724        | 0.48112 |      0.44431 |                    0.03681 |
| 21212        | 0.74785 |      0.72071 |                    0.02714 |
| 22077        | 1.42199 |      0.65931 |                    0.76267 |
| 22386        | 1.56466 |      1.54343 |                    0.02122 |
| 47566        | 0.83163 |      0.75973 |                    0.07190 |
| 85123A       | 0.62419 |      0.58788 |                    0.03631 |

Large single-day quantities are retained because many customers are wholesalers. A smooth statistical forecast cannot anticipate individual bulk purchases. Zero recorded sales also include closed days and unknown stockouts; neither model sees stock availability. The Christmas-period holdout may differ from earlier development windows. Positive/negative bias can coexist across products; aggregate bias alone hides that problem.

No products were excluded after seeing these results. Next separately labeled experiments could test holiday indicators, forecast intervals, hierarchy pooling, longer histories, and intermittent-product segmentation. Initial holdout artifacts must remain unchanged.

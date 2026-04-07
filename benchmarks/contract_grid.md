# Contract Grid Benchmark

Exact contract result: `lpp_refined_predictor(n)` matches the deterministic ground-truth grid at every declared band from $10^0$ through $10^{24}$.

## Summary

- bands evaluated: 25
- refined exact matches: 25/25
- max refined ppm: 0.000000000000
- max seed ppm: 413793.103448275884

## Worst Seed Rows

| Band | n | p_n | Seed | Seed error | Seed ppm | Refined | Exact match |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: |
| 10^1 | 10 | 29 | 17 | -12 | 413793.103448275884 | 29 | True |
| 10^2 | 100 | 541 | 508 | -33 | 60998.151571164512 | 541 | True |
| 10^3 | 1000 | 7919 | 7857 | -62 | 7829.271372648062 | 7919 | True |

## Artifacts

- CSV: `contract_grid.csv`
- Summary JSON: `summary_bands.json`
- Per-band JSON: `band_10_0.json` through `band_10_24.json`

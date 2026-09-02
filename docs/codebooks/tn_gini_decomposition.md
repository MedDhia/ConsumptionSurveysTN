# Gini at two geographies and the between/within-region split, 2000–2023

`data/processed/tn_gini_decomposition.csv` — 533 rows × 11 columns

The same inequality measured at two geographies, and split into the part that lies between INS's seven grandes régions and the part that lies inside them. One row per indicator and year.

**Two geographies, because the answer depends on which one you ask about.** The 24 governorates nest inside the seven regions, so every indicator has a Gini across governorates and a Gini across regions — the second computed on the same quantity aggregated, since a region's share of the national total is the sum of its governorates' shares. The region figure is always the smaller of the two, because aggregating hides the dispersion inside each region. *How much* smaller is the finding: where the two are close the inequality is between regions, and where they diverge it is inside them.

**Pre and post, not before and after an effect.** `period` splits at 2011. A difference between two period means is a description of what happened, not an estimate of what the revolution did: 2011 is one of several things that happened between 1994 and 2023, and `tn_rdit_estimates` records what became of the attempt to isolate it.

**The decomposition is the structural column.** Theil-T is additively decomposable, so `theil_governorate` splits exactly into `theil_between` and `theil_within`. `identity_gap` is the residual of that identity and is published rather than asserted: it is at machine precision, which is the evidence the arithmetic is right rather than merely plausible. `between_share` is the between part as a fraction of the total, and it is the number the Tunisian literature's coastal/interior framing is really about — a rise means inequality moved *between* regions even where the total held still.

**Unweighted, with a reason.** Population weights need a governorate population, which the corpus does not print before 2005, leaving three pre-revolution years. Each governorate counts once here, so this is inequality across administrative units rather than across Tunisians. `tn_governorate_inequality` carries the population-weighted family from 2005 for the indices where it can be computed.

Theil is undefined where any governorate reports none of the thing, so those indicator-years carry a Gini and an empty decomposition rather than a floored one.

## Variables

| Column | Type | Unit | INS origin | Description |
| --- | --- | --- | --- | --- |
| `indicator` | str | — | derived | — |
| `year` | int64 | — | derived | Calendar year the observation refers to. |
| `period` | str | — | derived | `pre` for years before 2011, `post` for 2011 onward. A label, not a design. |
| `gini_governorate` | float64 | — | derived | Gini across the 24 governorates, each counting once. |
| `gini_region` | float64 | — | derived | The same Gini across the 7 grandes régions, computed on the same quantity aggregated: a region's share of the national total is the sum of its governorates' shares. Nearly always the smaller of the two, because seven units cannot show the dispersion inside them. |
| `theil_governorate` | float64 | — | derived | Theil-T across the 24 governorates: the quantity that is decomposed. Empty where any governorate reports none of the thing, because a logarithm has nothing to say about a zero. |
| `theil_region` | float64 | — | derived | Theil-T across the 7 grandes régions. |
| `theil_between` | float64 | — | derived | The part of `theil_governorate` that lies between the seven regions: Σ (n_g/n)(μ_g/μ) ln(μ_g/μ). This is the coastal/interior component. |
| `theil_within` | float64 | — | derived | The part of `theil_governorate` that lies inside regions: Σ (n_g/n)(μ_g/μ) T_g. |
| `identity_gap` | float64 | — | derived | abs(between + within − total). Published rather than asserted: it is at machine precision, and the builder refuses to write the file if it exceeds 1e-9. |
| `between_share` | float64 | — | derived | `theil_between / theil_governorate`. The number a structural change would move: means inequality shifted *between* regions even where the total held still. |

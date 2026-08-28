# The evolution of inequality in Tunisia, 1985–2021

Six figures built from `data/processed`. Regenerate with `make figures`.

**No composite index appears in any of them.** No Gini, no Theil, no Atkinson, no
polarisation index. Every figure shows either an observed quantity — a group's mean
expenditure, a poverty rate, a budget share — or the relation between two observed
quantities, such as one region's mean against the national mean, or a region's share of
spending against its share of people. Any number here can be recovered from the datasets
with arithmetic you can do in your head.

That constraint costs something. A single index compresses a whole distribution into one
comparable number, and these figures cannot do that. What you get back is that nothing is
hidden inside a formula: when the gap between Grand Tunis and the Centre West moves, you
can see which line moved.

Every figure ships in a light and a dark version; the images below follow your theme.

---

### 1. Growth by quintile, 2015 → 2021

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="01-expenditure-by-quintile-dark.png">
  <img alt="Mean annual expenditure per person by quintile, 2015 and 2021" src="01-expenditure-by-quintile-light.png">
</picture>

Every quintile spent more in 2021 than in 2015. The bottom fifth gained 622 dinars per
person; the top fifth gained 3,219. Current prices, so much of this is inflation — the
point is the spread between the bars, not their length.

### 2. Each region against the national mean, 1990–2021

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="02-regional-gap-dark.png">
  <img alt="Each region's mean expenditure as a percentage of the national mean, by region, 1990 to 2021" src="02-regional-gap-light.png">
</picture>

Expressing each region as a percentage of the national mean removes inflation entirely,
so a 30-year comparison is meaningful. Grand Tunis fell from 141% to 126% of the national
mean — real convergence at the top. The Centre West went the other way, from 70% to 66%:
the poorest region lost ground relative to the country over three decades.

### 3. Urban and rural, 1990–2021

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="03-urban-rural-dark.png">
  <img alt="Urban and rural mean expenditure per person, and rural as a share of urban, 1990 to 2021" src="03-urban-rural-light.png">
</picture>

The levels diverge in dinars while the ratio slowly closes: a rural person spent 52% of
what an urban one did in 1990 and 66% in 2021. Two panels rather than two y-axes on one
plot, which would have invented a relationship between them.

### 4. Share of spending against share of people

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="04-expenditure-vs-population-share-dark.png">
  <img alt="Each region's share of national expenditure minus its share of population, 2015 and 2021" src="04-expenditure-vs-population-share-light.png">
</picture>

The most direct statement of regional inequality available without an index: if a region
holds 12.9% of the people and 8.6% of the spending, that gap is the inequality. Grand
Tunis remains the only large outlier, and its excess fell from +9.2 to +6.3 points.

### 5. Poverty by region, 2005–2021

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="05-poverty-by-region-dark.png">
  <img alt="Share of people below the national poverty line by region, 2005 to 2021, against the national rate" src="05-poverty-by-region-light.png">
</picture>

Between 2005 and 2015 poverty fell in every region; between 2015 and 2021 it rose again
in five of the seven. Only Grand Tunis and the North West kept improving. The grey line in each panel is the national
rate, on the revised (2011) methodology throughout — pre-2011 figures use a different and
incomparable definition and are deliberately absent.

### 6. The 2021 distribution

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="06-distribution-2021-dark.png">
  <img alt="Share of all expenditure held by each decile, and each decile's food share, 2021" src="06-distribution-2021-light.png">
</picture>

Recomputed from the microdata rather than transcribed. The richest tenth accounts for 28%
of all household spending and the poorest tenth for 3%. The right panel is an Engel
curve: the poorest tenth puts 35% of its budget on food, the richest 24%.

A note on that second panel, because the choice changes the answer. It plots the **mean
household food share, weighted by people**. Computed instead as aggregate food spending
over aggregate spending, the two agree to a tenth of a point through decile 9 and then
split — the aggregate ratio puts the top decile at 28.5% and ticks *upward* from decile
9, because a handful of very large budgets dominate the sum. The mean of household shares
is what "how much of its budget does this tenth put on food" actually means, and it falls
monotonically.

---

## Colour

The palette is the dataviz reference instance: blue `#2a78d6` and orange `#eb6834` on
light, blue `#3987e5` and orange `#d95926` on dark. Both pairs were checked with the
skill's `validate_palette.js` and pass every gate in both modes — worst-adjacent
colour-vision-deficiency ΔE 24.7 light and 26.8 dark, against a threshold of 8. No figure
uses more than two categorical series; where more than two groups appear they are small
multiples with one series per panel, so colour never has to carry seven identities at
once.

## Sources

Figures 1–5 come from `tn_consumption_panel.csv`, on the `published` basis throughout —
figures transcribed from INS documents, each row carrying its source table. Figure 6 is
recomputed from the EBCNV 2021 microdata. Every claim above is reproducible from
`scripts/make_figures.py`.

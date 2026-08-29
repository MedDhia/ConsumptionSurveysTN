# The evolution of inequality in Tunisia, 1985–2021

Sixteen figures built from `data/processed`. Regenerate with `make figures`.

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
incomparable definition and are deliberately absent. The dashed rule marks January 2011;
figures 13 to 16 pick up what it separates.

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

## Inequality within groups, not between them

The first six figures are built on regional and quintile **means**, which by construction
cannot show how much variation sits inside a group. These six look inside.

### 7. Spread within each region

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="07-within-region-spread-dark.png">
  <img alt="Spread of annual expenditure per person within each region, 2021" src="07-within-region-spread-light.png">
</picture>

The single most consequential figure here. Within every region the 90th percentile of
per-capita expenditure is 3.8 to 4.2 times the 10th. Between regions, the highest median
(Grand Tunis, 5,696 DT) is only 2.0 times the lowest (Centre West, 2,865 DT).

Inequality inside a Tunisian region is about double the inequality between regions. That
reframes figures 2 and 4: regional gaps are real and politically salient, but they are the
smaller part of the dispersion. Percentiles only — no index.

### 8. Dispersion inside governorates

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="08-delegation-dispersion-dark.png">
  <img alt="Poverty rate of each of 253 delegations, grouped by governorate" src="08-delegation-dispersion-light.png">
</picture>

The same point one tier down, with one dot per delegation. Bizerte runs from 5.3% to 39.9%
poverty across its delegations — a 34.6-point range inside a single governorate, wider
than the gap between the richest and poorest *regions*. A governorate average describes
almost nobody.

These are modelled small-area estimates from the 2020 poverty map, not survey estimates:
EBCNV is representative at region × milieu and no finer. Siliana is absent because its
table in that report carries no poverty column.

### 9. Who is poor against who the poor are

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="09-incidence-vs-share-of-poor-dark.png">
  <img alt="Poverty rate within each group and each group's share of all poor people, 2021" src="09-incidence-vs-share-of-poor-light.png">
</picture>

Two different questions with two different answers. Households headed by an unemployed
person have the highest poverty rate at 41.3% — but they are only 7.0% of all poor people.
Households headed by a non-agricultural worker have a 24.4% rate and make up 32.7% of the
poor.

Target the highest-risk group and you reach a small slice of poverty; target the largest
group and you spend most of it on the non-poor. This is precisely the distinction a single
index erases, which is much of the argument for not using one.

### 10. Deprivation in kind

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="10-deprivation-in-kind-dark.png">
  <img alt="Household amenities, poor against non-poor, 2021" src="10-deprivation-in-kind-light.png">
</picture>

Inequality with no dinars in it. A refrigerator is nearly universal — 93.9% of the poor
against 96.8% of the non-poor, a 3-point gap. Mains gas for cooking is not: 3.7% against
24.7%. A computer, 8.2% against 31.6%. A flush toilet, 53.7% against 85.1%.

Which amenities have converged and which have not is a different ranking from expenditure,
and the first use in this repository of the living-conditions file.

### 11. The social protection gap

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="11-social-protection-gap-dark.png">
  <img alt="Affiliation to a contributory social-insurance fund by region, 2021" src="11-social-protection-gap-light.png">
</picture>

Contributory cover reaches 40.8% of the non-poor and 18.5% of the poor — the people with
least capacity to absorb a shock are least likely to be insured against one, in every
region without exception.

INS's synthesis note reports 40.5% and 18.1% nationally. The sub-point difference is most
likely the denominator, but INS does not state which base it used, so this is a close
correspondence rather than a verified match.

### 12. The literacy gap across cohorts

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="12-literacy-gap-dark.png">
  <img alt="Literacy by poverty status and age band, 2021" src="12-literacy-gap-light.png">
</picture>

Among people aged 65 and over, 54.7% of the non-poor can read and write against 27.4% of
the poor — a 27-point gap. Among 15-to-24-year-olds the same gap is 0.8 points, with both
groups above 96%.

The clearest evolution story in the whole directory, and it comes from a single
cross-section: the cohorts are the time dimension. Whatever else has or has not improved,
mass schooling closed this particular gap almost completely.

The bands are cut from the raw age variable rather than the four-way `age_group`, which is
too coarse to show a gradient. The literacy question was asked of those aged 10 and over,
so the figure is restricted to 15 and over; every cell rests on at least 778 observations.

---

## Across the 2011 revolution

The waves are 2005, 2010, 2015 and 2021 and the revolution is January 2011, so it falls
between two of them: two before, two after. INS applied its revised (2011) poverty
methodology back to 2005 and 2010, which is the only reason a comparison across the break
is possible at all. Every poverty series below is on that revised methodology; the
pre-2011 figures use an incomparable definition and are absent.

**These are before-and-after descriptions, not causal estimates.** There is one country,
no counterfactual and no control group, and the 2010–2021 window holds the revolution and
also the 2015 Bardo and Sousse attacks, the tourism collapse, dinar depreciation, two IMF
programmes and COVID. Nothing here separates those. The figures say "across the
revolution" and never "because of it"; a reader who wants identification should treat this
directory as the wrong instrument.

### 13. National poverty across the revolution, 2005–2021

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="13-poverty-across-the-revolution-dark.png">
  <img alt="Share of people below the national poverty line, 2005 to 2021, with the 2019 modelled estimate" src="13-poverty-across-the-revolution-light.png">
</picture>

23.1% in 2005, 20.5% in 2010, 15.2% in 2015, 16.6% in 2021 — and 13.8% in 2019. That last
point changes the reading. On the four survey waves alone the story is "poverty fell, then
rose after the revolution"; with 2019 in the frame the entire rise sits between 2019 and a
survey fielded March 2021 to March 2022, in the middle of the pandemic.

The 2019 figure is drawn as an open marker because it is modelled, imputed by INS from the
2018–19 follow-up panel, which collected no consumption data. It is not a survey estimate
and should not be read as one. Leaving it out would have been the more misleading choice.

Two things the pre-revolution half of the line settles: poverty was already falling before
2011, by 2.6 points between 2005 and 2010, so a post-2011 decline that starts from the
revolution is reading a trend that was underway. And extreme poverty, on the same source,
went 7.4 → 6.0 → 2.9 → 2.9: it more than halved and then held, including through 2021.

### 14. The regional gap, in ratio and in points

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="14-regional-gap-two-ways-dark.png">
  <img alt="Centre West against Grand Tunis poverty, as a ratio and as a difference in points, 2005 to 2021" src="14-regional-gap-two-ways-light.png">
</picture>

Two panels because the two measures disagree, and the disagreement is the finding. The
Centre West against Grand Tunis:

| | 2005 | 2010 | 2015 | 2021 |
|---|---|---|---|---|
| Ratio | 4.0× | 3.8× | 5.8× | **7.9×** |
| Difference | 37.4 pp | 31.2 pp | 25.5 pp | **32.3 pp** |

Relatively the gap roughly doubled. Absolutely it is close to where it stood in 2010. Both
are true of the same two numbers, because the ratio grew mostly through the denominator:
Grand Tunis fell from 11.1% to 4.7% while the Centre West went 42.3% to 37.0%. Publishing
only the ratio would say the gap exploded; only the difference, that little changed.
Neither alone is honest, so both are on the page, on separate axes because the units
differ.

### 15. Urban and rural poverty across the revolution

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="15-urban-rural-poverty-dark.png">
  <img alt="Urban and rural poverty rates, 2005 to 2021" src="15-urban-rural-poverty-light.png">
</picture>

Rural poverty fell across the whole period, 38.8% to 24.8%. Urban fell to 2015 and then
went back up: 12.6% in 2010, 10.1% in 2015, 12.7% in 2021 — above where it was the year
before the revolution.

The urban–rural convergence that gets cited is therefore two different movements, and only
one of them is rural improvement. The reference line marks the 2010 urban level so the
crossing is visible rather than asserted.

### 16. What changed in the household budget, 2010 → 2021

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="16-budget-shift-2010-2021-dark.png">
  <img alt="Change in each COICOP function's share of the household budget between 2010 and 2021" src="16-budget-shift-2010-2021-light.png">
</picture>

The last pre-revolution wave against the most recent one, by COICOP function. Clothing
took 3.0 more points of the budget (8.6% → 11.6%) and health and hygiene 2.3 more
(8.8% → 11.1%); transport gave up 2.1 (9.0% → 6.9%) and communication 1.3 (5.4% → 4.1%).
Food moved least of anything large, 29.3% to 30.1%.

INS warns that the 2021 coefficients reflect the health crisis and are not usable to
update the CPI basket. That warning applies here too: this is a comparison of two years,
one of them abnormal, not a trend.

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

Figures 1–5, 9 and 13–16 come from `tn_consumption_panel.csv`, on the `published` basis
throughout — figures transcribed from INS documents, each row carrying its source table.
Figure 8 comes from the 2020 poverty map. Figures 6, 7, 10, 11 and 12 are recomputed from
the EBCNV 2021 microdata. Every claim above is reproducible from
`scripts/make_figures.py`.

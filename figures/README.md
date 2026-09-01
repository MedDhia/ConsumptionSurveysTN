# The evolution of inequality in Tunisia, 1985–2021

Forty-four figures built from `data/processed`. Regenerate with `make figures`.

**Composite indices now appear deliberately, in figures 39–44.** For most of this
directory they still do not: figures 1–34 show either an observed quantity — a group's mean
expenditure, a poverty rate, a budget share — or the relation between two observed
quantities, and any number in them can be recovered from the datasets with arithmetic you
can do in your head. That was a constraint worth keeping for as long as the question was
*what* the distribution looks like.

It was lifted for figures 39–44, where the question is how regional inequality **evolved**,
and a longitudinal answer needs one comparable number per year. Those five report the
standard family — Gini, Theil-T, Theil-L, Atkinson, the coefficient of variation and
percentile ratios — rather than a single index, because which index you pick is a choice
about which part of the distribution matters, and reporting one hides that choice. Figure
43 exists specifically to show the indices disagreeing.

Figure 38 is still not an exception and is worth saying why: a Lorenz curve is the
*uncompressed* form of the Gini. It shows the whole distribution rather than the one number
computed from it, and the statistic it is read on — the share of a service going to the
least-served half of the population — is an observed quantity you can recover from
`tn_governorate_comparable` by adding twelve numbers.

Figures 35–37 remain the narrow, separately-asked-for exception. They rank *goods* by how unevenly each
is spread across the seven regions, which cannot be done without reducing seven regional
means to one number per good. The seven values behind every one of them are published in
`tn_expenditure_by_product_region`, and the measure compares regions rather than
households.

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

## What the surveys cannot show on their own

EBCNV runs every five or six years and measures households. Three things that matter for
reading it come from a different INS publication entirely — the *Annuaire Statistique de
la Tunisie*, whose 2001–2023 editions carry annual series on prices and on work.

Bringing in a second source has a cost worth stating: these are national aggregates, not
survey microdata, and nothing here can be broken down by household. They are context for
the survey figures, not extensions of them.

### 17. Prices since 1999

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="17-prices-since-1999-dark.png">
  <img alt="Consumer price index for Tunisia, 1999 to 2023, base 2015 equals 100, with the EBCNV survey waves marked" src="17-prices-since-1999-light.png">
</picture>

The index stands at 64.7 in 2005, 79.0 in 2010, 100.0 in 2015 and 139.6 in 2021. Between
the last pre-revolution survey and the most recent one, prices rose 77%.

This is the yardstick figures 1 to 3 are **not** divided by. Those show expenditure in
nominal dinars, because that is what INS publishes and what the microdata contains. A
reader who takes the rise in mean per-capita expenditure between two waves as a gain in
living standards is reading this line into it without knowing.

INS publishes the same series on eight base years side by side. They are rescalings of
one series, not eight measurements, and this uses 2015 throughout.

### 18. What rose in price against what rose in the budget

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="18-price-against-budget-dark.png">
  <img alt="Change in price against change in budget share for nine consumption functions, 2015 to 2021" src="18-price-against-budget-light.png">
</picture>

Both endpoints are survey waves, so the two axes cover exactly the same span. Clothing
rose 54.7% in price and took 4.0 more points of the budget — the largest share rise in
figure 16, and mostly a price story rather than households buying more clothes.
Communication is the opposite corner: prices essentially flat at +4.7%, share down 0.3
points. Housing and energy rose 33.5%, below the 39.6% all-items rate, and still lost 2.7
points of the budget.

**A share can rise because quantity rose or because price did.** This figure separates
the two questions; it does not answer the second. Nothing here identifies a demand
response, and the same picture is consistent with several stories about what households
did.

Nine of the twelve functions are shown. EBCNV's function 6 is "hygiene and care" while
the CPI's division 6 is health with personal care filed under division 12, and EBCNV
folds holidays in with restaurants — so three of the twelve would compare different
baskets, and are left out rather than quietly plotted.

### 19. Unemployment by education since the revolution

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="19-unemployment-by-education-dark.png">
  <img alt="Unemployment rate by education level, 2011 to 2023, against the national rate" src="19-unemployment-by-education-light.png">
</picture>

In every one of the thirteen years, unemployment rises with education. People with no
schooling run between 4.3% and 10.9%; people with higher education between 20.2% and
29.2%, above the national rate throughout. The gradient never once inverts, which a test
asserts rather than leaving to the eye.

Read this against figure 12, where mass schooling has almost closed the literacy gap
between poor and non-poor among the young. Both can be true: education has been
distributed far more widely, and it does not lead where it is supposed to.

**This series does not span the revolution.** The 2005, 2010 and 2012 yearbooks carry no
unemployment table — checked in the documents, not assumed — so 2011 is the earliest year
available. It describes the period since, and cannot compare across.

---

## Inequality without dinars

Seven figures from the parts of EBCNV 2021 no earlier figure touched: the health,
education and labour modules, and the 3.26-million-row product file.

### 20. What households pay out of pocket for care

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="20-out-of-pocket-health-dark.png">
  <img alt="Median out-of-pocket health spending by item, poor against non-poor, 2021" src="20-out-of-pocket-health-light.png">
</picture>

Among people who report paying anything: 30 DT against 55 for doctor visits, tests and
imaging; 30 against 47 for medicine; 260 against 422 for a chronic illness; 100 against
280 for a hospital stay. Fewer of the poor pay at all — 69% report a consultation cost
against 79%.

Spending less on health is not the same as needing less of it, and the conditional
medians make that visible: the gap is in both who pays and how much.

The hospital row rests on 87 poor observations against 720 non-poor and is indicative;
the other three rest on between 769 and 16,603. INS's non-declared sentinel codes are
dropped throughout — they survive in the processed file as 999 and 999999 and would wreck
any average that kept them.

These amounts are in **dinars**. INS's own variable labels give no unit, and an earlier
version of this repository's codebook guessed millimes — which would make a doctor's
visit cost four santimes. Summed per household, the module comes to a median 172 against
1,749 for COICOP function 6, about 8%, which is what out-of-pocket medical care should be
inside a category that also holds hygiene and personal care. On the millimes reading it
would be 0.01%.

### 21. Chronic illness and who holds a card

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="21-chronic-illness-and-cover-dark.png">
  <img alt="Reported chronic illness and care-card cover, poor against non-poor, 2021" src="21-chronic-illness-and-cover-light.png">
</picture>

10.8% of the poor report a chronic illness against 20.2% of the non-poor.

The obvious reading — that the poor are healthier — is almost certainly wrong. A chronic
illness has to be diagnosed before it can be reported, and figure 20 shows the poor
consulting and paying less. The left panel most plausibly measures contact with a doctor.
It is included **because** it is a trap: a naive reading of a real INS variable produces
a conclusion that inverts the truth.

The right panel is the firmer finding. Free and reduced-tariff cards do reach the poor
more often, 34.1% against 20.0% — the targeting works in the direction intended — and
still leave roughly two thirds of the chronically ill poor holding no card at all.

### 22. Why people left school

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="22-why-people-left-school-dark.png">
  <img alt="Reason given for leaving education, poor against non-poor, 2021" src="22-why-people-left-school-light.png">
</picture>

"School supplies too expensive" is given by 23.9% of the poor and 13.5% of the non-poor.
The sharpest split is the answer that is not a reason for dropping out at all: 18.9% of
the non-poor left because they had **completed** their studies, against 6.4% of the poor —
three times.

"Saw no point in studying" is the most common answer in both groups, 42.4% and 36.7%.
Figure 19 is worth holding alongside it: for a Tunisian graduate, unemployment has run
above 20% every year since 2011.

### 23. How far school is

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="23-distance-to-school-dark.png">
  <img alt="Distance and travel time to the education institution, urban against rural, 2021" src="23-distance-to-school-light.png">
</picture>

35% of rural pupils are more than 4 km from their institution against 12% of urban ones,
close to three times. The median rural journey is 20 minutes against 15, and the upper
quartile 30 against 20.

Asked separately why they never attended school at all, 18.8% of the poor and 24.6% of
the non-poor answer that it was too far — a different question from figure 22, which asks
people who did attend why they stopped.

### 24. Why people are not working

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="24-why-people-are-not-working-dark.png">
  <img alt="Reason given for not working, men against women, 2021" src="24-why-people-are-not-working-light.png">
</picture>

Housework accounts for 54.8% of non-working women and 0.6% of non-working men. Nothing
else in this directory separates two groups so completely.

The mirror image is retirement: 31.2% of non-working men against 4.2% of women — itself a
consequence of the first, since a lifetime of unpaid housework produces no pension. And
"no work available" is given by 25.9% of men against 10.7% of women.

Read with figure 19: the unemployment rate counts only people looking for work, so the
women in the top row are not in it at all. A falling unemployment rate and a wall of
women outside the labour force are perfectly compatible.

### 25. Where working people work

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="25-where-the-poor-work-dark.png">
  <img alt="Where working people work, poor against non-poor, 2021" src="25-where-the-poor-work-light.png">
</picture>

What does *not* separate the two groups: employment status. 82.4% of working poor people
are employees, against 79.8% of the non-poor. The poor are not disproportionately
self-employed or informal by that measure.

What does: the sector. Farms take 21.6% of poor workers against 10.7%, building sites
20.8% against 9.2%. Public administration and public enterprises together take 22.0% of
non-poor workers and 9.6% of poor ones.

A public-sector job is the clearest single marker of not being poor in this data, which is
worth sitting with given how much of Tunisian politics since 2011 has turned on public
employment.

### 26. Where household money goes

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="26-where-household-money-goes-dark.png">
  <img alt="Share of household spending by type of outlet, poor against non-poor, 2021" src="26-where-household-money-goes-light.png">
</picture>

The first use of the product-level file: 3.26 million acquisition lines, one per household
per item. Shares of **dinars**, not of lines, so a supermarket trip is not counted equal
to a loaf of bread.

The weekly market takes 11.2% of poor spending against 5.3% of non-poor. Supermarkets
take 0.6% against 3.0% — five times. The private shop dominates both at 82.6% and 87.1%,
which is why the axis is logarithmic; on a linear scale every other outlet would be a
sliver.

Own production is 2.1% of poor spending against 0.9%, and 2.9% of rural against 0.4% of
urban — small everywhere, and one of the few places where being rural shows up as
something other than a disadvantage.

---

## Can the revolution's effect be identified?

The four figures above this line describe what happened across January 2011. These four
ask the harder question — whether any of it can be *attributed* to the revolution — and
answer no, by running the tests rather than asserting the conclusion.

**Why the answer is structural.** The revolution treated all twenty-four governorates at
the same instant. There is no untreated unit inside Tunisia, and no comparison country in
this data to build a synthetic one from. That rules out two candidate designs: an
interrupted time series, whose counterfactual is an extrapolated pre-trend, and a
difference-in-differences on differential exposure, which requires the compared groups to
have been on parallel paths beforehand. Figures 28 and 29 test exactly those two
requirements. Both fail.

It does not rule out a third, which figures 31–34 take up: **regression discontinuity in
time**, where the running variable is the calendar and no untreated unit is needed at all.
The conclusion below is about these four figures' outcome at annual frequency, not about
the revolution in general.

The outcome throughout is **pupils per teacher in the first cycle of basic education**,
across all 24 governorates and 21 years (1998–2018), 502 of 504 cells present. It needs no
population denominator — both halves come from the same chapter and the same years — and
it measures something governments actually allocate.

### 27. The counterfactual is an assumption

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="27-counterfactual-is-an-assumption-dark.png">
  <img alt="Pupils per teacher 1998 to 2018 with three different pre-trend extrapolations after 2011" src="27-counterfactual-is-an-assumption-light.png">
</picture>

An interrupted time series compares what happened against the pre-trend carried forward,
so the estimate is only ever as good as that extrapolation. Three defensible choices —
linear on 1998–2010, quadratic on the same window, linear on 2006–2010 — give "effects"
of **+7.0, +3.4 and +2.7** pupils per teacher. A factor of 2.6 between them, and nothing
in the data adjudicates.

The national series itself is not ambiguous: 23.8 pupils per teacher in 1998, falling to
16.8 by 2008, then flat and rising to 18.0 by 2018. Something changed. What the design
cannot say is *when*, or *because of what*.

### 28. Every candidate break year gives the same answer

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="28-placebo-break-years-dark.png">
  <img alt="Level shift estimated by segmented regression at each assumed break year from 2003 to 2015" src="28-placebo-break-years-light.png">
</picture>

The falsification test. The same segmented regression is run thirteen times, moving only
the year the break is assumed to occur. If January 2011 caused a discrete change, the
estimated step should peak there.

It does not. 2010 gives **+1.04**, 2011 gives **+1.05**, 2012 gives **+1.09** — and 2014
and 2015 give larger steps still, at +1.31 and +1.58. The estimates form a smooth ramp
across candidate years, which is the signature of a gradual change in trend, not of an
event. A single-break design cannot separate the two, and this figure is how you find
that out rather than assuming it away.

### 29. Parallel trends fail, and fail badly

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="29-parallel-trends-fail-dark.png">
  <img alt="Gap in pupils per teacher between interior and coastal governorates, 1998 to 2018" src="29-parallel-trends-fail-light.png">
</picture>

The natural difference-in-differences here splits governorates by exposure: the interior —
INS's Nord-Ouest, Centre-Ouest and Sud-Ouest, where the revolution began and where the
grievance was concentrated — against the coastal and metropolitan governorates.

That design needs the two groups to have been moving in parallel before 2011. They were
not. The gap widened in **ten of the twelve years to 2010** — narrowing only in 2001 and
2003 — averaging 0.20 pupils per teacher a year, going from −0.47 in 1998 to −2.97 by 2010
and on to −4.36 by 2018. A post-2011 difference is indistinguishable from a trend that had
been running for twelve years.

Note the sign, which is easy to misread: interior governorates have *fewer* pupils per
teacher — small rural schools against crowded coastal ones. On this measure the interior
looks better served, and still diverging.

### 30. What the data does support

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="30-regional-dispersion-dark.png">
  <img alt="Dispersion in pupils per teacher across 24 governorates, 1998 to 2018" src="30-regional-dispersion-light.png">
</picture>

Description, and it is worth having. The ratio between the highest and lowest governorate
went from **1.21 in 1998 to 1.70 in 2010 to 1.93 in 2018**; the interquartile ratio from
1.06 to 1.29. Both climb before, across and after the revolution, with no step at 2011.

Two ratios between observed quantities, so the no-composite-index rule holds here as
everywhere else in this directory.

This is the honest summary the other three leave standing: regional provision diverged
steadily over two decades, and nothing in *this* annual panel can attribute any part of
that divergence to the revolution. That is a finding about the limits of the evidence, not
a claim that the revolution had no effect — those are different statements, and only the
first is supported. Figures 31–34 press the same question with the one design that does
not need a control group.

---

## The design that needs no control group

Figures 27–30 ruled out the designs that require an untreated unit. Regression
discontinuity in time requires none (Hausman and Rapson 2018): the running variable is the
calendar, the cutoff is the event, and nobody can be on the wrong side of January 2011 by
choice. The revolution being unforeseen matters here, but it is worth being precise about
what it buys. It buys **no anticipation** — untreated outcomes were not already bending
before the cutoff in expectation of it. That is necessary and not sufficient. What
identifies the design is **continuity in time**: absent the event, the outcome would have
passed through the cutoff smoothly. Nothing about surprise establishes that; only getting
close enough to the cutoff to see it does.

Which is where the corpus splits in two. It holds a monthly series and an annual one, and
these four figures ask the same question of each.

### 31. At monthly frequency the design can stand right at the cutoff

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="31-rdit-monthly-trade-dark.png">
  <img alt="Monthly imports and exports either side of January 2011, with local linear fits" src="31-rdit-monthly-trade-light.png">
</picture>

Monthly imports and exports, 252 months each, 2003–2023 — table 14.1 of the yearbooks. A
twelve-month bandwidth puts twelve observations on each side of the cutoff, so the fit is
genuinely local rather than an extrapolation dressed as one.

The estimated jump is **−6.9% for exports and −4.5% for imports**. But it rests entirely on
January 2011 itself: dropping that single month sends exports to **+9.6%** and imports to
**+7.8%**, because the treated side must then be extrapolated back across a steep recovery.
That is the signature of a one-month disruption — the general strike, the closed border
crossings, the fortnight the ports barely ran — and not of a step to a new level.

### 32. The same design finds 2008 and 2020 loudly, and 2011 not at all

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="32-rdit-placebo-cutoffs-dark.png">
  <img alt="The estimated jump in monthly trade at every candidate cutoff from 2004 to 2021" src="32-rdit-placebo-cutoffs-light.png">
</picture>

The estimator re-run at every month from 2004 to 2021, with only the assumed cutoff moved.
This is the check that tells a real discontinuity from a series that jumps about anyway,
and it doubles as a test of the instrument: a design incapable of detecting a shock would
find nothing anywhere.

It finds plenty. The largest discontinuities in seventeen years of monthly trade are
**March 2020** (−47% on imports) and **November–December 2008** (−30% to −38%) — COVID and
the financial crisis, both unmistakable. Against that yardstick January 2011 is ordinary:
its jump is exceeded in size by **42% of arbitrary cutoffs for exports and 44% for
imports** at a twelve-month bandwidth. At the narrowest bandwidth, where the estimate is
the one-month dip, exports reach a placebo p of **0.054** and imports **0.151**.

So the monthly answer is not "no effect". It is: a sharp contraction in the month of the
uprising, at the edge of what this series' ordinary month-to-month movement would produce
anyway, and gone within a year.

### 33. The annual estimate is precise about a number it cannot pin down

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="33-honest-vs-conventional-dark.png">
  <img alt="Conventional and bias-aware confidence intervals across bandwidths, monthly and annual" src="33-honest-vs-conventional-light.png">
</picture>

A conventional standard error asks only how much an estimate would move under resampling.
It is silent on the local polynomial being the wrong shape, which is the dominant error
when the bandwidth is wide. Kolesár and Rothe (2018) and Armstrong and Kolesár (2018)
close that gap: bound the curvature of the conditional mean, take the worst-case bias over
that class, and widen the interval to cover it.

Applied here the two frequencies come apart completely. The **monthly** series can shrink
its bandwidth until the bias bound is negligible, and the honest interval is within
**0.3%** of the conventional one at six and nine months. The **annual** interior–coastal
gap cannot: its honest interval runs from **7.4× the conventional one at a five-year
bandwidth to 23× at ten years**, and it spans zero at every bandwidth — including the bandwidths
where the conventional interval excludes zero and would have been reported as a finding.

The annual panel's apparent effect of about **+0.1 pupils per teacher** is not a small
effect precisely measured. It is a number the design cannot separate from the curvature of
a trend.

### 34. Both series need the same number of periods; only one can afford them

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="34-randomisation-floor-dark.png">
  <img alt="Smallest attainable p-value against the calendar time a window spans, monthly and annual" src="34-randomisation-floor-light.png">
</picture>

Local randomisation replaces continuity with a stronger but exact assumption: inside a
narrow enough window, treat the cutoff as if it had landed at random among the periods.
The catch is arithmetic. A window admits only as many arrangements as it holds periods,
and that caps the p-value it can return **before any outcome is read**.

Reaching 0.05 takes three periods either side. For the monthly series that is three months
around January 2011 — a neighbourhood over which little else changed. For the annual
series it is three years, a window across which the interior–coastal gap moves by **1.2
pupils per teacher** on its own, which is precisely the trend local randomisation assumes
away. And the tell is that the annual randomisation p-value comes out **exactly at the
floor** (0.0286 at ±3 years): the observed split is the single most extreme arrangement,
which is what a monotone trend produces and what a discontinuity need not.

**What the four of them establish.** RDiT is the right design for this question, and at
monthly frequency it works: it identifies a jump, it detects the shocks it should, and its
honest and conventional intervals agree. Pointed at January 2011 it finds a one-month
contraction in trade that does not persist and barely clears the series' own noise. For
regional inequality the outcome is published annually, and there the same design cannot be
brought close enough to the cutoff to identify anything — which is a statement about the
publication frequency of Tunisian regional statistics, not about the revolution.

---

## Which goods are consumed unequally, and can 2011 be blamed?

These three are the one place in this directory where a composite index appears. The
question they ask — which *goods* are spread unevenly across the country — cannot be put
without reducing seven regional means to a single number per good, because otherwise
goods cannot be ranked against one another. What is compressed is seven observed values,
every one of them published in `tn_expenditure_by_product_region`, and the measure
compares regions rather than households. Everywhere else in this directory the rule
still holds.

The underlying table had never been read. Each survey volume prints mean expenditure per
person on every product broken down by the seven grandes regions; 2021 as a spreadsheet
annex, and 2005, 2010 and 2015 only as Arabic-language PDFs. Reading them yields 12,832
product-region-wave observations and 1,604 spatial Ginis across four waves, of which 111
goods appear in all four.

### 35. Medicine is bought everywhere; building a house is not

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="35-spatial-gini-by-good-dark.png">
  <img alt="The nine most and nine least regionally concentrated consumption goods, 2021" src="35-spatial-gini-by-good-light.png">
</picture>

Across 133 goods above 20 dinars per person per year, the spatial Gini runs from **0.034
to 0.487** — a fourteen-fold spread. What sits at each end is not random. The most evenly
spread are the things a household buys wherever it lives: bottled drinks, industrial milk,
pharmaceuticals, medical consultations, bus fares. The most concentrated are land for
building, construction spending, actual paid rent, mineral water and bananas — goods that
are either urban, regionally produced, or bought only where there is money to spare.

The correlation between a good's spatial Gini and its national spend is **−0.34**: bigger
budget items are more evenly spread, which is Engel's law showing up geographically.

### 36. The only interval in which regional gaps closed contains the revolution

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="36-spatial-gini-series-dark.png">
  <img alt="Spatial Gini per good across four survey waves, and the change over each interval" src="36-spatial-gini-series-light.png">
</picture>

For the 111 goods priced in all four waves, the spatial Gini fell over 2010–2015 for
**62% of them**, median change **−0.016**. Over the two intervals either side it rose:
**+0.005** for 2005–2010 and **+0.013** for 2015–2021.

That is a real pattern and it is worth stating plainly, but it is not evidence about the
revolution. There are three intervals, so one of them is the extreme by construction; the
2010–2015 window also contains the 2011 wage settlements, the public-hiring expansion and
the collapse in tourism; and the surveys bracket a five-year window rather than measuring
anything at the cutoff.

### 37. Four five-yearly observations cannot locate a discontinuity in 2011

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="37-why-rdd-fails-on-waves-dark.png">
  <img alt="Why regression discontinuity cannot be applied to four quinquennial survey waves" src="37-why-rdd-fails-on-waves-light.png">
</picture>

Regression discontinuity estimates a limit as the running variable approaches the cutoff.
The surveys ran in 2005, 2010, 2015 and 2021: the nearest observation before January 2011
is **one year** before it and the nearest after is **four years** after, with nothing
between. There is no neighbourhood to take a limit over, and the same local linear
estimator that works on monthly trade in figure 31 **refuses every bandwidth here** for
want of degrees of freedom.

Permutation inference reaches the same verdict before any outcome is read. Four periods
split two and two admit six arrangements, so the smallest attainable two-sided p-value is
**0.17** — no good's series, however it moves, can be significant at five percent.

This is the third time the same constraint has bound in this directory, and it is always
the same constraint: not the estimator, but how often the statistic is published.
Monthly trade identifies a discontinuity; the annual governorate panel cannot get close
enough to the cutoff for an honest interval to exclude zero; and four quinquennial survey
waves cannot support the design at all.

---

### 38. Job offers concentrated sharply; almost nothing else did

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="38-lorenz-across-governorates-dark.png">
  <img alt="Lorenz curves of job offers across the 24 governorates in 2010 and 2023, and the share going to the least-served half of the population for nineteen services" src="38-lorenz-across-governorates-light.png">
</picture>

Governorates are ordered from least to best served per person, so the diagonal is the
distribution in which every Tunisian is served equally regardless of where they live, and
distance below it is concentration.

The half of Tunisians living in the least-served governorates received **35% of job offers
in 2010 and 20% in 2023**. That fall of 15 points is roughly **four times** the next
largest among nineteen services complete in both years.

Two qualifications the year-by-year series adds, and figure 41 shows directly. **2010 is a
local peak** — 2005 to 2009 run between 28% and 32% — so the endpoint pair flatters the
size of the fall. And the decline is not evenly spread: 9 of the 15 points accrue over the
nine years to 2019, while **8 points arrive in the single year 2019 to 2020**, with a
partial recovery after. The faint lines are a real downward drift, but the largest single
move in them is the first pandemic year.

Nothing else in the panel moves like it. Ten of the nineteen became more concentrated and
nine less, most of them barely: primary teachers shifted two points, primary schools one.
Three moved the other way — **remittances, library subscriptions and fixed telephone
lines all spread out**, which is worth noticing, because two of those are things households
acquire rather than things the state allocates.

**This is a description of two years, not an effect of the revolution.** The shock is
national and simultaneous, so there is no untreated governorate to compare against and no
average effect to recover; see the note above figure 27. One further caution specific to
this series: job offers are administrative counts registered at employment offices, so a
change in *where offers are registered* would look identical to a change in where they are.


### 39. Regional inequality, service by service, 1994–2023

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="39-gini-evolution-by-service-dark.png">
  <img alt="Sixteen small multiples, each showing the Gini of one service across governorates from 1994 to 2023, with 2011 marked and 2020 to 2023 shaded" src="39-gini-evolution-by-service-light.png">
</picture>

The first figure in this directory to use a composite index, and the reason the constraint
was lifted: "how did inequality evolve" cannot be answered by an observed quantity, because
evolution needs one comparable number per year.

Sixteen services have both a long pre-2011 run and a long post-2011 run. **Most of them are
flat or falling.** Library book stock, public libraries, library books lent, marriages and
library subscribers all become *less* unequally distributed across the period; primary
schools, teachers and classrooms barely move at all. The Gini for primary provision sits
around 0.22 and stays there for thirty years.

Two rise. Bank branches climb from 0.47 to 0.53 and then stop when the series does in 2018.
Job offers rise from about 0.40 to about 0.55 — and the shaded band shows where: the rise
is concentrated in 2020–23, not at the dashed line.

The panels use the constant geography, Ariana and Manouba combined, which is what lets them
start in 1994 rather than 2000; see the note on figure 42 for what the unweighted reading
costs.

### 40. 2011 is not the year regional inequality changed

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="40-is-2011-special-dark.png">
  <img alt="Two bar panels by year: the share of services whose Gini rose, and the mean change in Gini, with 2011 highlighted" src="40-is-2011-special-light.png">
</picture>

This is the figure to read before attempting any design that puts a cutoff at 2011.

Across the sixteen services, **2011 ranks 9th of 29 years** by how many of them grew more
unequal, and **4th** by the size of the average move. The second of those is not nothing —
2011 is a real positive bump, and the figure marks it rather than dismissing it. But 1995,
2019 and 2020 are all larger, and on the breadth measure 2011 sits in the middle of the
distribution of years.

A regression discontinuity needs the cutoff to be distinguishable from the years around it.
Here it is not, and no amount of bandwidth tuning creates a discontinuity that the annual
series does not contain. That is a statement about what this data can support, not about
whether the revolution mattered.

### 41. The biggest break in the data is the pandemic, not the revolution

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="41-covid-contamination-dark.png">
  <img alt="Left, the Gini of job offers across governorates 1995 to 2023 with 2020 to 2023 shaded; right, the post-2011 slope break computed through 2023 and through 2019" src="41-covid-contamination-light.png">
</picture>

Job offers carry the largest post-2011 slope break of any series here, and this figure is
why that statistic should not be read as evidence about 2011.

Fitting a linear post-2011 trend through 2023 reports a break of **+0.127** Gini per decade.
Fitting the same thing through 2019 only reports **+0.028** — a factor of 4.5. The
difference is four pandemic years in which the Gini jumps from 0.47 to 0.59 and `p90/p10`
goes from about 11 to 41.

The pre-2011 years are genuinely flat, which is what made the break look credible in the
first place. What is wrong is running one straight line from 2011 to 2023 across a series
that contains a second, much larger shock, and attributing the result to the first one.

Job offers are administrative counts registered at employment offices, so a change in
*where offers are registered* would look identical to a change in where they are. Both
readings are consistent with a pandemic that closed offices unevenly.

### 42. Inequality between governorates is not inequality between Tunisians

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="42-weighted-or-not-dark.png">
  <img alt="Left, the Gini of primary pupils read weighted and unweighted from 2005 to 2023; right, a dumbbell of the two readings for 24 services" src="42-weighted-or-not-light.png">
</picture>

Weighting governorates by population asks about a Tunisian picked at random. Leaving it out
asks about an administrative unit picked at random. They are different questions and they
give different answers.

**Weighting lowers the measured Gini in all 24 services** where both readings exist, by
0.047 on average and by 0.098 for cinema screens, the largest gap. The reason is that the
governorates at the extremes of these distributions are the small ones: Tozeur and Tataouine
move an unweighted index far more than their share of the population justifies.

This matters for interpretation rather than for arithmetic. A governorate-level regression
weights every governorate equally, so it implicitly uses the unweighted reading — the one
that, on this evidence, systematically overstates inequality between people. And the
weighted family cannot reach before 2005, because no yearbook in the corpus prints
governorate population earlier. So a long pre-period and a population-weighted index are
not simultaneously available here, and that trade has to be made explicitly.

### 43. Which index you choose is a choice about what counts

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="43-index-disagreement-dark.png">
  <img alt="Left, five inequality indices for library readers normalised to their 1995 values; right, the change in Theil-T against the change in Theil-L for sixteen services" src="43-index-disagreement-light.png">
</picture>

Reporting a single index hides a decision. Each of these weights a different part of the
distribution, and on real data they disagree.

For library readers, **four of the five say the distribution grew more unequal after 2011
and Atkinson ε=2 says the opposite.** ε=2 weights the worst-served governorates most
heavily, so the two readings together say something the Gini alone cannot: the bottom of the
distribution caught up while the spread above it widened.

The right panel generalises that. Theil-T is top-sensitive and Theil-L bottom-sensitive, so
a service above the dashed line moved more at the bottom of its distribution than at the
top. Most sit close to the line — the two Theils usually agree — and the ones that do not
are where a distributional story exists to be told.

### 44. The revolution left no discontinuity in regional inequality

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="44-gini-rdd-governorates-dark.png">
  <img alt="Left, between-governorate Gini for nineteen services and their average; middle, the share of services rejecting a permutation test at each candidate cutoff year; right, the local-linear jump at 2011 with bias-aware intervals" src="44-gini-rdd-governorates-light.png">
</picture>

The regression discontinuity the governorate strand was built for, and it returns a null.
What makes the null worth drawing rather than stating is the middle panel.

Run at January 2011, a local randomisation test rejects for **nine of the seventeen
services** it can score. Taken alone that reads as a finding. Run the identical test at
every other year from 2001 to 2018 and it rejects for **between 39% and 65% of services at
every one of them** — 2011 ranks sixth of eighteen. The test compares a mean before with a
mean after, and most of these series trend, so it rejects whatever year is pointed at. The
2011 rejection is trend, not a break, and nothing but the placebo shows that.

The right panel is the estimator that removes the trend: local linear with the
Armstrong–Kolesár bias-aware interval. **Zero lies inside every interval.** The worst-case
bias also exceeds the point estimate for every service, so the honest reading is *not
identified* rather than *precisely zero* — with seventeen pre-cutoff years there is no
bandwidth small enough to be local and large enough to fit.

Two limits worth carrying. This is the unweighted Gini, because population weighting needs
a governorate denominator the corpus does not print before 2005, so it measures inequality
across administrative units rather than across Tunisians. And a design with nineteen
services and eight years either side can rule out a large jump, not a small one.

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
Figure 8 comes from the 2020 poverty map. Figures 17 and 19 come from the INS statistical
yearbooks, and figure 18 sets one of those against the panel. Figures 6, 7, 10, 11, 12 and
20–26 are recomputed from the EBCNV 2021 microdata. Figures 27–30 come from the statistical yearbooks'
governorate panel, and figures 31–34 from the same corpus's monthly trade table (14.1)
alongside that panel. Figures 35–37 come from `tn_spatial_gini_by_product`, built by
reading the product-by-region tables out of all four survey volumes. Figure 38 comes from
`tn_governorate_comparable`, the per-head normalisation of that same governorate panel, and
figures 39–43 from `tn_governorate_inequality`, the conventional indices computed on it, and figure 44 from those indices together with `tn_rdit_estimates`. Every claim above is reproducible from `scripts/make_figures.py`, and
the numbers quoted here were recomputed from the data before being written rather than
read off the charts.

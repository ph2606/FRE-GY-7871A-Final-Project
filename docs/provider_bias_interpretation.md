# Interpreting the provider bias proxy

Prepared October 15, 2026 for the provider comparison requested after the original October 13 snapshot. The primary study's macro/media forecast comparison remains separate from this supplementary provider analysis. New retrieval dates must remain visible even when the compared releases occurred before the study cutoff.

## Display and benchmark

Use providers on the **x-axis** and the signed bias proxy on the **y-axis**, as requested. A precise y-axis label is **Excess negative headlines (percentage points)**. A suitable title is **Provider bias proxy: same-release negativity**. The term “bias proxy” refers only to the operational, relative measure defined here.

For provider `p` and official release `e`, let `n_pe` be the fraction of its sampled titles that the frozen contextual model classifies negative. Let `K` providers all cover the identical retained release set `E`. Define

`b_pe = 100 × [n_pe − mean(n_qe for all other retained providers q)]`

`B_p = mean(b_pe over the common releases e)`.

Average first within provider/release, then equally across releases. Otherwise prolific providers or unusually heavily covered releases would receive different effective event weights. The other-provider benchmark is equally weighted across providers, rather than weighted by their number of titles. Document the exact classifier negative-label rule; a negative argmax class is different from a negative probability cutoff or negative continuous score.

A positive value means **more negative classified wording than the other providers on the same releases**. A negative value means less negative wording. Zero means equal to the selected panel benchmark. It does not mean unbiased, factually correct, politically centrist or appropriate in absolute terms. A difference of 10 percentage points is a share difference, not 10% greater probability and not a percentage of false reporting.

Caption template: “Each bar is a provider’s negative-title share minus the equal-weight mean of the other providers covering identical official releases, averaged equally across releases. Error bars resample calendar months jointly across providers. Zero is the sampled-panel reference. Title-only, model-based wording differences do not establish factual distortion, political ideology or effects on consumers.”

## What matching improves and what remains

The shared release dates prevent a provider from appearing more negative solely because its sampled events had worse aggregate news. They do not make the stories identical. An employment release contains payrolls, unemployment, wages, participation and revisions; a truthful headline can emphasize any of these. Differences can therefore combine presentation, legitimate target-audience interests and selection of different factual components. Matching cannot identify a pure framing treatment or prove inappropriate pessimism.

Keep the event registry and inclusion window fixed before reading provider scores. Include only titles genuinely addressing the named release, rather than any economy item appearing near its date. Separate web headlines from television transcripts, commentary and social posts. Report provider and event counts, duplicate/syndication treatment, search caps, missing providers and late/revised headlines. Search failure is not evidence that a provider ignored an event.

The primary chart should use the same event set for every displayed provider, with a declared minimum support. If missingness prevents this, show an explicit insufficient-support result instead of assigning a provider zero. An available-event comparison may be a sensitivity, but its provider differences can partly reflect different event baskets. Adding or removing providers changes the leave-one-out reference and can change each bar even when a provider’s text stays fixed.

The original 300-title annotation packet does not establish accuracy for newly added CNBC or Fox titles. Classifier performance can differ across providers even for the same event. Label this extrapolation explicitly. Match display names to observed publication domains: Fox News and Fox Business are distinct publications, and an umbrella aggregation requires a documented decision. Do not pool them merely because the user mentioned “Fox.”

Resample months jointly to preserve all provider comparisons and the two release types within a month. State the number of calendar-month clusters. With a short January–September window, intervals have limited precision and rely on the chosen resampling assumptions. They condition on the selected releases, retrieval method and frozen classifier. They omit classifier uncertainty, missing/deleted titles and the uncertainty of generalizing to all of a provider’s output. Pointwise intervals do not provide simultaneous confidence in a ranking; avoid announcing the “most biased” provider from bar height alone.

## Research grounding and construct boundaries

Budak, Goel and Rao distinguish which issues outlets cover from how they present those issues. Their ideological measurement uses human judgments of party treatment and source-blinding; their construct is broader and differently anchored than generic negative economic wording. This supports separating selection, presentation and annotation validity, but does not validate this project's custom score. [Budak, Goel and Rao, *Public Opinion Quarterly* 80(S1), 250–271, 2016, author-hosted paper](https://5harad.com/papers/mediabias.pdf).

Gentzkow and Shapiro anchor a newspaper-language slant index to language used by congressional Republicans and Democrats. Their explicitly partisan reference illustrates why a model trained to recognize positive and negative wording cannot automatically supply an ideological scale. The present provider plot does not replicate their index. [Gentzkow and Shapiro, *Econometrica* 78(1), 35–71, 2010, author-hosted paper](https://web.stanford.edu/~gentzkow/research/biasmeas.pdf).

Soroka, Fournier and Nir measure physiological responses while participants watch video news, finding an average negativity response with substantial individual variation. This concerns audience reactions, not a negative-headline proportion. Measuring negative content alone cannot establish that readers exhibit the same cognitive mechanism or that national consumer sentiment falls because of it. [Soroka, Fournier and Nir, *PNAS* 116(38), 18888–18892, 2019, full primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC6754543/).

Factual bias needs a separately specified accuracy benchmark: match the title's economic metric, period, units, release status and uncertainty to the official information available at publication. Partisan slant needs a separately justified political target/reference. Consumer impact needs exposure and identification. This chart supplies none of those by itself; it is a comparative content diagnostic suitable for reviewing source composition in a forecasting workflow.

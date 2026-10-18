# Economic narratives and consumer sentiment

Panagiotis Housos | ph2606 | AI Applications in Finance | Fall 2026

This final project studies economic narratives and University of Michigan consumer sentiment ahead of the November 3, 2026 midterms. The economic information cutoff is **October 13, 2026**, America/New_York. The **October 15 revision** adds a separate provider comparison of January–September releases, and the **October 17 extension** evaluates investment allocations. Open [the executed notebook](final_project.ipynb) for the computed report and aggregate exhibits. The local deliverables are a 12-page LaTeX PDF, an interactive standalone dashboard, a standalone provider bar graph, and a PowerPoint with speaker notes.

People can feel worse about the economy than official numbers suggest. This project asks whether selected news wording helps explain that difference, then tests three aggressive trading ideas using the wording alone. The economic-model answer changes when we account for persistent survey scores and changes in survey methods. The news measure does not reliably improve forecasts. Two wording-only trading rules make a historical profit after assumed costs, but all three finish below an ordinary S&P 500 fund and suffer larger worst percentage losses. These findings do not prove that news caused people's feelings or establish a reliable way to earn future profits.

**A quick vocabulary guide:** a survey asks people questions; an index combines answers into a score, not a dollar amount or a percentage of unhappy people. A forecast is a model's estimate. The sentiment gap is actual score minus model estimate. A percentage point is the difference between percentages: 40% minus 30% is 10 percentage points. The trading experiment's **wording gap** is a different measure: how much more often selected national headlines are labeled negative than one local outlet's headlines. Negative news can be accurate. The dashboard explains these terms before its charts and gives plain-language examples of the fund choices and losses.

**Material assignment limitation:** the requested two independent human annotators were unavailable. Blinded 300-item human worksheets, guide, adjudication workflow and validation code are prepared. Two separate AI agents independently reviewed the same 300 items without seeing classifier outputs or each other's labels. Their diagnostic concordance is explicitly AI, and cannot satisfy the human requirement. No human accuracy, agreement or validated factual-error rate is invented.

New to this topic? Start with the [plain-language reading guide](docs/READING_GUIDE.md), including the two different gaps, a worked trading decision and a short glossary.

## Measurement and timing

The supplied spreadsheet was read first and audited by its four separate date columns. All 584 inflation values match **core** PCE within 0.0001 percentage point; the assignment requires headline PCE, so the main analysis recomputes headline YoY inflation from PCEPI. The spreadsheet's Q3 GDP value is excluded because the advance estimate is scheduled after the cutoff. October sentiment 46.3 is the official October 9 preliminary estimate and is kept separate from completed-final evaluation.

The economic panel starts in January 2010. BLS U-3, BEA PCEPI, real GDP and real disposable personal income are acquired using actual historical ALFRED snapshots for each first-of-month prediction origin, plus a cutoff snapshot. Growth rates are computed entirely within the same vintage. GDP remains a released quarterly predictor; it is not interpolated into synthetic monthly GDP. Historical within-day release times are unresolved, so an origin means the end of that calendar day. Official Michigan headline, Current Conditions and Expectations are separate outcomes. Their historical tables are latest-final targets, rather than archived survey-target vintages; revision leakage in those targets cannot be ruled out.

M1 uses U-3, headline PCE YoY and quarterly real GDP growth at an annualized rate. M2 adds previous-month contextual media tone. M3 additionally includes real disposable income YoY and cumulative 36-month PCE price growth. The comparison also refits controls-only, AR1, autoregressive macro and persistence benchmarks on common dates. Expanding-origin forecasts, rolling-window and seasonal checks, alternate GDP growth, survey-mode ramp, media lags/source/dictionary/framing sensitivities, coefficient stability, interval coverage and a future-tone diagnostic are retained. The future-tone placebo is explicitly excluded from prediction. HAC inference and multiple-test adjustments do not turn these associations into causal effects.

The survey-mode ramp is known collection design, not a causal estimate of the mode effect. Michigan's 2026 methodological reports also show that low sentiment persists in consistent-mode comparisons. Party and demographic descriptions are published context; individual affiliation, exposure and beliefs are unavailable.

The revision adds ADF/KPSS diagnostics and exploratory differenced/dynamic forecasts on the same 44 assessment months. These warn against a mechanical interpretation of persistent levels and do not establish reliable media gains. The new two-contrast family is separate from the three primary loss contrasts; HAC bandwidth checks are sensitivity analyses. The collector also explicitly caps final Michigan targets at September, preventing a later clean download from admitting October's post-cutoff final release. Earlier target revisions remain an acknowledged limitation.

## Media and annotation

Google News RSS retrieves the same broad economic query for AP, Reuters, NPR, Gothamist, Texas Tribune and Colorado Sun. Hacker News Algolia supplies user-posted story titles. A fixed hash samples at most 12 titles per outlet-month. Coverage runs January 2020 through October 12, 2026; October is partial and excluded from outcome evaluation. Titles average within outlet, outlets within group, and groups into the monthly measure. Source counts, caps, geographic uncertainty, exclusions and coverage are retained.

This selected title panel measures content supply, not exposure. Ranked RSS caps, historical edits, missing index snapshots and HN's selected audience prevent a deployable historical real-time backtest. Conservative news availability uses the following New York midnight; social creation times do not establish original unedited wording. Content published after a forecast origin cannot enter that origin's signal. Objective relevance refinements and the original annotation-pool preservation are disclosed in [the protocol amendments](docs/MEDIA_PROTOCOL_AMENDMENTS.md).

The pinned CardiffNLP RoBERTa revision is `3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7`. Assets are hash-verified, no remote code runs, and it is not fine-tuned on project outcomes. VADER is the conventional comparison. The contextual model dates from 2022; measurements on earlier text therefore use a later representation. Literal frame/salience/attribution rules are provisional. Numeric claims are screened for verification, and a limited official-reference audit is distinct from corpus-wide factual validation. Political-name swaps and source-prefix tests diagnose sensitivity without proving bias. The codebook and model specifications are in [MEDIA_CODEBOOK.md](docs/MEDIA_CODEBOOK.md).

No generative prompt produces the primary empirical score. The separate AI annotation instructions and method are disclosed in [AI_USE.md](AI_USE.md); detailed item-level labels remain local. Human validation runs on separately completed forms and never treats AI labels as human.

## Provider bar graph

The supplemental chart places **news providers on the x-axis** and a **relative negativity-bias proxy in percentage points on the y-axis**. CNBC, Fox News and Fox Business are separate publications. Query dates, official release events, neutral search terms, provider selection, scoring and uncertainty are recorded in [the final protocol](docs/PROVIDER_COMPARISON_PROTOCOL.md), with retrospective relevance and coverage refinements in [the amendments](docs/PROVIDER_PROTOCOL_AMENDMENT.md). The separate provider collection never changes the original monthly media series or forecasting results.

Within each identical release event, average each provider's negative-headline classifications, then subtract the equal-weight mean of the other providers. Average those differences equally across the common releases. Positive means more negative classified wording than the selected same-release peers; zero is a peer reference, never objective neutrality. The final chart compares six providers over six common releases, with 72 headlines. The chart reports counts and conditional 95% calendar-month resampling stability ranges. Unsupported providers receive no comparable bar, rather than a zero. Continuous-probability, dictionary, event-bootstrap, one-title and release-family sensitivities are retained.

The classifier has not been human-validated on the new provider sample. Truthful selection of different release components can change framing, while search selection and classification error lie outside the plotted intervals. With at most nine month clusters, precision and generalizability are limited. This is not a measure of ideological slant, false reporting, exposure or causal consumer impact. See [the interpretation and primary research](docs/provider_bias_interpretation.md).

The primary supplement uses a documented AI title/date relevance review, plus mechanical exclusions for previews, unrelated metrics, market reactions and multi-topic roundups. Administrative branding and a leading Watch prefix are removed before scoring; raw titles are preserved. Detailed review decisions remain local at `data/annotations/provider_relevance_review.csv`. A fresh clone can acquire/score the automated candidates, but exact reproduction of this refinement requires the saved local review or a new documented review. It must not be represented as human validation or an untouched test. Sensitivities change some provider estimates and signs; the bars are not a provider-reputation ranking.

## Three aggressive wording-only trading ideas

Use only the negative-title shares of **Reuters, NPR and Colorado Sun**, not economic numbers, market-price trends or survey forecasts. Reuters and NPR receive equal national weight; subtract Colorado Sun's share. Compare the previous completed month's difference with the middle value of the preceding 12 months, excluding the month being tested. This is a relative-wording proxy, not a verified measure of factual or political bias. The fixed three-outlet roster has complete coverage; the separate six-release CNBC/Fox provider graph is not a trading history.

| Fixed idea | Above-usual national-minus-local gap | Below-usual gap |
|---|---|---|
| Fade the gap | UPRO | SPXU |
| Follow the gap | SPXU | UPRO |
| Wait for a turn | UPRO only if the gap is also falling | SPXU only if the gap is also rising |

UPRO aims for three times the S&P 500's daily move; SPXU aims for three times the opposite daily move. These are daily targets before fees, not three times a whole month's return. BIL holds short US Treasury bills. Every rule holds one fund at a time; missing data, ties and waiting states use BIL. The rules were fixed before their new returns were calculated, after earlier project findings and SPY/BIL history were known. No settings were searched to find a winner.

From **February 2, 2021 to October 2, 2026**, with ten cents paid per $100 bought or sold, including entry, switches and final sale:

| Rule / comparison | Final account from $100 | Worst fall from an earlier high | Account high → low at that percentage fall |
|---|---:|---:|---:|
| Fade the gap | $143.52 | −63.7% | $200.60 → $72.75 |
| Follow the gap | $18.52 | −89.1% | $111.27 → $12.16 |
| Wait for a turn | $138.68 | −34.4% | $144.82 → $94.96 |
| Ordinary S&P 500 fund (SPY) | $217.34 | −24.5% | $126.74 → $95.70 |

The account can rise before falling, so a drawdown is not a loss calculated from the original $100. The last column shows the high and later low at the worst **percentage** fall; another period can have a larger dollar fall. None of the three ends above SPY, and all three have a deeper worst percentage fall. Greater leverage makes the experiment more aggressive, not the evidence stronger. Positive past profit is not proof of future skill, and no rule is retuned after these results.

The history is reconstructed using retrospectively collected titles, a later language model and revised adjusted fund prices. Sparse local months can contain one title; different topics and places can change the gap even when every story is true. Taxes and nonlinear market impact are omitted. See the [simple signal recipe and exact counts](docs/BIAS_SIGNAL_METHOD.md), [frozen trading protocol](docs/BIAS_TRADING_PROTOCOL.md) and [results including all reference portfolios](docs/BIAS_TRADING_RESULTS.md). No trades were placed.

## Earlier allocation comparison: a separate reference

The October 17 extension tests a fixed macro-and-trend allocation against SPY buy-and-hold, BIL buy-and-hold and a monthly-rebalanced **60% SPY / 40% BIL** mix. The protocol preceded calculation of strategy performance, after the economic findings were known. From **January 2, 2015 through October 2, 2026**, $100 becomes **$188.01** under the timing rule, **$280.16** under the fixed mix, **$453.78** in SPY and **$125.29** in BIL. Each path pays **10 basis points per dollar bought or sold**, including entry and final liquidation; both sides of a switch incur costs. The fixed mix is the preferred research reference retrospectively, with 9.17% net CAGR and a 20.78% maximum drawdown, versus 5.52% and 20.11% for the timing rule. SPY delivers more growth with a 33.72% maximum drawdown. This comparison does not establish an optimal allocation or future profit.

The primary rule holds 80% SPY when prior-month price exceeds its ten-month average and an as-of, custom three-month unemployment deterioration measure is below 0.50 percentage point; otherwise it holds 20%. The remainder is BIL, a short Treasury-bill ETF. Signals use prior completed-month prices and actual ALFRED vintages; execution is at the first joint ETF close strictly after the origin. Yahoo adjusted closes approximate split/distribution-adjusted total returns, with fractional units and reinvestment. Taxes and nonlinear market impact are omitted, and the cost rate is assumed.

Secondary gap/media overlays are pseudo-real-time diagnostics over 44 origins, rather than deployable historical signals: survey targets are revised and media wording is retrospectively reconstructed using a later representation. Every gap is negative, so its overlay is a constant ten-point equity increase; raw return gains can reflect exposure. Positive historical net return does not establish alpha or promise future profitability. The provider bars never select trades. See the [protocol](docs/INVESTMENT_PROTOCOL.md) and [computed results and limitations](docs/INVESTMENT_RESULTS.md). No trades were placed.

## Reproduce

Use Python 3.12. The lock records the observed Windows environment. Other platforms should resolve `requirements.txt` for their platform and record a new lock. From the project folder in PowerShell:

```powershell
python -m venv .venv
$projectPython = '.\.venv\Scripts\python.exe'
& $projectPython -m pip install -r requirements-lock.txt

# Read-only public acquisition; caches are hash-checked.
& $projectPython scripts/01_collect_economics.py
& $projectPython -m src.media acquire --start 2020-01-01 --end 2026-10-13
& $projectPython -m src.media score
& $projectPython -m src.annotation_packet
& $projectPython -m src.provider_bias all

# Recompute actual observations, test methods, build and execute deliverables.
& $projectPython scripts/03_analyze.py
& $projectPython -m src.dynamics
& $projectPython -m src.investing all
& $projectPython -m src.bias_trading all
& $projectPython scripts/04_build_deliverables.py
& $projectPython scripts/05_execute_notebook.py
xelatex -interaction=nonstopmode -halt-on-error report.tex
xelatex -interaction=nonstopmode -halt-on-error report.tex
Copy-Item -LiteralPath report.pdf -Destination Panagiotis_Housos_Final_Project.pdf
& $projectPython scripts/06_freeze_validate.py --run-tests
& $projectPython scripts/07_package_submission.py
Start-Process -FilePath dashboard.html
```

The source spreadsheet is optional for estimating the official panel, but reproducing its audit requires `Perceptual_Bias_Data.xlsx` in the parent directory. It is intentionally not uploaded. Model weights require about 500 MB on first download. Endpoint access and mutable content can change; re-downloads reproduce the method rather than guaranteeing the original sample. Existing caches are reused; to refresh intentionally, archive the old cache and change the cutoff with an explicit new protocol version rather than silently overwrite historical results. [SNAPSHOT.md](SNAPSHOT.md) binds this submission to local hashes.

For actual completed independent human labels:

```powershell
& $projectPython -m src.validate_annotations --a data/annotations/human_final_A_blinded.csv --b data/annotations/human_final_B_blinded.csv --label-type human
# Supply an adjudicated file only after the independent labels are locked.
```

For separately identified AI development diagnostics, use `--label-type ai_diagnostic` and the `ai_annotator_A.csv` / `ai_annotator_B.csv` paths. Detailed worksheets and diagnostics are not committed under the no-data policy. Blank forms produce an explicit pending status. A fresh clone can regenerate forms but cannot reproduce unavailable human work or deterministically recreate independent AI judgments; the notebook retains aggregate diagnostic outputs.

## Dashboard and prospective updates

Open local `dashboard.html` for interactive date zooming, series toggles and hover values. Its ten charts show economic forecasts and uncertainty, gaps, provider framing, media measures, source coverage, calibration, economic inputs, the earlier allocation reference and the new wording-only trading results. A first-use glossary, three rule cards and dollar examples explain the evidence without assuming finance knowledge. Supporting tables retain model errors and release events. It clearly labels unvalidated measures, incomplete October, unavailable factual accuracy and the limits of retrospective investment results. The generator is [src/dashboard.py](src/dashboard.py). No external hosting, credentials or paid services are needed.

Future updates must preserve previous vintages, verify official calendars, use only information published by each origin, and rebuild every artifact. October 23 Michigan final and October 29 GDP/PCE releases are after this cutoff. Election proximity is context, not an identified treatment. [The causal design](docs/causal_design.md) details a prospective truthful-framing experiment, falsification and national transportability requirements; no participants were recruited.

This submission intentionally freezes the October 13 snapshot. Advancing the monitoring period requires changing `CUTOFF` in `src/economics.py`, the origin range and cutoff-vintage calls in `scripts/01_collect_economics.py`, the monitoring target/preliminary-source record in `scripts/03_analyze.py`, the media acquisition `--end`, and cutoff/period descriptions in the dashboard and shared narrative. Verify and replace the preliminary record with the correctly dated official release; never carry October's 46.3 into a different month. Archive mutable Michigan/source-response caches before acquisition so the prior snapshot remains available. Then rerun the documented pipeline, validation and snapshot. Merely rerunning the frozen commands does not advance the study date.

Also update `LAST_FINAL_TARGET_MONTH` only when the corresponding final survey release is available. The provider supplement's event registry/window and both investment protocols' origin/execution dates are frozen independently. Preserve the wording signal's fixed roster and full preceding-12-month baseline; incomplete October cannot enter a completed-month signal. Do not extend a historical wealth chart by silently changing its evaluation window. Rerunning the saved notebook checks its input hashes and stops on changed inputs; rebuild it after an intentional refresh so the narrative, calculated tables and saved figures stay consistent.

The original AI review packet has 300 titles, of which 277 survive final relevance screening. The separate final human packet retains those 277 and supplements 23 eligible titles, yielding 300 final-corpus items in independently shuffled blank forms. The original AI labels and scores remain unchanged. Human and AI evaluations therefore have explicitly different eligible pools.

## Submission policy

Git includes source, meaningful tests, dependencies, the executed notebook, aggregate snapshot and documentation. **No datasets are committed**: raw responses, prices/indices, item text, annotations, derived tables, model weights, figures, caches and generated deliverables remain local/ignored. The PDF, PowerPoint and dashboard are supplied separately. No institutional submission, external messaging or financial trade was performed. See [AI_USE.md](AI_USE.md) and [primary sources](docs/sources.md).

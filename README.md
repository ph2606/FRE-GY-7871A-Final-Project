# Economic narratives and consumer sentiment

Panagiotis Housos | ph2606 | AI Applications in Finance | Fall 2026

This final project studies economic narratives and University of Michigan consumer sentiment ahead of the November 3, 2026 midterms. The information cutoff is **October 13, 2026**, America/New_York. Open [the executed notebook](final_project.ipynb) for the computed report and aggregate exhibits. The separate local deliverables are a 12-page LaTeX PDF, an interactive standalone dashboard, and a nine-slide PowerPoint with approximately 6–7 minutes of speaker notes.

The main conclusion is that a large gap from the three-indicator economic model is sensitive to model dynamics and survey-method controls. Persistence is a demanding benchmark. Lagged media tone provides no robust incremental forecasting evidence in the common chronological assessment. This is an observational, retrospective content analysis; no causal national media effect or investment strategy is established. Exact computed metrics are preserved in the notebook and snapshot.

**Material assignment limitation:** the requested two independent human annotators were unavailable. Blinded 300-item human worksheets, guide, adjudication workflow and validation code are prepared. Two separate AI agents independently reviewed the same 300 items without seeing classifier outputs or each other's labels. Their diagnostic concordance is explicitly AI, and cannot satisfy the human requirement. No human accuracy, agreement or validated factual-error rate is invented.

## Measurement and timing

The supplied spreadsheet was read first and audited by its four separate date columns. All 584 inflation values match **core** PCE within 0.0001 percentage point; the assignment requires headline PCE, so the main analysis recomputes headline YoY inflation from PCEPI. The spreadsheet's Q3 GDP value is excluded because the advance estimate is scheduled after the cutoff. October sentiment 46.3 is the official October 9 preliminary estimate and is kept separate from completed-final evaluation.

The economic panel starts in January 2010. BLS U-3, BEA PCEPI, real GDP and real disposable personal income are acquired using actual historical ALFRED snapshots for each first-of-month prediction origin, plus a cutoff snapshot. Growth rates are computed entirely within the same vintage. GDP remains a released quarterly predictor; it is not interpolated into synthetic monthly GDP. Historical within-day release times are unresolved, so an origin means the end of that calendar day. Official Michigan headline, Current Conditions and Expectations are separate outcomes. Their historical tables are latest-final targets, rather than archived survey-target vintages; revision leakage in those targets cannot be ruled out.

M1 uses U-3, headline PCE YoY and quarterly real GDP growth at an annualized rate. M2 adds previous-month contextual media tone. M3 additionally includes real disposable income YoY and cumulative 36-month PCE price growth. The comparison also refits controls-only, AR1, autoregressive macro and persistence benchmarks on common dates. Expanding-origin forecasts, rolling-window and seasonal checks, alternate GDP growth, survey-mode ramp, media lags/source/dictionary/framing sensitivities, coefficient stability, interval coverage and a future-tone diagnostic are retained. The future-tone placebo is explicitly excluded from prediction. HAC inference and multiple-test adjustments do not turn these associations into causal effects.

The survey-mode ramp is known collection design, not a causal estimate of the mode effect. Michigan's 2026 methodological reports also show that low sentiment persists in consistent-mode comparisons. Party and demographic descriptions are published context; individual affiliation, exposure and beliefs are unavailable.

## Media and annotation

Google News RSS retrieves the same broad economic query for AP, Reuters, NPR, Gothamist, Texas Tribune and Colorado Sun. Hacker News Algolia supplies user-posted story titles. A fixed hash samples at most 12 titles per outlet-month. Coverage runs January 2020 through October 12, 2026; October is partial and excluded from outcome evaluation. Titles average within outlet, outlets within group, and groups into the monthly measure. Source counts, caps, geographic uncertainty, exclusions and coverage are retained.

This selected title panel measures content supply, not exposure. Ranked RSS caps, historical edits, missing index snapshots and HN's selected audience prevent a deployable historical real-time backtest. Conservative news availability uses the following New York midnight; social creation times do not establish original unedited wording. Content published after a forecast origin cannot enter that origin's signal. Objective relevance refinements and the original annotation-pool preservation are disclosed in [the protocol amendments](docs/MEDIA_PROTOCOL_AMENDMENTS.md).

The pinned CardiffNLP RoBERTa revision is `3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7`. Assets are hash-verified, no remote code runs, and it is not fine-tuned on project outcomes. VADER is the conventional comparison. The contextual model dates from 2022; measurements on earlier text therefore use a later representation. Literal frame/salience/attribution rules are provisional. Numeric claims are screened for verification, and a limited official-reference audit is distinct from corpus-wide factual validation. Political-name swaps and source-prefix tests diagnose sensitivity without proving bias. The codebook and model specifications are in [MEDIA_CODEBOOK.md](docs/MEDIA_CODEBOOK.md).

No generative prompt produces the primary empirical score. The separate AI annotation instructions and method are disclosed in [AI_USE.md](AI_USE.md); detailed item-level labels remain local. Human validation runs on separately completed forms and never treats AI labels as human.

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

# Recompute actual observations, test methods, build and execute deliverables.
& $projectPython scripts/03_analyze.py
& $projectPython -m pytest tests -q
& $projectPython scripts/04_build_deliverables.py
& $projectPython scripts/05_execute_notebook.py
xelatex -interaction=nonstopmode -halt-on-error report.tex
xelatex -interaction=nonstopmode -halt-on-error report.tex
Copy-Item -LiteralPath report.pdf -Destination Panagiotis_Housos_Final_Project.pdf
& $projectPython scripts/06_freeze_validate.py
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

Open local `dashboard.html` for interactive date zooming, series toggles and hover values. It shows economic forecasts and uncertainty, gaps, media measures, source coverage, model errors and release events. It clearly labels unvalidated measures, incomplete October and unavailable factual accuracy. The generator is [src/dashboard.py](src/dashboard.py). No external hosting, credentials or paid services are needed.

Future updates must preserve previous vintages, verify official calendars, use only information published by each origin, and rebuild every artifact. October 23 Michigan final and October 29 GDP/PCE releases are after this cutoff. Election proximity is context, not an identified treatment. [The causal design](docs/causal_design.md) details a prospective truthful-framing experiment, falsification and national transportability requirements; no participants were recruited.

This submission intentionally freezes the October 13 snapshot. Advancing the monitoring period requires changing `CUTOFF` in `src/economics.py`, the origin range and cutoff-vintage calls in `scripts/01_collect_economics.py`, the monitoring target/preliminary-source record in `scripts/03_analyze.py`, the media acquisition `--end`, and cutoff/period descriptions in the dashboard and shared narrative. Verify and replace the preliminary record with the correctly dated official release; never carry October's 46.3 into a different month. Archive mutable Michigan/source-response caches before acquisition so the prior snapshot remains available. Then rerun the documented pipeline, validation and snapshot. Merely rerunning the frozen commands does not advance the study date.

The original AI review packet has 300 titles, of which 277 survive final relevance screening. The separate final human packet retains those 277 and supplements 23 eligible titles, yielding 300 final-corpus items in independently shuffled blank forms. The original AI labels and scores remain unchanged. Human and AI evaluations therefore have explicitly different eligible pools.

## Submission policy

Git includes source, meaningful tests, dependencies, the executed notebook, aggregate snapshot and documentation. **No datasets are committed**: raw responses, prices/indices, item text, annotations, derived tables, model weights, figures, caches and generated deliverables remain local/ignored. The PDF, PowerPoint and dashboard are supplied separately. No institutional submission, external messaging or financial trade was performed. See [AI_USE.md](AI_USE.md) and [primary sources](docs/sources.md).

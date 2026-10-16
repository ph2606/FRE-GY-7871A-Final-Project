# Submission snapshot

Information cutoff: **October 13, 2026**, America/New_York. Election day is outside this snapshot.
Raw/derived datasets, detailed annotations and model weights remain local and are excluded from Git.
A fresh download reproduces the method, but mutable search feeds, original wording, deletions and revisions can change results.

- Local file inventory: 4,259 files, 739,379,188 bytes.
- Canonical inventory SHA-256: `14a272f35e99b574deac75ddb89bc9f9b19338b5a2e5541abd1db09c122787e0`.
- Full itemized inventory is local at `outputs/snapshot_manifest.json`.
- Media: 3,787 titles, 82 months, 81 complete.
- Common media assessment: 44 months.
- Human-specific annotation requirement: **not satisfied**; AI diagnostics are separately identified.
- Provider supplement: 6 providers and 6 identical releases; collected retrospectively for the October 15 revision.

| Artifact / key input | SHA-256 |
| --- | --- |
| `data/processed/monthly_dataset.csv` | `8cfeac44c5132ab25883598bf3d4a0ad84cd10f6b7f5af43b8d16e55127f9b6a` |
| `data/processed/media_corpus.csv` | `89f4f8ca9fedf92c5f68ce810fda4b866eb4aa3de613bd583c46a56b1baf909f` |
| `data/processed/media_scores.csv` | `c8ea6ce87cf91290c688b30854cdb37ddaa9dbf62f275494593fedb15626d2ab` |
| `data/processed/media_monthly.csv` | `9643fa2ad6052d7f66020737aa2d2fd65f22362d1969f1fec623549cb5fc91fa` |
| `outputs/tables/forecasts.csv` | `541c6a4dfc5654817969270b47326efe5bf6f75d81377aee2346b8f266d4548b` |
| `outputs/tables/model_metrics.csv` | `06fa2435db040de0c68ef943a9fc285532153b922bba28a0fdb749369a2201ed` |
| `outputs/tables/predictive_loss_tests.csv` | `a582f83adf47cc3bc3fff06e6cc40ddecedc4e437a29af0514b5b8159593b31b` |
| `docs/MEDIA_CODEBOOK.md` | `130688ff3da3bb23f52c7e6681bd4daf6dbc9e2dfb7348dccc0dadab452b6e29` |
| `outputs/tables/provider_bias.csv` | `06e999b8b87368f37891f4a25c347bf63ccd3e00278a513dfcc68cb3d3efeeb9` |
| `outputs/tables/provider_bias_summary.json` | `b0131239a41d3bb7e48a14c520fa0ad4fc84f6dba74135f20caa54383d28b28c` |
| `Provider_Bias_Comparison.png` | `635048705b19fe72b3a86e9f87107054500539ca91633715b5d6b27b9fea3262` |
| `Provider_Bias_Comparison.pdf` | `f898b5d5cb451b8b27cbd06242d833426bfc1633b9f3bb9a0a69ac590ffd4bf4` |
| `Panagiotis_Housos_Final_Project.pdf` | `60e36ae3ff934acd6b214793d4d46f350638264115652829cecfc9e28f29ce4a` |
| `Panagiotis_Housos_Final_Project.pptx` | `7b0048b1450a24d4c4411c6564d2e63c2c1056ea034368835c6d7c9ee0a5693e` |
| `final_project.ipynb` | `aede973ca9a4617c8845cee3b5d3758c82462925d9ba1712490526e1c700174e` |
| `dashboard.html` | `9afdd5b31e2dd566fd99545d98b596e021285304a582d363c29c3e93fe59f8b2` |

Observed interpreter: Python 3.12.5 on Windows; exact package closure in requirements-lock.txt.
The latest Michigan historical targets are not historical survey vintages. Macro predictors use actual ALFRED snapshots; media tests remain retrospective pseudo-out-of-sample.
Detailed AI annotations and claim checks are development diagnostics, not validated human ground truth.

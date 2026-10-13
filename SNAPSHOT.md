# Submission snapshot

Information cutoff: **October 13, 2026**, America/New_York. Election day is outside this snapshot.
Raw/derived datasets, detailed annotations and model weights remain local and are excluded from Git.
A fresh download reproduces the method, but mutable search feeds, original wording, deletions and revisions can change results.

- Local file inventory: 3,712 files, 681,741,754 bytes.
- Canonical inventory SHA-256: `5437cd58971bd60133f0e4feec3f003872a135d1cebb89d2c63c44c90bb4cbe7`.
- Full itemized inventory is local at `outputs/snapshot_manifest.json`.
- Media: 3,787 titles, 82 months, 81 complete.
- Common media assessment: 44 months.
- Human-specific annotation requirement: **not satisfied**; AI diagnostics are separately identified.

| Artifact / key input | SHA-256 |
| --- | --- |
| `data/processed/monthly_dataset.csv` | `fce41bcbcc9a1b8b65695272d22da403bd8650d6aa773d876a97620b572df2ff` |
| `data/processed/media_corpus.csv` | `89f4f8ca9fedf92c5f68ce810fda4b866eb4aa3de613bd583c46a56b1baf909f` |
| `data/processed/media_scores.csv` | `c8ea6ce87cf91290c688b30854cdb37ddaa9dbf62f275494593fedb15626d2ab` |
| `data/processed/media_monthly.csv` | `9643fa2ad6052d7f66020737aa2d2fd65f22362d1969f1fec623549cb5fc91fa` |
| `outputs/tables/forecasts.csv` | `541c6a4dfc5654817969270b47326efe5bf6f75d81377aee2346b8f266d4548b` |
| `outputs/tables/model_metrics.csv` | `06fa2435db040de0c68ef943a9fc285532153b922bba28a0fdb749369a2201ed` |
| `outputs/tables/predictive_loss_tests.csv` | `a582f83adf47cc3bc3fff06e6cc40ddecedc4e437a29af0514b5b8159593b31b` |
| `docs/MEDIA_CODEBOOK.md` | `130688ff3da3bb23f52c7e6681bd4daf6dbc9e2dfb7348dccc0dadab452b6e29` |
| `Panagiotis_Housos_Final_Project.pdf` | `466e0c1f89b127a312899346eaf42651601a60280ef6b6249d91a2790646d1af` |
| `Panagiotis_Housos_Final_Project.pptx` | `3702e6003806c794afb46d051e70e7217ce64f84b5efdd2388bd6655e64480b1` |
| `final_project.ipynb` | `7036994884564407c1dc33d242824a6bdd1b9e267d002423d22037a4a00e2b63` |
| `dashboard.html` | `3cab0448fb631e2337e2a1de686f0170cdf262fa5d4fe6f423490bec5faa98dd` |

Observed interpreter: Python 3.12.5 on Windows; exact package closure in requirements-lock.txt.
The latest Michigan historical targets are not historical survey vintages. Macro predictors use actual ALFRED snapshots; media tests remain retrospective pseudo-out-of-sample.
Detailed AI annotations and claim checks are development diagnostics, not validated human ground truth.

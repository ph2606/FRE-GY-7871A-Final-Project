# Submission snapshot

Information cutoff: **October 13, 2026**, America/New_York. Election day is outside this snapshot.
Raw/derived datasets, detailed annotations and model weights remain local and are excluded from Git.
A fresh download reproduces the method, but mutable search feeds, original wording, deletions and revisions can change results.

- Local file inventory: 4,294 files, 764,567,161 bytes.
- Canonical inventory SHA-256: `df5c970f693846b61e28cf3b3681523630a5ea2df9fe93e0240c4e4582472157`.
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
| `Provider_Bias_Comparison.png` | `97e92f7e8e98c7dacf236e32e9de504765ec5849900e1a39be80b2433dba6966` |
| `Provider_Bias_Comparison.pdf` | `970b52600f5e8a52a04d1092ef6b820ecdca081b63cdffd08de843d170f3b41c` |
| `Panagiotis_Housos_Final_Project.pdf` | `ece2f6b3ab51189baeaccd0e7ef9b226a262559206d7efdc8f2bfab6e4ccb678` |
| `Panagiotis_Housos_Final_Project.pptx` | `25c807b1e97c18beae6137d587f6c7804df971f34fa2971e5ec52e6545ec1f9b` |
| `final_project.ipynb` | `1032f8851639fc59deb4ad32dded4574fe1e92a594f38d52c2c3f22b5bf3e18e` |
| `dashboard.html` | `0522537002f0e2ce9f6c3400e5b5b9f3c58d60636b8fbddd7844b9db340359ff` |

Observed interpreter: Python 3.12.5 on Windows; exact package closure in requirements-lock.txt.
The latest Michigan historical targets are not historical survey vintages. Macro predictors use actual ALFRED snapshots; media tests remain retrospective pseudo-out-of-sample.
Detailed AI annotations and claim checks are development diagnostics, not validated human ground truth.

# External human-reference check: Financial PhraseBank

This protocol is written before either classifier scores this benchmark. It is a separate October 18, 2026 validation extension, after the October 13 economic snapshot. It is not newly collected human work, an untouched target-domain test, or a substitute for the assignment's two independent people labeling 300 project headlines.

## Source and permission

Use the authors' Financial PhraseBank v1.0 distribution, transported through the pinned Hugging Face mirror at revision `170cd2fc2ae7f3dcb51653b4f008c39c906cdac9`. ZIP SHA-256 must equal `0e1a06c4900fdae46091d031068601e3773ba067c7cecb5b0da1dcba5ce989a6`. Parse only `FinancialPhraseBank-v1.0/Sentences_AllAgree.txt`, encoded ISO-8859-1; do not run dataset-repository code.

The bundled authors' README identifies investor-perspective sentence labels, with five to eight judgments per sentence. The `AllAgree` subset retains unanimous positive/neutral/negative judgments. These are company-news sentences assembled by the Aalto research team, not the project's U.S. economic headlines or measured consumer beliefs. Unanimous items can be easier than ambiguous coverage.

The bundled `License.txt` specifies **Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported**. This academic comparison attributes Malo, Sinha, Takala, Korhonen and Wallenius. Original files, text, reference labels and item predictions remain local and are excluded from Git/submission source under the no-data policy. Retain the source README and license locally. Do not imply that the license permits an unrestricted commercial dataset release.

Sources: [authors' paper, Good Debt or Bad Debt](https://arxiv.org/abs/1307.5336v2), [pinned distribution](https://huggingface.co/datasets/takala/financial_phrasebank/blob/170cd2fc2ae7f3dcb51653b4f008c39c906cdac9/data/FinancialPhraseBank-v1.0.zip), [pinned dataset card](https://huggingface.co/datasets/takala/financial_phrasebank/blob/170cd2fc2ae7f3dcb51653b4f008c39c906cdac9/README.md), [license](https://creativecommons.org/licenses/by-nc-sa/3.0/).

## Freeze before predictions

1. Read all unanimous rows; preserve each original sentence and line number. For duplicate detection only, normalize Unicode to NFC, collapse whitespace and case-fold. Conflicting labels on the same normalized text cause failure. Retain the first occurrence of repeated same-label text.
2. Separately within each human class, rank items by SHA-256 of `phrasebank-external-v1|class|normalized_text`. Take the first **100 per class**, 300 total, then order by item ID. There is no prediction-based selection or resampling. Class labels select strata but are never part of classifier inputs.
3. `python -m src.external_validation prepare` records protocol/script/sample hashes, selected IDs, preparation time, dataset hashes, pinned model revision, VADER package version and lexicon fingerprints. `score` refuses changed inputs or a missing freeze. The first freeze must precede prediction creation. Do not retune after seeing results.

## Fixed comparisons

Use the project's unchanged Cardiff classifier `cardiffnlp/twitter-roberta-base-sentiment-latest`, revision `3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7`, with the same preprocessing, label order, long-text splitting and class argmax as the project. Use the installed locked VADER dictionary with compound thresholds below -0.05 / above +0.05; endpoints are neutral. Do not train, select models, calibrate probabilities or change thresholds on these examples.

Report both models: agreement/accuracy against the external consensus, macro-F1 (equal class weight), each class's precision/recall/F1 and support, and confusion counts. Accuracy's Wilson 95% range is a descriptive binomial range conditional on the selected cases, not a correction for unknown clustering or domain shift. A balanced 100/100/100 sample does not estimate accuracy under the original dataset's or project's class prevalence. No outlet-level performance is claimed because these records do not provide project outlet strata.

## Limits that accompany every result

- This external human-annotated benchmark does not satisfy the two-human requirement on the target project corpus; that status remains false.
- Labels describe potential company/investor implications, rather than economic headline wording, factual accuracy, ideology, framing or effects on Michigan sentiment.
- The dataset was public before these models. Training/pretraining overlap is unknown; no claim is made that the examples are unseen training data.
- The unanimous and balanced subset changes difficulty and class mix. Results cannot be transported directly to noisy headlines, sources, social posts or the provider bars.
- This check can reveal a classifier limitation. It cannot establish that the classifier or the custom negativity measure is valid for the main economic question.

Reproduce with `python -m src.external_validation prepare`, then `python -m src.external_validation score`. Aggregate outputs are local at `outputs/tables/external_validation_*`; the notebook/report may display clearly identified aggregates. Detailed examples are not committed.

"""Frozen external human-reference benchmark; never target human validation."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import unicodedata
import zipfile

import numpy as np
import pandas as pd
import requests
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from statsmodels.stats.proportion import proportion_confint
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/external_phrasebank'
PROCESSED = ROOT / 'data/processed'
OUT = ROOT / 'outputs/tables'
PROTOCOL = ROOT / 'docs/EXTERNAL_VALIDATION_PROTOCOL.md'
REVISION = '170cd2fc2ae7f3dcb51653b4f008c39c906cdac9'
ARCHIVE_SHA = '0e1a06c4900fdae46091d031068601e3773ba067c7cecb5b0da1dcba5ce989a6'
ARCHIVE = RAW / 'FinancialPhraseBank-v1.0.zip'
URL = f'https://huggingface.co/datasets/takala/financial_phrasebank/resolve/{REVISION}/data/FinancialPhraseBank-v1.0.zip'
MEMBER = 'FinancialPhraseBank-v1.0/Sentences_AllAgree.txt'
SAMPLE = PROCESSED / 'external_phrasebank_sample.csv'
FREEZE = PROCESSED / 'external_phrasebank_freeze.json'
PREDICTIONS = PROCESSED / 'external_phrasebank_predictions.csv'
LABELS = ['negative', 'neutral', 'positive']
MODEL_ID = 'cardiffnlp/twitter-roberta-base-sentiment-latest'
MODEL_REVISION = '3216a57f2a0d9c45a2e6c20157c20c49fb4bf9c7'


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value) -> str:
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def normalized(text: str) -> str:
    return ' '.join(unicodedata.normalize('NFC', text).split()).casefold()


def parse_author_rows(content: bytes) -> pd.DataFrame:
    rows, seen = [], {}
    for line_number, line in enumerate(content.decode('iso-8859-1').splitlines(), 1):
        if not line.strip():
            continue
        text, separator, label = line.rpartition('@')
        if not separator or label.strip() not in LABELS or not text.strip():
            raise ValueError(f'Invalid author row {line_number}')
        text, label = text.strip(), label.strip()
        key = normalized(text)
        if key in seen:
            if seen[key] != label:
                raise ValueError('Conflicting reference labels on duplicate text')
            continue
        seen[key] = label
        item_id = digest(key.encode('utf-8'))
        rank = digest(f'phrasebank-external-v1|{label}|{key}'.encode('utf-8'))
        rows.append({'item_id': item_id, 'author_line': line_number, 'text': text,
                     'human_reference': label, 'selection_rank': rank})
    return pd.DataFrame(rows)


def select_sample(frame: pd.DataFrame, per_class: int = 100) -> pd.DataFrame:
    parts = []
    for label in LABELS:
        group = frame.loc[frame.human_reference.eq(label)].sort_values(['selection_rank', 'item_id'])
        if len(group) < per_class:
            raise ValueError(f'Insufficient unique {label} examples')
        parts.append(group.head(per_class))
    result = pd.concat(parts).sort_values('item_id').reset_index(drop=True)
    if result.item_id.duplicated().any():
        raise ValueError('Sample IDs must be unique')
    return result


def vader_class(compound: float) -> str:
    return 'negative' if compound < -.05 else 'positive' if compound > .05 else 'neutral'


def vader_fingerprint(analyzer) -> dict:
    return {'package_version': importlib.metadata.version('vaderSentiment'),
            'lexicon_sha256': canonical(analyzer.lexicon),
            'emoji_lexicon_sha256': canonical(analyzer.emojis),
            'thresholds': {'negative_below': -.05, 'positive_above': .05}}


def source_rows() -> pd.DataFrame:
    RAW.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        response = requests.get(URL, timeout=90)
        response.raise_for_status()
        if digest(response.content) != ARCHIVE_SHA:
            raise ValueError('Author archive differs from the pinned distribution')
        ARCHIVE.write_bytes(response.content)
        write_json(RAW / 'acquisition.json', {'url': URL, 'revision': REVISION,
                   'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                   'http_status': response.status_code, 'bytes': len(response.content),
                   'sha256': digest(response.content)})
    if digest(ARCHIVE.read_bytes()) != ARCHIVE_SHA:
        raise ValueError('Cached archive hash mismatch')
    metadata = json.loads((RAW / 'acquisition.json').read_text(encoding='utf-8'))
    if metadata['sha256'] != ARCHIVE_SHA or metadata['url'] != URL:
        raise ValueError('Acquisition metadata differs from the pinned source')
    with zipfile.ZipFile(ARCHIVE) as archive:
        license_bytes = archive.read('FinancialPhraseBank-v1.0/License.txt')
        if b'Attribution-NonCommercial-ShareAlike 3.0' not in license_bytes:
            raise ValueError('Expected author license was not found')
        (RAW / 'License.txt').write_bytes(license_bytes)
        (RAW / 'README.txt').write_bytes(archive.read('FinancialPhraseBank-v1.0/README.txt'))
        return parse_author_rows(archive.read(MEMBER))


def expected_freeze(sample, analyzer) -> dict:
    return {'protocol_sha256': digest(PROTOCOL.read_bytes()),
            'script_sha256': digest(Path(__file__).read_bytes()),
            'archive_sha256': ARCHIVE_SHA, 'dataset_revision': REVISION,
            'sample_records_sha256': canonical(sample.to_dict('records')),
            'sample_ids': sample.item_id.tolist(), 'n': len(sample),
            'class_counts': sample.human_reference.value_counts().to_dict(),
            'model_id': MODEL_ID, 'model_revision': MODEL_REVISION,
            'vader': vader_fingerprint(analyzer)}


def prepare():
    sample = select_sample(source_rows())
    frozen = expected_freeze(sample, SentimentIntensityAnalyzer())
    if FREEZE.exists():
        previous = json.loads(FREEZE.read_text(encoding='utf-8'))
        if previous['inputs'] != frozen:
            raise ValueError('Frozen inputs changed; do not silently replace this benchmark')
        if digest(SAMPLE.read_bytes()) != previous['sample_csv_sha256']:
            raise ValueError('Frozen sample CSV changed')
        print('Existing 300-item pre-scoring freeze verified.')
        return
    if PREDICTIONS.exists():
        raise ValueError('Predictions exist without a pre-scoring freeze')
    PROCESSED.mkdir(parents=True, exist_ok=True)
    sample.to_csv(SAMPLE, index=False, lineterminator='\n')
    write_json(FREEZE, {'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
                       'inputs': frozen, 'sample_csv_sha256': digest(SAMPLE.read_bytes()),
                       'predictions_existed_at_freeze': False})
    print('Frozen 300 external examples: 100 in each human-reference class; no predictions created.')


def metrics(reference, predicted) -> dict:
    precision, recall, f1, support = precision_recall_fscore_support(
        reference, predicted, labels=LABELS, zero_division=0)
    matched = sum(a == b for a, b in zip(reference, predicted))
    low, high = proportion_confint(matched, len(reference), method='wilson')
    return {'n': len(reference), 'external_human_reference_accuracy': float(accuracy_score(reference, predicted)),
            'accuracy_wilson_lower': float(low), 'accuracy_wilson_upper': float(high),
            'macro_f1': float(f1_score(reference, predicted, labels=LABELS, average='macro', zero_division=0)),
            'per_class': {label: {'precision': float(precision[i]), 'recall': float(recall[i]),
                                 'f1': float(f1[i]), 'support': int(support[i])}
                          for i, label in enumerate(LABELS)},
            'labels': LABELS, 'confusion_rows_human_reference': confusion_matrix(reference, predicted, labels=LABELS).tolist()}


def score():
    if not FREEZE.exists():
        raise ValueError('Run prepare before scoring: a pre-scoring freeze is required')
    sample = pd.read_csv(SAMPLE, keep_default_na=False)
    freeze = json.loads(FREEZE.read_text(encoding='utf-8'))
    analyzer = SentimentIntensityAnalyzer()
    if (freeze['inputs'] != expected_freeze(sample, analyzer)
            or freeze['sample_csv_sha256'] != digest(SAMPLE.read_bytes())):
        raise ValueError('Protocol, script, sample or model specification changed after freezing')
    from src.media import MODEL_ID as active_model, REVISION as active_revision, copy_model, contextual
    if (active_model, active_revision) != (MODEL_ID, MODEL_REVISION):
        raise ValueError('The project model no longer matches the frozen benchmark')
    assets = copy_model()
    if PREDICTIONS.exists():
        frame = pd.read_csv(PREDICTIONS, keep_default_na=False)
        previous_path = OUT / 'external_validation_summary.json'
        previous = json.loads(previous_path.read_text(encoding='utf-8'))
        if (digest(PREDICTIONS.read_bytes()) != previous['predictions_sha256']
                or previous['freeze_sha256'] != digest(FREEZE.read_bytes())):
            raise ValueError('Cached predictions changed or belong to a different freeze')
        if not frame[sample.columns].equals(sample):
            raise ValueError('Cached prediction rows differ from the frozen sample')
    else:
        probabilities = contextual(sample.text.tolist())
        if probabilities.shape != (len(sample), 3) or not np.isfinite(probabilities).all():
            raise ValueError('Invalid contextual probabilities')
        frame = sample.copy()
        frame['contextual_class'] = np.array(LABELS)[probabilities.argmax(axis=1)]
        frame['vader_compound'] = [analyzer.polarity_scores(text)['compound'] for text in sample.text]
        frame['dictionary_class'] = frame.vader_compound.map(vader_class)
        for i, label in enumerate(LABELS):
            frame['contextual_'+label] = probabilities[:, i]
        frame.to_csv(PREDICTIONS, index=False, lineterminator='\n')
    comparisons = {name: metrics(frame.human_reference.tolist(), frame[column].tolist())
                   for name, column in [('contextual', 'contextual_class'), ('dictionary', 'dictionary_class')]}
    summary = {'status': 'external_human_reference_only',
               'dataset': 'Financial PhraseBank v1.0, unanimous subset', 'n': len(frame),
               'sample_class_counts': frame.human_reference.value_counts().to_dict(),
               'source_unique_class_counts': source_rows().human_reference.value_counts().to_dict(),
               'prepared_at_utc': freeze['prepared_at_utc'], 'scored_at_utc': datetime.now(timezone.utc).isoformat(),
               'freeze_sha256': digest(FREEZE.read_bytes()), 'protocol_sha256': digest(PROTOCOL.read_bytes()),
               'predictions_sha256': digest(PREDICTIONS.read_bytes()), 'model_assets': assets,
               'comparisons': comparisons, 'human_specific_requirement_satisfied': False,
               'source_url': URL, 'license': 'CC-BY-NC-SA-3.0',
               'citation': 'Malo, Sinha, Takala, Korhonen and Wallenius, Good Debt or Bad Debt (2014; arXiv:1307.5336v2).',
               'limitations': ['External company/investor-perspective sentences, not target economic headlines.',
                              'Unanimous balanced subset changes difficulty and prevalence.',
                              'Training/pretraining overlap is unknown; not claimed to be unseen model data.',
                              'Does not validate framing, factual accuracy, ideology, provider bars or consumer effects.',
                              'Does not replace two independent human annotators on the project corpus.',
                              'Wilson ranges are descriptive and do not account for unknown sentence/source clustering.']}
    OUT.mkdir(parents=True, exist_ok=True)
    model_rows, class_rows, confusion_rows = [], [], []
    for name, result in comparisons.items():
        model_rows.append({'model': name, **{k: result[k] for k in ['n', 'external_human_reference_accuracy',
                           'accuracy_wilson_lower', 'accuracy_wilson_upper', 'macro_f1']}})
        class_rows += [{'model': name, 'human_class': label, **values} for label, values in result['per_class'].items()]
        confusion_rows += [{'model': name, 'human_class': human, 'predicted_class': predicted,
                            'n': result['confusion_rows_human_reference'][i][j]}
                           for i, human in enumerate(LABELS) for j, predicted in enumerate(LABELS)]
    for suffix, rows in [('models', model_rows), ('classes', class_rows), ('confusion', confusion_rows)]:
        pd.DataFrame(rows).to_csv(OUT / f'external_validation_{suffix}.csv', index=False)
    write_json(OUT / 'external_validation_summary.json', summary)
    print(pd.DataFrame(model_rows).to_string(index=False))
    print('External human reference only; the target two-human requirement remains unsatisfied.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'score'])
    action = parser.parse_args().action
    prepare() if action == 'prepare' else score()


if __name__ == '__main__':
    main()

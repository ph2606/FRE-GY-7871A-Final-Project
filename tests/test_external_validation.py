import pandas as pd
import pytest

from src.external_validation import LABELS, metrics, parse_author_rows, select_sample, vader_class


def test_selection_is_stratified_order_invariant_and_deduplicated():
    payload = '\n'.join(f'Company {label} sentence {i}@{label}' for label in LABELS for i in range(110))
    frame = parse_author_rows((payload+'\nCompany negative sentence 0@negative').encode('iso-8859-1'))
    selected = select_sample(frame)
    assert len(frame) == 330 and len(selected) == selected.item_id.nunique() == 300
    assert selected.human_reference.value_counts().to_dict() == dict.fromkeys(LABELS, 100)
    pd.testing.assert_frame_equal(selected, select_sample(frame.sample(frac=1, random_state=18)))


def test_conflicting_or_invalid_author_labels_fail():
    with pytest.raises(ValueError, match='Conflicting'):
        parse_author_rows(b'Profit rose@positive\n  PROFIT rose  @negative')
    with pytest.raises(ValueError, match='Invalid'):
        parse_author_rows(b'Profit rose@mixed')


def test_fixed_dictionary_boundaries_are_neutral():
    assert [vader_class(x) for x in [-.051, -.05, 0, .05, .051]] == [
        'negative', 'neutral', 'neutral', 'neutral', 'positive']


def test_class_scores_and_confusion_use_human_reference_rows():
    result = metrics(['negative', 'neutral', 'positive'], ['negative', 'neutral', 'negative'])
    assert result['n'] == 3
    assert result['external_human_reference_accuracy'] == pytest.approx(2/3)
    assert result['macro_f1'] == pytest.approx((2/3+1+0)/3)
    assert result['confusion_rows_human_reference'] == [[1, 0, 0], [0, 1, 0], [1, 0, 0]]
    assert result['per_class']['positive']['support'] == 1
    assert result['accuracy_wilson_lower'] < 2/3 < result['accuracy_wilson_upper']

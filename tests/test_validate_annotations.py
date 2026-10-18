"""Reference-cohort integrity matters more than a single concordance average."""
import json
import pandas as pd
import pytest
from src import validate_annotations as validation


def diagnostic_files(tmp_path,monkeypatch):
    monkeypatch.setattr(validation,'ROOT',tmp_path)
    annotations=tmp_path/'data/annotations'
    processed=tmp_path/'data/processed'
    annotations.mkdir(parents=True)
    processed.mkdir(parents=True)
    scores=pd.DataFrame({'id':list('abcde'),'source':['NPR','Reuters','NPR','Reuters','Colorado Sun'],
                         'contextual_class':['negative','neutral','positive','negative','neutral'],
                         'vader_class':['neutral','positive','neutral','neutral','negative']})
    scores.to_csv(annotations/'frozen_media_scores.csv',index=False)
    # b is removed from the final corpus, while its original model score remains.
    scores.loc[scores.id.ne('b')].to_csv(processed/'media_scores.csv',index=False)
    a=pd.DataFrame({'id':list('abcde'),'tone':['negative','neutral','positive','mixed','cannot_determine'],
                    'annotator_type':'AI diagnostic'})
    b=pd.DataFrame({'id':list('abcde'),'tone':['negative','positive','positive','neutral','cannot determine'],
                    'annotator_type':'AI diagnostic'})
    a.to_csv(annotations/'A.csv',index=False)
    b.to_csv(annotations/'B.csv',index=False)
    return annotations/'A.csv',annotations/'B.csv'


def test_final_eligible_source_tables_preserve_original_and_uncertainty_denominators(tmp_path,monkeypatch):
    a,b=diagnostic_files(tmp_path,monkeypatch)
    result=validation.evaluate(a,b,label_type='ai_diagnostic')
    assert result['completed_independent_pairs']==5
    assert result['annotation_pool_final_eligible_n']==4
    assert result['annotation_pool_final_excluded_n']==1
    assert not result['human_specific_requirement_satisfied']
    original=result['model_reference_concordance']['annotator_a']['contextual']
    final=result['final_eligible_model_reference_concordance']['annotator_a']['contextual']
    assert original['n']==3 and final['n']==2
    assert set(original['by_source'])=={'NPR','Reuters'}
    assert set(final['by_source'])=={'NPR'}
    assert final['by_source']['NPR']['n']==2
    assert sum(map(sum,final['confusion_matrix_rows_reference']))==final['n']
    assert sum(x['support'] for x in final['class_concordance'].values())==final['n']
    summary=result['cohort_summary']['final_eligible_pool']
    assert summary['annotators']['annotator_a']['excluded_mixed_or_uncertain_n']==2
    assert summary['annotators']['annotator_b']['three_class_reference_n']==3
    assert summary['annotators']['annotator_a']['tone_counts']['cannot determine']==1
    saved=json.loads((tmp_path/'outputs/ai_diagnostic_validation_metrics.json').read_text())
    assert saved['final_eligible_model_reference_concordance']==result['final_eligible_model_reference_concordance']


def test_ai_marked_rows_are_never_accepted_as_human_labels(tmp_path,monkeypatch):
    a,b=diagnostic_files(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='AI-marked'):
        validation.evaluate(a,b,label_type='human')


def test_blank_human_forms_have_no_completed_validation(tmp_path,monkeypatch):
    a,b=diagnostic_files(tmp_path,monkeypatch)
    for path in [a,b]:
        pd.DataFrame({'id':list('abcde'),'tone':''}).to_csv(path,index=False)
    result=validation.evaluate(a,b,label_type='human')
    assert result['status']=='pending'
    assert result['completed_independent_pairs']==0
    assert not result['human_specific_requirement_satisfied']
    assert 'model_reference_concordance' not in result

"""Validate independent document labels without inventing human observations.

Blank sheets produce an explicit pending status. Use --label-type ai_diagnostic
for AI-created labels; their concordance is never named human accuracy.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score,cohen_kappa_score,confusion_matrix,f1_score,precision_recall_fscore_support

ROOT=Path(__file__).resolve().parents[1]
TONES=['negative','neutral','positive','mixed','cannot determine']

def read(path):
    frame=pd.read_csv(path,keep_default_na=False)
    if 'item_id' in frame:frame=frame.rename(columns={'item_id':'id'})
    if not {'id','tone'}.issubset(frame):raise ValueError(f'{path}: id and tone required')
    if frame.id.duplicated().any():raise ValueError(f'{path}: duplicate item IDs')
    # Accept mechanically equivalent exported labels, preserving original files unchanged.
    frame.tone=frame.tone.str.strip().str.lower().str.replace('_',' ',regex=False).str.replace(r'\s+',' ',regex=True)
    bad=set(frame.tone)-set(TONES)-{''}
    if bad:raise ValueError(f'{path}: invalid tone labels {bad}')
    return frame

def compare(reference,prediction):
    labels=['negative','neutral','positive']
    p,r,f,n=precision_recall_fscore_support(reference,prediction,labels=labels,zero_division=0)
    return {'n':len(reference),'agreement':float(accuracy_score(reference,prediction)),
      'macro_f1_reference_concordance':float(f1_score(reference,prediction,labels=labels,average='macro',zero_division=0)),
      'class_concordance':{lab:{'precision':float(p[i]),'recall':float(r[i]),'f1':float(f[i]),'support':int(n[i])} for i,lab in enumerate(labels)},
      'confusion_matrix_rows_reference':confusion_matrix(reference,prediction,labels=labels).tolist(),'labels':labels}

def evaluate(a_path,b_path,adjudicated=None,label_type='human',out=None):
    a=read(a_path);b=read(b_path)
    if label_type=='human':
        for sheet in [a,b]:
            if 'annotator_type' in sheet and sheet.annotator_type.str.contains('AI',case=False,regex=False).any():
                raise ValueError('AI-marked annotations cannot be evaluated as human labels')
    joined=a.merge(b,on='id',suffixes=('_a','_b'),validate='one_to_one')
    valid=joined.tone_a.isin(TONES)&joined.tone_b.isin(TONES)
    completed=joined[valid]
    prefix='human' if label_type=='human' else 'ai_diagnostic'
    output=Path(out) if out else ROOT/f'outputs/{prefix}_validation_metrics.json'
    result={'label_type':label_type,'completed_independent_pairs':len(completed),'matched_sheet_rows':len(joined),
      'missing_a_ids':sorted(set(b.id)-set(a.id)),'missing_b_ids':sorted(set(a.id)-set(b.id)),
      'status':'complete' if len(completed)>=300 else 'pending',
      'human_specific_requirement_satisfied':label_type=='human' and len(completed)>=300,
      'interpretation':'AI annotation concordance is a diagnostic and does not substitute for two independent human annotators.' if label_type!='human' else 'Independent annotator agreement; adjudication required for a reference-label performance claim.'}
    if len(completed):
        result['tone_agreement']=float(completed.tone_a.eq(completed.tone_b).mean())
        result['tone_cohens_kappa']=float(cohen_kappa_score(completed.tone_a,completed.tone_b,labels=TONES))
        dimensions={}
        for c in a.columns:
            if c in ['id','text','tone','notes','evidence','confidence'] or c not in b:continue
            aa=completed.get(c+'_a');bb=completed.get(c+'_b')
            if aa is None or bb is None:continue
            mask=aa.astype(str).ne('')&bb.astype(str).ne('')
            if mask.any():dimensions[c]={'n':int(mask.sum()),'agreement':float(aa[mask].eq(bb[mask]).mean())}
        result['dimension_agreement']=dimensions
        snapshot=ROOT/'data/annotations/frozen_media_scores.csv'
        use_frozen=label_type!='human' and snapshot.exists()
        scores=pd.read_csv(snapshot if use_frozen else ROOT/'data/processed/media_scores.csv')
        final_ids=set(pd.read_csv(ROOT/'data/processed/media_scores.csv').id)
        result['original_annotation_pool_model_reference']=str(snapshot.relative_to(ROOT)) if use_frozen else 'data/processed/media_scores.csv'
        result['annotation_pool_final_eligible_n']=int(completed.id.isin(final_ids).sum())
        result['annotation_pool_final_excluded_n']=int((~completed.id.isin(final_ids)).sum())
        if label_type=='human' and result['annotation_pool_final_eligible_n']<300:
            result['human_specific_requirement_satisfied']=False
            result['status']='pending'
        result['development_screen_warning']='Relevance screening was refined after annotation-pool inspection. Original300 pool and initial model scores are preserved; this is development diagnostic evidence, not an untouched validation holdout.'
        merged=completed.merge(scores[['id','source','contextual_class','vader_class']],on='id',validate='one_to_one')
        diagnostics={}
        for annotator in ['a','b']:
            classified=merged[merged['tone_'+annotator].isin(['negative','neutral','positive'])]
            diagnostics['annotator_'+annotator]={}
            for model,col in [('contextual','contextual_class'),('dictionary','vader_class')]:
                entry=compare(classified['tone_'+annotator],classified[col])
                entry['by_source']={source:compare(g['tone_'+annotator],g[col]) for source,g in classified.groupby('source')}
                diagnostics['annotator_'+annotator][model]=entry
        result['model_reference_concordance']=diagnostics
        final_merged=merged[merged.id.isin(final_ids)]
        # Preserve both cohorts: inspecting relevance after annotation must not
        # silently turn the original 300-item diagnostic into a final holdout.
        cohort_summary={}
        for cohort,subset in [('original_review_pool',merged),('final_eligible_pool',final_merged)]:
            entry={'n':len(subset),
                   'tone_agreement':float(subset.tone_a.eq(subset.tone_b).mean()) if len(subset) else None,
                   'annotators':{}}
            for annotator in ['a','b']:
                tones=subset['tone_'+annotator]
                comparable=int(tones.isin(['negative','neutral','positive']).sum())
                entry['annotators']['annotator_'+annotator]={
                    'three_class_reference_n':comparable,
                    'excluded_mixed_or_uncertain_n':len(subset)-comparable,
                    'tone_counts':{tone:int(tones.eq(tone).sum()) for tone in TONES}}
            cohort_summary[cohort]=entry
        result['cohort_summary']=cohort_summary
        result['final_eligible_model_reference_concordance']={}
        for annotator in ['a','b']:
            classified=final_merged[final_merged['tone_'+annotator].isin(['negative','neutral','positive'])]
            final_diagnostics={}
            for model,col in [('contextual','contextual_class'),('dictionary','vader_class')]:
                entry=compare(classified['tone_'+annotator],classified[col])
                entry['by_source']={source:compare(g['tone_'+annotator],g[col])
                                    for source,g in classified.groupby('source')}
                final_diagnostics[model]=entry
            result['final_eligible_model_reference_concordance']['annotator_'+annotator]=final_diagnostics
        if adjudicated:
            adj=read(adjudicated);adj=adj[adj.tone.isin(['negative','neutral','positive'])]
            reference=adj.merge(scores[['id','source','contextual_class','vader_class']],on='id',validate='one_to_one')
            result['adjudicated_reference_n']=len(reference)
            result['adjudicated_model_performance']={model:compare(reference.tone,reference[col]) for model,col in [('contextual','contextual_class'),('dictionary','vader_class')]}
            if label_type!='human':result['adjudicated_reference_warning']='AI adjudication is not human ground truth; these are diagnostic reference-concordance metrics.'
    output.parent.mkdir(parents=True,exist_ok=True)
    # One-class annotations can make kappa undefined; JSON uses null, never NaN.
    def normalize(value):
        if isinstance(value,float) and not np.isfinite(value):return None
        if isinstance(value,dict):return {k:normalize(v) for k,v in value.items()}
        if isinstance(value,list):return [normalize(v) for v in value]
        return value
    output.write_text(json.dumps(normalize(result),indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['label_type','status','completed_independent_pairs','human_specific_requirement_satisfied']},indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--a',default=str(ROOT/'data/annotations/human_final_A_blinded.csv'))
    p.add_argument('--b',default=str(ROOT/'data/annotations/human_final_B_blinded.csv'))
    p.add_argument('--adjudicated');p.add_argument('--label-type',choices=['human','ai_diagnostic'],default='human');p.add_argument('--out')
    args=p.parse_args();evaluate(args.a,args.b,args.adjudicated,args.label_type,args.out)

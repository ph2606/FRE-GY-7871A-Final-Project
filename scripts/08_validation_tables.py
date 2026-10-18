"""Export aggregate AI diagnostic tables; no human accuracy or item text is saved.

Run after explicitly evaluating the saved A/B files as ai_diagnostic. Wilson
ranges describe agreement conditional on this inspected sample and an iid-item
working assumption. They omit dependence, reference error and sampling bias.
"""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/tables'
COHORTS=[('original_review_pool','model_reference_concordance'),
         ('final_eligible_pool','final_eligible_model_reference_concordance')]


def wilson(matches,n):
    if not n:
        return None,None
    z=1.959963984540054
    p=matches/n
    denominator=1+z*z/n
    center=(p+z*z/(2*n))/denominator
    radius=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/denominator
    return max(0.,center-radius),min(1.,center+radius)


def main():
    path=ROOT/'outputs/ai_diagnostic_validation_metrics.json'
    diagnostic=json.loads(path.read_text(encoding='utf-8'))
    if diagnostic.get('label_type')!='ai_diagnostic':
        raise ValueError('This export requires explicitly labeled AI development diagnostics')
    cohort_rows=[];model_rows=[];source_rows=[];class_rows=[];confusion_rows=[]
    for cohort,key in COHORTS:
        cohort_info=diagnostic['cohort_summary'][cohort]
        for reference,info in cohort_info['annotators'].items():
            cohort_rows.append({'cohort':cohort,'reference':reference,'paired_items':cohort_info['n'],
                                **{k:v for k,v in info.items() if k!='tone_counts'},
                                **info['tone_counts']})
        for reference,models in diagnostic[key].items():
            for model,entry in models.items():
                base={'cohort':cohort,'reference':reference,'model':model,'label_type':'ai_diagnostic'}
                matrix=np.asarray(entry['confusion_matrix_rows_reference'],dtype=int)
                matches=int(np.trace(matrix));lower,upper=wilson(matches,entry['n'])
                model_rows.append({**base,'n':entry['n'],'matching_labels':matches,
                                   'agreement':entry['agreement'],
                                   'agreement_wilson_lower_95':lower,'agreement_wilson_upper_95':upper,
                                   'macro_f1_concordance':entry['macro_f1_reference_concordance']})
                for source,sub in entry['by_source'].items():
                    matches=int(np.trace(sub['confusion_matrix_rows_reference']))
                    lower,upper=wilson(matches,sub['n'])
                    source_rows.append({**base,'source':source,'n':sub['n'],'matching_labels':matches,
                                        'agreement':sub['agreement'],
                                        'agreement_wilson_lower_95':lower,'agreement_wilson_upper_95':upper,
                                        'macro_f1_concordance':sub['macro_f1_reference_concordance']})
                for index,label in enumerate(entry['labels']):
                    values=entry['class_concordance'][label]
                    class_rows.append({**base,'reference_class':label,**values,
                                       'predicted_n':int(matrix[:,index].sum()),
                                       'correctly_matching_class_n':int(matrix[index,index])})
                    for j,predicted in enumerate(entry['labels']):
                        confusion_rows.append({**base,'reference_class':label,
                                               'model_class':predicted,'n':int(matrix[index,j])})
    OUT.mkdir(parents=True,exist_ok=True)
    frames={'validation_cohorts':cohort_rows,'validation_model_concordance':model_rows,
            'validation_source_concordance':source_rows,'validation_class_concordance':class_rows,
            'validation_confusion_matrices':confusion_rows}
    dimensions=[{'cohort':'original_review_pool','dimension':key,**value}
                for key,value in diagnostic.get('dimension_agreement',{}).items()]
    frames['validation_dimension_agreement']=dimensions
    for name,rows in frames.items():
        pd.DataFrame(rows).to_csv(OUT/(name+'.csv'),index=False)
    summary={'label_type':'ai_diagnostic','human_requirement_satisfied':False,
             'original_pool_n':diagnostic['completed_independent_pairs'],
             'final_eligible_n':diagnostic['annotation_pool_final_eligible_n'],
             'excluded_from_original_n':diagnostic['annotation_pool_final_excluded_n'],
             'original_ai_tone_agreement':diagnostic['tone_agreement'],
             'original_ai_tone_kappa':diagnostic['tone_cohens_kappa'],
             'final_ai_tone_agreement':diagnostic['cohort_summary']['final_eligible_pool']['tone_agreement'],
             'cohorts':cohort_rows,'model_concordance':model_rows,
             'tables':{key:'outputs/tables/'+key+'.csv' for key in frames},
             'source_json_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
             'interpretation':'AI development-reference concordance, not human ground truth or validated classifier accuracy. Original and final eligibility pools remain distinct.',
             'wilson_interpretation':'Descriptive 95% Wilson agreement ranges assume independent items conditional on this inspected, stratified sample. They omit source/story dependence, AI-reference error, selection and post-review screening; they are not population accuracy confidence intervals.',
             'class_zero_division_convention':'As in the saved validator, undefined precision/recall/F1 is coded0. Reference support and predicted counts must accompany small/empty classes;0 must not be read as an estimated failure rate with no observations.',
             'adjudication':'Independent originals are preserved. No completed human adjudication or human reference correctness is claimed.'}
    (OUT/'validation_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False),encoding='utf-8')
    print(pd.DataFrame(model_rows).to_string(index=False))
    print('Exported six aggregate tables and validation_summary.json; no item-level text or labels copied.')
    return summary


if __name__=='__main__':
    main()

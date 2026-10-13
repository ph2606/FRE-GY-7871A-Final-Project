"""Prepare eligible human worksheets while preserving the original AI review pool."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def build():
    folder = ROOT/'data/annotations'
    scores = pd.read_csv(ROOT/'data/processed/media_scores.csv',keep_default_na=False)
    original = pd.read_csv(folder/'annotator_A_blinded.csv',keep_default_na=False)
    selected = scores[scores.id.isin(original.item_id)].copy()
    remaining = scores[~scores.id.isin(selected.id)].copy()
    remaining['packet_hash'] = remaining.id.map(lambda x:hashlib.sha256(('human-final-787126:'+x).encode()).hexdigest())
    buckets = [g.sort_values('packet_hash').to_dict('records') for _,g in remaining.groupby(['source','contextual_class'],sort=True)]
    additions=[]
    while len(selected)+len(additions)<300:
        progressed=False
        for bucket in buckets:
            if bucket and len(selected)+len(additions)<300:
                additions.append(bucket.pop(0));progressed=True
        if not progressed:raise ValueError('Insufficient final-eligible titles for 300-item packet')
    selected = pd.concat([selected,pd.DataFrame(additions)],ignore_index=True)
    assert len(selected)==300 and selected.id.nunique()==300
    columns = [c for c in original.columns if c not in ['item_id','text']]
    sheet=selected[['id','text']].rename(columns={'id':'item_id'}).copy()
    for col in columns:sheet[col]=''
    for letter,seed in [('A',797126),('B',807126)]:
        path=folder/f'human_final_{letter}_blinded.csv'
        if path.exists():
            old=pd.read_csv(path,keep_default_na=False)
            if old.tone.ne('').any():
                if set(old.item_id)!=set(sheet.item_id):raise ValueError('Do not overwrite completed human labels after corpus changes')
                continue
        sheet.sample(frac=1,random_state=seed).to_csv(path,index=False)
    selected[['id','source','source_group','month','contextual_class','numeric_claim_eligible']].to_csv(folder/'human_final_sampling_key_PRIVATE.csv',index=False)
    status={'status':'pending','final_eligible_items':300,'completed_human_annotators':0,
            'retained_from_original_review_pool':len(selected)-len(additions),'supplemented_final_eligible_items':len(additions),
            'note':'Final human worksheets contain 300 eligible items. Original300 AI review texts and scores are preserved separately; AI review eligibility is277.'}
    (ROOT/'outputs/human_final_packet_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    return status


if __name__=='__main__':print(json.dumps(build(),indent=2))

"""Critical media invariants: relevance safeguards, weights and fresh model install."""
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import media

@pytest.mark.parametrize('title,excluded',[
    ('BICEP3 tightens the bounds on cosmic inflation',True),
    ("Maps: See the parade and balloon inflation",True),
    ('Economy Candy - Photo Gallery',True),
    ('Steve Jobs',True),
    ('House Speaker says he did a horrible job',True),
    ('Nigerian inflation squeezes households',False), # first acquisition geography screen handles this country
    ('Myanmar economy contracts again',True),
    ('U.S. economy feels effects of Myanmar crisis',False),
    ('There is one major gift Trump is inheriting from Biden: A good job market',False),
    ('Condiment maker adds70 jobs in Georgia',False),
    ('Thousands in Puerto Rico still without housing since Maria',False),
    ('US unemployment rate falls to3.6%',False),
    ('My job loss has squeezed our grocery budget',False),
    ('Texas A&M president weighs tuition after one year in the job',False),
])
def test_strict_screen(title,excluded):
    assert bool(media.strict_screen_reason(title)) is excluded

def test_group_weights_and_unverified_calibration(tmp_path,monkeypatch):
    monkeypatch.setattr(media,'DATA',tmp_path);monkeypatch.setattr(media,'OUT',tmp_path)
    (tmp_path/'media_acquisition.json').write_text(json.dumps({'cutoff_exclusive_ny':'2026-10-13'}))
    frame=pd.DataFrame({'month':['2026-09-01']*5,'source_group':['national','national','national','local','social'],
       'source':['AP','AP','Reuters','Local','HN'],'media_tone':[1.,1.,-1.,.6,-.2],
       'vader_tone':[1.,1.,-1.,.6,-.2],'contextual_class':['positive','positive','negative','positive','neutral'],
       'vader_class':['positive','positive','negative','positive','neutral'],'geographic_relevance':['not_stated']*5})
    for c in list(media.RULES)+['political_actor_mention','political_credit_proxy','political_blame_proxy','numeric_claim_eligible']:frame[c]=0
    result=media.aggregate(frame).iloc[0]
    # AP's second title does not increase AP's outlet weight, nor national's group weight.
    assert result.media_tone==pytest.approx((0+.6-.2)/3)
    assert result.group_count==3 and result.source_count==4
    assert pd.isna(result.factual_error_rate) and result.verified_claim_count==0
    assert not result.partial_month

def test_official_model_fallback_without_sibling(tmp_path,monkeypatch):
    monkeypatch.setattr(media,'ROOT',tmp_path/'project')
    monkeypatch.setattr(media,'MODEL_DIR',tmp_path/'project/models'/media.REVISION)
    names=['config.json','merges.txt','vocab.json','special_tokens_map.json','pytorch_model.bin','README.md']
    payloads={name:('official-test-content:'+name).encode() for name in names}
    info={'sha':media.REVISION,'siblings':[{'rfilename':name,'lfs':{'sha256':hashlib.sha256(payload).hexdigest()}} for name,payload in payloads.items()]}
    class Response:
        status_code=200
        def __init__(self,payload):self.content=payload
        def raise_for_status(self):pass
        def iter_content(self,*args):yield self.content
        def __enter__(self):return self
        def __exit__(self,*args):pass
    calls=[]
    def get(url,**kwargs):
        calls.append(url)
        if '/api/models/' in url:return Response(json.dumps(info).encode())
        return Response(payloads[url.rsplit('/',1)[-1]])
    monkeypatch.setattr(media.requests,'get',get)
    assets=media.copy_model()
    assert len(assets)==6 and len(calls)==7
    assert all(media.REVISION in url for url in calls)
    media.copy_model()
    assert len(calls)==7 # local hash verification reuses immutable official bytes
    (media.MODEL_DIR/'config.json').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='hash mismatch'):media.copy_model()

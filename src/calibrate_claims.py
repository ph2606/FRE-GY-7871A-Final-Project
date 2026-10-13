"""Reproduce a small, purposive official-release numeric alignment diagnostic.

This checks values at title precision; it does not estimate a factual-error rate.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def run():
    metadata=json.loads((ROOT/'data/raw/media/official_claim_benchmarks.json').read_text(encoding='utf-8'))
    benchmarks=pd.DataFrame(metadata['sources'])
    benchmarks['release_day']=pd.to_datetime(benchmarks.release_at,utc=True).dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d')
    corpus=pd.read_csv(ROOT/'data/processed/media_scores.csv')
    records=[]
    for row in corpus[corpus.id.isin(metadata['claim_item_ids'])].itertuples():
        day=pd.Timestamp(row.published_at).tz_convert('America/New_York').strftime('%Y-%m-%d')
        official=benchmarks[benchmarks.release_day.eq(day)]
        if len(official)!=1:raise ValueError('Expected exactly one release-day benchmark')
        official=official.iloc[0]
        # Curated records each have one percentage; payroll counts are ignored.
        values=re.findall(r'(\d+(?:\.\d+)?)\s*%',row.text)
        if len(values)!=1:raise ValueError('Ambiguous percentage claim')
        value=float(values[0]);difference=value-float(official.value)
        availability=pd.Timestamp(row.available_at);release=pd.Timestamp(official.release_at)
        if availability<release:raise ValueError('Benchmark unavailable under conservative availability convention')
        explicit_period=bool(re.search(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b',row.text,re.I))
        records.append({'id':row.id,'text':row.text,'source':row.source,'month':row.month,
            'published_at':row.published_at,'available_at':row.available_at,'release_at':official.release_at,
            'official_observation_period':official.observation_period,'claim_value_percent':value,
            'official_value_percent':float(official.value),'difference_percentage_points':difference,
            'numeric_value_aligned':abs(difference)<0.05,'period_explicit_in_title':explicit_period,
            'official_url':official.url,'metric':'US headline U-3 unemployment rate, seasonally adjusted',
            'classification':'numerically_aligned; omitted definition/period or intraday vintage not fully verifiable from title' if abs(difference)<0.05 else 'numeric_discrepancy_requires_definition_and_vintage_review',
            'scope':'Single headline percentage; all rhetoric, payroll counts and wider article claims outside this check',
            'reviewer_type':'AI-assisted primary-source transcription and deterministic numeric comparison; no human verification'})
    checks=pd.DataFrame(records);checks.to_csv(ROOT/'data/processed/factual_calibration_checks.csv',index=False)
    monthly=pd.read_csv(ROOT/'data/processed/media_monthly.csv')
    monthly['numeric_alignment_checked_count']=monthly.month.map(checks.groupby('month').size()).fillna(0).astype(int)
    monthly['numeric_alignment_aligned_count']=monthly.month.map(checks.groupby('month').numeric_value_aligned.sum()).fillna(0).astype(int)
    monthly.to_csv(ROOT/'data/processed/media_monthly.csv',index=False)
    summary_path=ROOT/'outputs/media_summary.json';summary=json.loads(summary_path.read_text(encoding='utf-8'))
    summary['factual_calibration']={'numeric_eligible_titles':int(corpus.numeric_claim_eligible.sum()),
       'purposive_same_release_day_values_checked':len(checks),'numerically_aligned':int(checks.numeric_value_aligned.sum()),
       'population_factual_error_rate':None,'fully_verified_definition_period_and_intraday_vintage_claims':0,
       'interpretation':'Eight purposive unemployment-title percentages match archived official release values; this is numeric alignment, not an estimate of overall factual accuracy. Most titles omit precise definition or period; RSS intraday timestamps are unreliable. No factual-error rate is estimated.',
       'checks_path':'data/processed/factual_calibration_checks.csv','benchmarks_path':'data/raw/media/official_claim_benchmarks.json'}
    summary_path.write_text(json.dumps(summary,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(json.dumps(summary['factual_calibration'],indent=2))
    return checks

if __name__=='__main__':run()

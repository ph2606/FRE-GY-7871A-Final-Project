"""Validate deliverable consistency and bind the submission to local input hashes."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata as md
import json
import platform
import subprocess
import sys
import nbformat
import pandas as pd
from packaging.requirements import Requirement
from pptx import Presentation
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def environment_lock():
    required = []
    for line in (ROOT / 'requirements.txt').read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            required.append(Requirement(line).name)
    seen, versions = set(), {}
    while required:
        name = required.pop()
        key = name.lower().replace('_','-')
        if key in seen:
            continue
        seen.add(key)
        dist = md.distribution(name)
        versions[dist.metadata['Name']] = dist.version
        for raw in dist.requires or []:
            requirement = Requirement(raw)
            if requirement.marker is None or requirement.marker.evaluate({'extra': ''}):
                required.append(requirement.name)
    content = ['# Exact observed Python 3.12 Windows environment dependency closure.',
               '# For Linux/macOS regenerate platform-specific packages from requirements.txt.',
               '--extra-index-url https://download.pytorch.org/whl/cpu']
    content += [name + '==' + version for name,version in sorted(versions.items(),key=lambda x:x[0].lower())]
    (ROOT / 'requirements-lock.txt').write_text('\n'.join(content)+'\n',encoding='utf-8')
    return versions


def main():
    OUT.mkdir(exist_ok=True)
    pdf = ROOT / 'Panagiotis_Housos_Final_Project.pdf'
    pages = len(PdfReader(pdf).pages)
    assert 10 <= pages <= 12, pages
    nb = nbformat.read(ROOT / 'final_project.ipynb', as_version=4)
    nbformat.validate(nb)
    codes = [c for c in nb.cells if c.cell_type == 'code']
    assert codes and all(c.execution_count is not None for c in codes), 'Notebook not fully executed'
    assert not [o for c in codes for o in c.get('outputs',[]) if o.output_type == 'error']
    prs = Presentation(ROOT / 'Panagiotis_Housos_Final_Project.pptx')
    words = sum(len(s.notes_slide.notes_text_frame.text.split()) for s in prs.slides)
    assert 6 <= words/140 <= 8, f'Narration duration {words/140:.2f} minutes'
    html = (ROOT / 'dashboard.html').read_text(encoding='utf-8')
    assert 'Plotly.newPlot' in html and 'Human validation outstanding' in html
    metrics = pd.read_csv(OUT/'tables/model_metrics.csv')
    common = metrics[(metrics['sample']=='common_media_oos')&(metrics.target=='sentiment')]
    assert common.n.nunique()==1 and common.start.nunique()==1 and common.end.nunique()==1
    assert {'M1_economic','M2_economic_media','M3_economic_media_controls','Persistence'}.issubset(set(common.model))
    forecasts = pd.read_csv(OUT/'tables/forecasts.csv',parse_dates=['month','training_end'])
    assert (forecasts.training_end < forecasts.month).all()
    media = pd.read_csv(ROOT/'data/processed/media_monthly.csv')
    assert media.month.nunique() == len(media) and media.media_tone.between(-1,1).all()
    human = json.loads((OUT/'human_validation_metrics.json').read_text())
    assert human['human_specific_requirement_satisfied'] is False
    assert human['completed_independent_pairs'] == 0
    versions = environment_lock()
    inventory = []
    for folder in ['data','outputs']:
        for path in sorted((ROOT/folder).rglob('*')):
            if not path.is_file() or any(x in path.parts for x in ['__pycache__','jupyter_runtime','ipython','edge_preview']):
                continue
            if path.name in ['snapshot_manifest.json','deliverable_validation.json']:
                continue
            inventory.append({'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    digest = hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    (OUT/'snapshot_manifest.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
    summary = json.loads((OUT/'tables/economic_summary.json').read_text())
    media_summary = json.loads((OUT/'media_summary.json').read_text())
    lines = ['# Submission snapshot','',
             'Information cutoff: **October 13, 2026**, America/New_York. Election day is outside this snapshot.',
             'Raw/derived datasets, detailed annotations and model weights remain local and are excluded from Git.',
             'A fresh download reproduces the method, but mutable search feeds, original wording, deletions and revisions can change results.','',
             f'- Local file inventory: {len(inventory):,} files, {sum(x["bytes"] for x in inventory):,} bytes.',
             f'- Canonical inventory SHA-256: `{digest}`.',
             '- Full itemized inventory is local at `outputs/snapshot_manifest.json`.',
             f'- Media: {media_summary["n_titles"]:,} titles, {media_summary["months"]} months, {media_summary["complete_months"]} complete.',
             f'- Common media assessment: {summary["media_comparison"]["holdout_n"]} months.',
             '- Human-specific annotation requirement: **not satisfied**; AI diagnostics are separately identified.',
             '', '| Artifact / key input | SHA-256 |', '| --- | --- |']
    keys = ['data/processed/monthly_dataset.csv','data/processed/media_corpus.csv','data/processed/media_scores.csv',
            'data/processed/media_monthly.csv','outputs/tables/forecasts.csv','outputs/tables/model_metrics.csv',
            'outputs/tables/predictive_loss_tests.csv','docs/MEDIA_CODEBOOK.md',
            'Panagiotis_Housos_Final_Project.pdf','Panagiotis_Housos_Final_Project.pptx','final_project.ipynb','dashboard.html']
    for name in keys:
        path = ROOT/name
        if path.exists():lines.append(f'| `{name}` | `{sha(path)}` |')
    lines += ['',f'Observed interpreter: Python {platform.python_version()} on {platform.system()}; exact package closure in requirements-lock.txt.',
              'The latest Michigan historical targets are not historical survey vintages. Macro predictors use actual ALFRED snapshots; media tests remain retrospective pseudo-out-of-sample.',
              'Detailed AI annotations and claim checks are development diagnostics, not validated human ground truth.']
    (ROOT/'SNAPSHOT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    result = {'validated_at_utc':datetime.now(timezone.utc).isoformat(),'report_pages':pages,
              'notebook_code_cells':len(codes),'notebook_errors':0,'presentation_slides':len(prs.slides),
              'narration_words':words,'estimated_minutes_140wpm':words/140,
              'common_forecast_months':int(common.n.iloc[0]),'snapshot_manifest_sha256':digest,
              'human_requirement_satisfied':False,'platform':platform.platform(),
              'python':platform.python_version(),'package_count':len(versions)}
    (OUT/'deliverable_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()

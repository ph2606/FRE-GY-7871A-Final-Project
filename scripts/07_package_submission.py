"""Package the frozen submission from current tracked worktree bytes (stdlib only)."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import os
import re
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / 'Panagiotis_Housos_Final_Project_Submission.zip'
SUBMISSION_README = ROOT / 'SUBMISSION_README.md'
ASSETS = (
    'Panagiotis_Housos_Final_Project.pdf',
    'Panagiotis_Housos_Final_Project.pptx',
    'dashboard.html',
    'Provider_Bias_Comparison.png',
    'Provider_Bias_Comparison.pdf',
    'Investment_Strategy_Comparison.png',
    'Investment_Strategy_Comparison.pdf',
    'Bias_Trading_Comparison.png',
    'Bias_Trading_Comparison.pdf',
    'Country_Birth_Rates_Top_100.pdf',
    'Country_Birth_Rates_01.png',
    'Country_Birth_Rates_02.png',
    'Country_Birth_Rates_03.png',
    'Country_Birth_Rates_04.png',
    'Country_Birth_Rates_05.png',
    'Reader_Fertility_Trends.png',
    'Reader_Fertility_Trends.pdf',
    'Reader_AI_Learning.png',
    'Reader_AI_Learning.pdf',
)
ROOT_SOURCE = {
    '.gitattributes', '.gitignore', 'AI_USE.md', 'README.md', 'SNAPSHOT.md',
    'requirements.txt', 'requirements-lock.txt', 'final_project.ipynb',
}
SOURCE_DIRS = {'src', 'scripts', 'tests', 'docs'}
SOURCE_SUFFIXES = {'.py', '.md', '.txt', '.json', '.toml', '.yaml', '.yml', '.ini', '.cfg'}
EXCLUDED_DIRS = {
    'data', 'outputs', 'notes', 'raw', 'labels', 'annotations', 'weights', 'models',
    '.git', '.venv', '__pycache__', '.pytest_cache', '.ipynb_checkpoints',
}
CONTROL_NAMES = (
    'SNAPSHOT.md', 'outputs/snapshot_manifest.json',
    'outputs/deliverable_validation.json', 'outputs/test_summary.json',
)


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def sha(content):
    return hashlib.sha256(content).hexdigest()


def local_path(name):
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name or ':' in name:
        raise ValueError(f'Unsafe relative path: {name}')
    path = ROOT.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError(f'Path escapes the project: {name}')
    return path


def tracked_source():
    # --cached includes staged new files, even before their first commit.
    names = set(git('ls-files', '--cached', '-z').decode('utf-8').split('\0')) - {''}
    selected = set()
    for name in names:
        parts = PurePosixPath(name).parts
        if any(part.lower() in EXCLUDED_DIRS for part in parts):
            continue
        if name in ROOT_SOURCE or (
            parts[0] in SOURCE_DIRS and PurePosixPath(name).suffix.lower() in SOURCE_SUFFIXES
        ):
            local_path(name)
            selected.add(name)
    required = ROOT_SOURCE | {'scripts/07_package_submission.py'}
    missing = required - selected
    if missing:
        raise ValueError('Required source must be tracked or staged: ' + ', '.join(sorted(missing)))
    return selected


def readme(validation, tests, head, status, source_count):
    state = 'tracked changes present' if status else 'no tracked changes reported'
    return f'''# Final project submission

Panagiotis Housos | ph2606 | AI Applications in Finance | Fall 2026

The main study is frozen at October 13, 2026 (America/New_York). The separate
provider comparison was collected retrospectively for the October 15, 2026 revision.
The investing extension was developed October 17, with returns ending October 2.
The October 18 integrated revision adds Part B's manifesto, literature evidence,
World Bank demographic charts and an external published human-label benchmark.
The user explicitly overrode the original report page cap; the talk keeps 6-8 minutes.
These are study dates; the recorded checks below may have run later.

Contents:

- `Panagiotis_Housos_Final_Project.pdf`: {validation['report_pages']}-page report.
- `Panagiotis_Housos_Final_Project.pptx`: {validation['presentation_slides']} slides,
  with {validation['narration_words']:,} speaker-note words (about
  {validation['estimated_minutes_140wpm']:.1f} minutes at 140 words per minute).
- `dashboard.html`: self-contained interactive dashboard; open in a browser.
- `Provider_Bias_Comparison.png` and `.pdf`: standalone provider comparison figure.
- `Investment_Strategy_Comparison.png` and `.pdf`: net wealth comparison.
- `Bias_Trading_Comparison.png` and `.pdf`: three aggressive news-only experiments.
- `Country_Birth_Rates_Top_100.pdf`: five ranked bar charts, 20 entries per chart,
  with separate `Country_Birth_Rates_01.png` through `05.png` image exports.
- `Reader_Fertility_Trends` and `Reader_AI_Learning` in PNG/PDF:
  other original Part B charts with sources and interpretation boundaries.
- `final_project.ipynb`: executed notebook with {validation['notebook_code_cells']}
  code cells and {validation['notebook_errors']} recorded errors.
- {source_count} tracked source/documentation files, including the notebook,
  `README.md`, `AI_USE.md`, dependencies, tests and `SNAPSHOT.md`.

Recorded validation: {validation['validated_at_utc']}.
Recorded test command: `{tests['command']}`; {tests['passed']} passed,
exit code {tests['exit_code']}, recorded {tests['recorded_at_utc']}.
Packaging checks file hashes and archive integrity; it does not rerun those tests.
The provider figure compares {validation['provider_comparison_n']} providers over
{validation['common_provider_events']} identical releases. Its relative negativity
proxy uses a selected peer reference; it is not factual accuracy or ideological bias.
The preferred monthly 60% SPY / 40% BIL allocation was chosen after comparing the
fixed strategies. Historical profit after modeled costs does not establish media
alpha, untouched validation, suitability for every investor, or future profit.
The final revision explains concepts from scratch and adds three experiments
whose fund choices use only earlier relative negative wording. They use actual
daily leveraged ETF histories. All three underperform SPY's compounded growth
on the same dates; one suffers a large loss. The proxy does not verify bias.

The requirement for two independent human annotators on 300 items remains
**unsatisfied**. AI annotation diagnostics are disclosed separately and cannot
substitute for human labels, agreement or accuracy. No participants were recruited.

Raw/derived datasets, item-level text and labels, cached responses, model weights,
working outputs and private notes are excluded. Exact data-dependent reproduction
requires the retained local inputs/review decisions; mutable public downloads can
change the sample. The notebook contains saved aggregate results. See `README.md`
for the workflow and `AI_USE.md` for AI assistance and limitations.

Git HEAD at packaging: `{head}`; {state}.
Included source is captured from the current tracked worktree, including staged
new files; it is not asserted to equal HEAD. Untracked source is excluded.
`SNAPSHOT.md` binds the notebook and all nine generated deliverables to their hashes.
'''.encode('utf-8')


def main():
    git_root = Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve()
    if git_root != ROOT:
        raise ValueError('The script must belong to this project Git root')
    for target in (ARCHIVE, SUBMISSION_README):
        if target.resolve().parent != ROOT:
            raise ValueError(f'Output must stay in the explicit project root: {target.name}')

    controls = {name: local_path(name).read_bytes() for name in CONTROL_NAMES}
    validation = json.loads(controls['outputs/deliverable_validation.json'])
    tests = json.loads(controls['outputs/test_summary.json'])
    if tests['exit_code'] != 0 or tests['passed'] <= 0 or validation['notebook_errors'] != 0:
        raise ValueError('Successful recorded tests and an error-free notebook are required')
    if validation['human_requirement_satisfied'] is not False:
        raise ValueError('Update the submission limitation text after verified human validation')

    manifest = json.loads(controls['outputs/snapshot_manifest.json'])
    digest = sha(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode())
    snapshot = controls['SNAPSHOT.md'].decode('utf-8')
    digest_match = re.search(r'Canonical inventory SHA-256: `([0-9a-f]{64})`', snapshot)
    if not digest_match or digest != digest_match.group(1) or digest != validation['snapshot_manifest_sha256']:
        raise ValueError('Snapshot inventory and recorded validation disagree; freeze again')
    inventory = {entry['path']: entry for entry in manifest}
    test_entry = inventory['outputs/test_summary.json']
    if sha(controls['outputs/test_summary.json']) != test_entry['sha256']:
        raise ValueError('Recorded test summary changed after the snapshot; freeze again')
    bound = dict(re.findall(r'\| `([^`]+)` \| `([0-9a-f]{64})` \|', snapshot))

    source_names = tracked_source()
    payload = {
        name: controls[name] if name in controls else local_path(name).read_bytes()
        for name in sorted(source_names | set(ASSETS))
    }
    for name in (*ASSETS, 'final_project.ipynb'):
        if name not in bound:
            raise ValueError(f'Missing direct SNAPSHOT.md artifact hash: {name}')
    for name, content in payload.items():
        if name in bound and sha(content) != bound[name]:
            raise ValueError(f'Artifact changed after the snapshot: {name}')
    notebook = json.loads(payload['final_project.ipynb'])
    cells = [cell for cell in notebook['cells'] if cell['cell_type'] == 'code']
    if (len(cells) != validation['notebook_code_cells']
            or any(cell.get('execution_count') is None for cell in cells)
            or any(out.get('output_type') == 'error' for cell in cells for out in cell.get('outputs', []))):
        raise ValueError('Notebook execution does not match recorded validation')

    head = git('rev-parse', 'HEAD').decode().strip()
    status = git('status', '--porcelain=v1', '-z', '--untracked-files=no')
    submission = readme(validation, tests, head, status, len(source_names))
    payload['SUBMISSION_README.md'] = submission
    temporary = []
    try:
        fd, name = tempfile.mkstemp(prefix='.submission-', suffix='.zip', dir=ROOT)
        os.close(fd)
        temporary_zip = Path(name)
        temporary.append(temporary_zip)
        with zipfile.ZipFile(temporary_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, content in sorted(payload.items()):
                member = zipfile.ZipInfo(name, date_time=(2026, 10, 15, 0, 0, 0))
                member.create_system = 3
                member.external_attr = 0o100644 << 16
                member.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(member, content, compresslevel=9)
        with zipfile.ZipFile(temporary_zip) as archive:
            if archive.testzip() is not None or archive.namelist() != sorted(payload):
                raise ValueError('Archive integrity or member list check failed')
            for name, content in payload.items():
                if archive.read(name) != content:
                    raise ValueError(f'Embedded bytes differ from captured input: {name}')

        # Abort rather than publish a mixture if another build changed the inputs.
        for name, content in {**controls, **payload}.items():
            if name != 'SUBMISSION_README.md' and local_path(name).read_bytes() != content:
                raise ValueError(f'Input changed during packaging: {name}')
        if (tracked_source() != source_names or git('rev-parse', 'HEAD').decode().strip() != head
                or git('status', '--porcelain=v1', '-z', '--untracked-files=no') != status):
            raise ValueError('Tracked source state changed during packaging; retry after the build finishes')

        fd, name = tempfile.mkstemp(prefix='.submission-', suffix='.md', dir=ROOT)
        temporary_readme = Path(name)
        temporary.append(temporary_readme)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(submission)
        # Both replacements are narrowly scoped, same-directory atomic operations.
        os.replace(temporary_readme, SUBMISSION_README)
        os.replace(temporary_zip, ARCHIVE)
    finally:
        for path in temporary:
            if path.parent == ROOT:
                path.unlink(missing_ok=True)
    print(f'Packaged {len(payload)} files: {ARCHIVE.name}')
    print(f'{ARCHIVE.stat().st_size:,} bytes; SHA-256 {sha(ARCHIVE.read_bytes())}')


if __name__ == '__main__':
    main()

"""Execute the submitted notebook with the same interpreter used for this script."""
from pathlib import Path
import os
import sys
import nbformat
from nbclient import NotebookClient
from ipykernel.kernelspec import install

ROOT = Path(__file__).resolve().parents[1]
runtime = ROOT / 'outputs' / 'jupyter_runtime'
runtime.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('JUPYTER_RUNTIME_DIR', str(runtime))
os.environ.setdefault('IPYTHONDIR', str(ROOT / 'outputs' / 'ipython'))
install(user=True, kernel_name='finance_final_project', display_name='Python (Finance final project)')
path = ROOT / 'final_project.ipynb'
notebook = nbformat.read(path, as_version=4)
NotebookClient(notebook, timeout=1800, kernel_name='finance_final_project',
               resources={'metadata': {'path': str(ROOT)}}).execute()
errors = [o for c in notebook.cells if c.cell_type == 'code'
          for o in c.get('outputs', []) if o.output_type == 'error']
assert not errors, errors
nbformat.validate(notebook)
path.write_text(nbformat.writes(notebook), encoding='utf-8', newline='\n')
print(f'Executed {sum(c.cell_type == "code" for c in notebook.cells)} code cells with {sys.executable}.')

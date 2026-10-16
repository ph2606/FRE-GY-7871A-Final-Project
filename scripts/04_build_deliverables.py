"""Build the report, saved-output notebook, dashboard and narrated presentation."""
from pathlib import Path
import hashlib
import re
import sys
import json
import shutil
import nbformat as nbf
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
from study_content import sections, slides
from src.dashboard import build as build_dashboard
from src.exhibits import build as build_figures
from src.annotation_packet import build as build_human_packet


def esc(value):
    mapping = {'&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
               '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
    return ''.join(mapping.get(char, char) for char in str(value))


def prose(value):
    saved = []
    def keep(text):
        saved.append(text)
        return f'ZZTOKEN{len(saved)-1}ZZ'
    value = re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)',
                   lambda m: keep(r'\href{' + esc(m[2]) + '}{' + esc(m[1]) + '}'), value)
    value = re.sub(r'\*\*(.*?)\*\*', lambda m: keep(r'\textbf{' + esc(m[1]) + '}'), value)
    value = esc(value)
    for i, text in enumerate(saved):
        value = value.replace(f'ZZTOKEN{i}ZZ', text)
    return value


def latex_table(item):
    n = len(item['headers'])
    widths = item.get('widths', [1 / n] * n)
    layout = ''.join(r'>{\raggedright\arraybackslash}p{' + str(w) +
                     r'\dimexpr\linewidth-' + str(2*n) + r'\tabcolsep\relax}' for w in widths)
    lines = [r'\par\smallskip\noindent{\fontsize{9.0}{11.1}\selectfont',
             r'\begin{tabular}{' + layout + '}', r'\toprule',
             ' & '.join(r'\textbf{' + esc(h) + '}' for h in item['headers']) + r' \\', r'\midrule']
    lines.extend(' & '.join(esc(x) for x in row) + r' \\[3pt]' for row in item['rows'])
    return '\n'.join(lines + [r'\bottomrule\end{tabular}}\par\smallskip'])


PREAMBLE = r'''\documentclass[11pt,letterpaper]{article}
\usepackage[margin=0.7in,headheight=15pt,headsep=13pt,footskip=20pt]{geometry}
\usepackage{fontspec}
\IfFontExistsTF{Cambria}{\setmainfont{Cambria}}{\setmainfont{Latin Modern Roman}}
\IfFontExistsTF{Calibri}{\setsansfont{Calibri}}{\setsansfont{Latin Modern Sans}}
\usepackage{amsmath,booktabs,array,graphicx,xcolor,fancyhdr,titlesec,hyperref}
\definecolor{navy}{HTML}{18354B}\definecolor{teal}{HTML}{087E83}
\hypersetup{colorlinks=true,urlcolor=teal,linkcolor=navy,pdfauthor={Panagiotis Housos},pdftitle={Economic Narratives and Consumer Sentiment Ahead of the 2026 Midterms}}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\sffamily\small AI Applications in Finance | Final Project}
\fancyhead[R]{\sffamily\small Panagiotis Housos | ph2606}
\fancyfoot[L]{\sffamily\footnotesize Information cutoff: October 13, 2026 | Preliminary evidence}
\fancyfoot[R]{\sffamily\small\thepage\ / 12}
\renewcommand{\headrulewidth}{0.3pt}
\titleformat{\section}{\sffamily\Large\bfseries\color{navy}}{}{0pt}{}
\titlespacing*{\section}{0pt}{0pt}{10pt}
\setlength{\parindent}{0pt}\setlength{\parskip}{7pt}
\setlength{\tabcolsep}{4pt}\renewcommand{\arraystretch}{1.05}
\emergencystretch=2em
\begin{document}
\fontsize{10.6}{13.5}\selectfont
'''


def build_report(content):
    tex = [PREAMBLE]
    markdown = ['# Economic Narratives and Consumer Sentiment Ahead of the 2026 Midterms',
                'Panagiotis Housos | ph2606 | Fall 2026', '']
    for page, (title, items) in enumerate(content):
        if page:
            tex.append(r'\newpage')
        if page == 0:
            tex += [r'{\sffamily\fontsize{23}{27}\selectfont\bfseries\color{navy} Economic Narratives and Consumer Sentiment}\par',
                    r'{\sffamily\large Ahead of the 2026 U.S. Midterm Elections}\par\bigskip']
        if page == 11:
            tex.append(r'\fontsize{9.4}{11.8}\selectfont')
        tex.append(r'\section*{' + esc(title) + '}')
        markdown += ['## ' + title, '']
        for item in items:
            if item['type'] == 'p':
                tex += [prose(item['text']), r'\par']
                markdown += [item['text'], '']
            elif item['type'] == 'table':
                tex.append(latex_table(item))
                markdown += ['| ' + ' | '.join(item['headers']) + ' |',
                             '| ' + ' | '.join(['---'] * len(item['headers'])) + ' |']
                markdown += ['| ' + ' | '.join(map(str, row)) + ' |' for row in item['rows']]
                markdown.append('')
            elif item['type'] == 'figure':
                tex += [r'\begin{center}\includegraphics[width=' + item.get('width', '.97') + r'\linewidth]{outputs/' + item['name'] + r'.pdf}\end{center}',
                        r'{\footnotesize\color{navy} ' + prose(item['caption']) + r'\par}']
                markdown += ['![' + item['caption'] + '](outputs/' + item['name'] + '.png)', '']
    (ROOT / 'report.tex').write_text('\n'.join(tex + [r'\end{document}']), encoding='utf-8')
    (ROOT / 'REPORT.md').write_text('\n'.join(markdown), encoding='utf-8')


def build_notebook(content):
    input_paths = ['data/processed/monthly_dataset.csv','data/processed/media_monthly.csv',
                   'outputs/tables/provider_bias.csv']
    expected_inputs = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                       for name in input_paths if (ROOT/name).exists()}
    cells = [nbf.v4.new_markdown_cell('# Economic narratives and consumer sentiment\n\n**Panagiotis Housos | ph2606 | AI Applications in Finance | Final Project**\n\nInformation cutoff: October 13, 2026. Human validation is not completed; independent AI reviews are explicitly separate. Acquisition and model scoring run separately. The cells below rerun analysis from local frozen inputs. Raw datasets are excluded from Git under the established submission policy.'),
             nbf.v4.new_code_cell("from pathlib import Path\nimport json\nimport hashlib\nimport pandas as pd\nfrom IPython.display import display, Image\nROOT = Path.cwd()\nassert (ROOT / 'src/economics.py').exists(), 'Execute from the project root.'\nexpected_inputs = " + repr(expected_inputs) + "\nfor name, expected in expected_inputs.items():\n    path = ROOT / name\n    assert path.exists(), f'Acquire required input: {name}'\n    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, f'Input changed: {name}. Rerun analysis and rebuild deliverables before executing this notebook.'\npd.set_option('display.max_columns', 14)\npd.set_option('display.max_colwidth', 70)\npd.set_option('display.precision', 4)"),
             nbf.v4.new_markdown_cell('## Recompute the frozen empirical analysis\n\nThe economic feature matrix uses historical ALFRED snapshots. Media reconstruction is retrospective and subject to source selection and original-wording limitations. The package never invents missing records, exposure or human labels.'),
             nbf.v4.new_code_cell("import subprocess, sys\nfor command in [['scripts/03_analyze.py'], ['-m', 'src.dynamics']]:\n    result = subprocess.run([sys.executable, *command], cwd=ROOT, capture_output=True, text=True)\n    print(result.stdout)\n    assert result.returncode == 0, result.stderr\nprint('Primary analysis and exploratory dynamics recalculated from acquired observations.')")]
    cells += [nbf.v4.new_markdown_cell('## Persistence and differenced-model sensitivity\n\nThese checks were added after the primary analysis and are exploratory. ADF and KPSS have different null hypotheses; structural breaks limit either interpretation. The differenced models use the same 44 test months and a separately identified two-contrast loss-test family.'),
              nbf.v4.new_code_cell("display(pd.read_csv(ROOT / 'outputs/tables/dynamics_unit_root.csv'))\ndisplay(pd.read_csv(ROOT / 'outputs/tables/dynamics_differenced_metrics.csv'))\ndisplay(pd.read_csv(ROOT / 'outputs/tables/dynamics_loss_hac.csv'))")]
    cells += [nbf.v4.new_markdown_cell('## Independent AI diagnostic: class and source concordance\n\nThese are AI development references, not human ground truth. The original pool has 300 items; final-corpus eligibility and mixed/uncertain exclusions are explicit. Small source/class cells have unstable estimates. Required human validation remains pending.'),
              nbf.v4.new_code_cell("path = ROOT / 'outputs/ai_diagnostic_validation_metrics.json'\nai = json.loads(path.read_text()) if path.exists() else {}\nif ai:\n    display(pd.Series({k: ai.get(k) for k in ['label_type','completed_independent_pairs','tone_agreement','tone_cohens_kappa','annotation_pool_final_eligible_n','annotation_pool_final_excluded_n','human_specific_requirement_satisfied']}))\n    rows, classes = [], []\n    for annotator, models in ai['model_reference_concordance'].items():\n        for model, entry in models.items():\n            for source, result in entry['by_source'].items():\n                rows.append({'reference': annotator, 'model': model, 'source': source, 'n': result['n'], 'agreement': result['agreement'], 'macro_F1_concordance': result['macro_f1_reference_concordance']})\n            for label, result in entry['class_concordance'].items():\n                classes.append({'reference': annotator, 'model': model, 'class': label, **result})\n    display(pd.DataFrame(rows))\n    display(pd.DataFrame(classes))\nelse:\n    print('Independent AI diagnostic inputs are unavailable in this clone; no human labels are inferred.')"),
              nbf.v4.new_markdown_cell('## Political-name and source-label stress tests\n\nThe original text is held constant except for the specified change. Changed names can change meaning. Class switches do not prove political discrimination or factual bias.'),
              nbf.v4.new_code_cell("media_summary = json.loads((ROOT / 'outputs/media_summary.json').read_text())\ndisplay(pd.DataFrame(media_summary['perturbation']['variant_comparisons']))\nprint('Source-prefix paired mean absolute tone difference:', media_summary['perturbation']['source_pair_mean_absolute_delta'])\nprint('Factual-calibration status:', media_summary.get('factual_calibration'))")]
    if (ROOT/'outputs/tables/provider_bias.csv').exists():
        cells += [nbf.v4.new_markdown_cell('## News-provider comparison: matched official releases\n\nA separate supplemental sample includes CNBC and Fox brands. The provider bars use a common set of releases and a defined peer reference. This is a relative negative-framing proxy, not a factual or ideological rating. The original forecast corpus and 300-title AI review remain separate; the new providers do not have independent human validation.'),
                  nbf.v4.new_code_cell("provider_table = pd.read_csv(ROOT / 'outputs/tables/provider_bias.csv')\ndisplay(provider_table)\nprovider_summary = json.loads((ROOT / 'outputs/tables/provider_bias_summary.json').read_text())\ndisplay(pd.Series(provider_summary, name='provider_comparison_protocol'))")]
    for page_index,(title, items) in enumerate(content):
        cells.append(nbf.v4.new_markdown_cell('## ' + title))
        for item_index,item in enumerate(items):
            if item['type'] == 'p':
                cells.append(nbf.v4.new_markdown_cell(item['text']))
            elif item['type'] == 'table':
                code = ("import sys\nif str(ROOT / 'scripts') not in sys.path: sys.path.insert(0, str(ROOT / 'scripts'))\n"
                        "from study_content import sections\nitem = sections()["+str(page_index)+"][1]["+str(item_index)+"]\n"
                        "display(pd.DataFrame(item['rows'], columns=item['headers']))")
                cells.append(nbf.v4.new_code_cell(code))
            elif item['type'] == 'figure':
                cells.append(nbf.v4.new_code_cell("display(Image(filename=str(ROOT / 'outputs' / " + repr(item['name'] + '.png') + ")))"))
                cells.append(nbf.v4.new_markdown_cell(item['caption']))
    cells.append(nbf.v4.new_markdown_cell('## Reproducibility and limitations\n\nSee `README.md`, `SNAPSHOT.md`, `AI_USE.md`, the source manifest, codebook, causal proposal, and annotation-validation protocol. A fresh download can change mutable feed results. Saved aggregate outputs preserve this snapshot, while item-level data remain local.'))
    nb = nbf.v4.new_notebook(cells=cells)
    nb.metadata.kernelspec = {'name': 'finance_final_project', 'display_name': 'Python (Finance final project)', 'language': 'python'}
    nb.metadata.language_info = {'name': 'python', 'version': '3.12'}
    nbf.validate(nb)
    nbf.write(nb, ROOT / 'final_project.ipynb')


def add_text(slide, left, top, width, height, text, size=24, color='18354B', bold=False):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    for i, line in enumerate(text.split('\n')):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.text = line
        p.font.name = 'Calibri'
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = RGBColor.from_string(color)
        p.space_after = Pt(14)
    return box


def build_slides(content):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    notes = []
    for i, item in enumerate(content):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor.from_string('F4F7F8')
        add_text(slide, .55, .35, 12.2, .9, item['title'], 32, bold=True)
        add_text(slide, .58, 1.38, 5.5 if item.get('image') else 11.9, 5.1,
                 '\n'.join(item['points']), 23)
        if item.get('image'):
            slide.shapes.add_picture(str(ROOT / 'outputs' / (item['image'] + '.png')),
                                     Inches(6.2), Inches(1.45), width=Inches(6.6))
        add_text(slide, .6, 6.98, 11.7, .3,
                 f'Panagiotis Housos | ph2606   •   As of October 13, 2026   •   {i+1}/{len(content)}', 11)
        slide.notes_slide.notes_text_frame.text = item['notes']
        notes += [f"Slide {i+1}: {item['title']}", item['notes'], '']
    prs.save(ROOT / 'Panagiotis_Housos_Final_Project.pptx')
    (ROOT / 'docs' / 'presentation_script.md').write_text('\n'.join(notes), encoding='utf-8')
    word_count = sum(len(s['notes'].split()) for s in content)
    print(f'Presentation: {len(content)} slides, {word_count} narration words (~{word_count/140:.1f} min at 140 wpm).')


if __name__ == '__main__':
    (ROOT / 'docs').mkdir(exist_ok=True)
    build_human_packet()
    build_figures()
    content = sections()
    assert len(content) == 12
    build_report(content)
    build_notebook(content)
    build_dashboard()
    build_slides(slides())
    if (ROOT/'outputs/provider_bias.png').exists():
        shutil.copyfile(ROOT/'outputs/provider_bias.png',ROOT/'Provider_Bias_Comparison.png')
        shutil.copyfile(ROOT/'outputs/provider_bias.pdf',ROOT/'Provider_Bias_Comparison.pdf')
    print('Built 12-page report source, notebook, dashboard, and presentation.')

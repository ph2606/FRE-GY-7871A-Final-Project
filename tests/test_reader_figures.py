"""Figure bytes must not depend on charts rendered earlier in the process.

Demography fixtures are synthetic and never enter empirical outputs. Every file
created by these tests is inside pytest's temporary directory.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from src import part_b_demography as demography
from src import reader_evidence


@pytest.fixture(autouse=True)
def restore_matplotlib_state():
    with plt.rc_context():
        yield
        plt.close('all')


@pytest.fixture
def synthetic_country_comparison():
    """Thirteen country rows plus world, with deliberately artificial values."""
    codes=demography.ENTITIES[:14]
    old=np.linspace(1.5,6.5,len(codes))
    return pd.DataFrame({
        'entity':codes,
        'entity_name':[demography.LABELS[code] for code in codes],
        'fertility_births_per_woman_1990':old,
        'fertility_births_per_woman_2023':.6*old+.1,
        'births_per_1000_people_1990':7*old+1,
        'births_per_1000_people_2023':4*old+2,
    })


@pytest.fixture
def synthetic_income_history():
    rows=[]
    for index,code in enumerate(['WLD','LIC','LMC','UMC','HIC']):
        for year in [1990,2000,2010,2023]:
            rows.append({'entity':code,'year':year,
                         'fertility_births_per_woman':1.4+.8*index-.015*(year-1990)})
    return pd.DataFrame(rows)


def inherit_conflicting_style():
    # The cap setting reproduces the exhibits -> demography build-order bug.
    # Other inherited options guard against the same failure returning through
    # fonts, automatic bounds or transparent/tight output in another notebook.
    plt.style.use('dark_background')
    plt.rcParams.update({'lines.solid_capstyle':'round','lines.dash_capstyle':'round',
                         'font.weight':'bold','axes.autolimit_mode':'round_numbers',
                         'savefig.transparent':True,'savefig.bbox':'tight',
                         'figure.dpi':173,'path.simplify':False})


def figure_bytes(folder,stem):
    result={suffix:(folder/f'{stem}.{suffix}').read_bytes() for suffix in ['png','pdf']}
    assert result['png'].startswith(b'\x89PNG\r\n\x1a\n')
    assert result['pdf'].startswith(b'%PDF-')
    return result


@pytest.mark.parametrize('chart,fixture_name,stem',[
    ('paired_figure','synthetic_country_comparison','part_b_demography_comparison'),
    ('income_figure','synthetic_income_history','part_b_fertility_trends'),
])
def test_demography_png_and_pdf_are_independent_of_prior_style(
        tmp_path,monkeypatch,request,chart,fixture_name,stem):
    data=request.getfixturevalue(fixture_name)
    render=getattr(demography,chart)
    plt.rcdefaults()
    clean=tmp_path/'clean'
    monkeypatch.setattr(demography,'OUT',clean)
    render(data)
    expected=figure_bytes(clean,stem)

    inherit_conflicting_style()
    inherited=tmp_path/'inherited'
    monkeypatch.setattr(demography,'OUT',inherited)
    render(data)
    actual=figure_bytes(inherited,stem)
    assert actual==expected,'Demography output changed with inherited Matplotlib style'


def test_reader_learning_png_and_pdf_are_independent_of_prior_style(tmp_path,monkeypatch):
    def render(folder):
        monkeypatch.setattr(reader_evidence,'OUT',folder)
        monkeypatch.setattr(reader_evidence,'TABLES',folder/'tables')
        reader_evidence.build()
        return figure_bytes(folder,'reader_ai_learning')

    plt.rcdefaults()
    expected=render(tmp_path/'clean')
    inherit_conflicting_style()
    actual=render(tmp_path/'inherited')
    assert actual==expected,'Reader learning output changed with inherited Matplotlib style'

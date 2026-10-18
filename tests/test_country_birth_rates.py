"""Synthetic World Bank records protect the ranking and five-chart comparison."""
from copy import deepcopy

import matplotlib
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from src import country_birth_rates as birth


@pytest.fixture
def payloads():
    metadata, values = [], []
    for i in range(110):
        iso2 = chr(65+i//26)+chr(65+i%26)
        code = 'X'+iso2
        metadata.append({'id': code, 'iso2Code': iso2, 'name': f'Economy {i:03}',
                         'region': {'id': 'REG', 'value': 'Test region'},
                         'incomeLevel': {'value': 'High income'}})
        values.append({'indicator': {'id': 'SP.DYN.CBRT.IN'}, 'date': '2023',
                       'country': {'id': iso2, 'value': 'Untrusted response label'},
                       'countryiso3code': code, 'value': 55-i/4})
    return [{'page': 1, 'pages': 1}, values], [{'page': 1, 'pages': 1}, metadata]


def add_entity(values, metadata, code, iso2, name, value, region_id='REG', region_name='Test region'):
    metadata[1].append({'id': code, 'iso2Code': iso2, 'name': name,
                        'region': {'id': region_id, 'value': region_name},
                        'incomeLevel': {'value': 'High income'}})
    values[1].append({'indicator': {'id': birth.INDICATOR}, 'date': '2023',
                      'country': {'id': iso2}, 'countryiso3code': code, 'value': value})


def test_official_metadata_excludes_aggregates_and_missing_but_retains_territories_and_zero(payloads):
    values, metadata = payloads
    add_entity(values, metadata, 'WLD', '1W', 'World', 999, region_id='NA')
    add_entity(values, metadata, 'HIC', 'XD', 'High income group', 888, region_name='Aggregates')
    add_entity(values, metadata, 'MIS', 'MS', 'Missing observation', None)
    add_entity(values, metadata, 'HKG', 'HK', 'Hong Kong SAR, China', 0)
    omitted = {'id': 'OMT', 'iso2Code': 'OM', 'name': 'Not returned',
               'region': {'id': 'REG', 'value': 'Test region'},
               'incomeLevel': {'value': 'High income'}}
    metadata[1].append(omitted)

    ranked, excluded = birth.rank_observations(values, metadata)
    assert len(ranked) == 111
    assert not {'WLD', 'HIC', 'MIS', 'OMT'} & set(ranked.iso3)
    assert ranked.set_index('iso3').loc['HKG', 'births_per_1000_people'] == 0
    assert ranked.set_index('iso3').loc['HKG', 'country'] == 'Hong Kong SAR, China'
    assert set(excluded.iso3) == {'WLD', 'HIC', 'MIS', 'OMT'}
    assert 'aggregate' in excluded.set_index('iso3').loc['WLD', 'reason'].lower()
    assert ranked['rank'].tolist() == list(range(1, 112))


@pytest.mark.parametrize('invalid', [-0.01, np.nan, np.inf, -np.inf])
def test_invalid_rates_cannot_silently_enter_a_rank_or_become_zero(payloads, invalid):
    values, metadata = payloads
    values[1][0]['value'] = invalid
    with pytest.raises(ValueError, match='Invalid birth rate'):
        birth.rank_observations(values, metadata)


@pytest.mark.parametrize(('field', 'value'), [('date', '2024'), ('indicator', {'id': 'SP.DYN.TFRT.IN'})])
def test_other_years_and_fertility_cannot_replace_the_common_year_birth_rate(payloads, field, value):
    values, metadata = payloads
    values[1][0][field] = value
    with pytest.raises(ValueError, match='indicator/year'):
        birth.rank_observations(values, metadata)


@pytest.mark.parametrize('defect', ['missing_metadata', 'disagreeing_code', 'duplicate_value', 'duplicate_metadata'])
def test_country_identity_errors_fail_instead_of_double_counting_or_guessing(payloads, defect):
    values, metadata = payloads
    if defect == 'missing_metadata':
        values[1][0]['country']['id'] = 'ZZ'
    elif defect == 'disagreeing_code':
        values[1][0]['countryiso3code'] = 'ZZZ'
    elif defect == 'duplicate_value':
        values[1].append(deepcopy(values[1][0]))
    else:
        metadata[1].append(deepcopy(metadata[1][0]))
    with pytest.raises(ValueError):
        birth.rank_observations(values, metadata)


def test_sort_uses_unrounded_values_then_official_name_and_code_and_is_order_invariant(payloads):
    values, metadata = payloads
    rates = [99.044, 99.043, 98.0, 98.0, 98.0]
    names = ['Zebra', 'Alpha', 'Zulu', 'Shared name', 'Shared name']
    for i, (rate, name) in enumerate(zip(rates, names)):
        values[1][i]['value'] = rate
        metadata[1][i]['name'] = name
    ranked, _ = birth.rank_observations(values, metadata)
    assert ranked.iso3.head(5).tolist() == ['XAA', 'XAB', 'XAD', 'XAE', 'XAC']
    assert round(ranked.births_per_1000_people.iloc[0], 1) == round(ranked.births_per_1000_people.iloc[1], 1)
    shuffled_values, shuffled_metadata = deepcopy(values), deepcopy(metadata)
    rng = np.random.default_rng(2023)
    rng.shuffle(shuffled_values[1])
    rng.shuffle(shuffled_metadata[1])
    replay, _ = birth.rank_observations(shuffled_values, shuffled_metadata)
    pd.testing.assert_frame_equal(ranked, replay)


def test_fewer_than_one_hundred_qualified_economies_is_not_presented_as_a_top_hundred(payloads):
    values, metadata = payloads
    values[1] = values[1][:99]
    with pytest.raises(ValueError, match='Fewer than100'):
        birth.rank_observations(values, metadata)


def test_five_groups_cover_top_hundred_once_and_keep_global_ranks(payloads):
    ranked, _ = birth.rank_observations(*payloads)
    groups = birth.split_top100(ranked)
    assert len(groups) == 5
    assert [len(group) for group in groups] == [20]*5
    combined = pd.concat(groups, ignore_index=True)
    assert combined.iso3.nunique() == 100
    assert combined['rank'].tolist() == list(range(1, 101))
    assert [(int(group['rank'].min()), int(group['rank'].max())) for group in groups] == [
        (1, 20), (21, 40), (41, 60), (61, 80), (81, 100)]
    pd.testing.assert_frame_equal(combined, ranked.head(100).reset_index(drop=True))
    groups[0].loc[groups[0].index[0], 'country'] = 'Changed in a chart copy'
    assert ranked.country.iloc[0] != 'Changed in a chart copy'


@pytest.mark.parametrize('defect', ['duplicate_economy', 'rank_gap', 'ascending_rate', 'only_99'])
def test_chart_groups_reject_an_invalid_top_hundred(payloads, defect):
    ranked, _ = birth.rank_observations(*payloads)
    ranked = ranked.head(100).copy()
    if defect == 'duplicate_economy':
        ranked.loc[1, 'iso3'] = ranked.loc[0, 'iso3']
    elif defect == 'rank_gap':
        ranked.loc[99, 'rank'] = 101
    elif defect == 'ascending_rate':
        ranked.loc[1, 'births_per_1000_people'] = ranked.loc[0, 'births_per_1000_people']+1
    else:
        ranked = ranked.head(99)
    with pytest.raises(ValueError):
        birth.split_top100(ranked)


def test_all_five_chart_pages_share_zero_scale_units_style_and_one_hundred_bar_labels(payloads):
    ranked, _ = birth.rank_observations(*payloads)
    ceiling = birth.common_axis_max(ranked)
    assert ceiling >= ranked.births_per_1000_people.max()+4
    assert ceiling % 10 == 0
    displayed_ranks = []
    figures = []
    try:
        with matplotlib.rc_context():
            for page, group in enumerate(birth.split_top100(ranked), 1):
                fig = birth.page_figure(group, page, ceiling)
                figures.append(fig)
                assert len(fig.axes) == 2
                assert any('2023' in text.get_text() for text in fig.texts)
                for ax in fig.axes:
                    assert ax.get_xlim() == pytest.approx((0, ceiling))
                    assert len(ax.patches) == 10
                    assert colors.to_hex(ax.get_facecolor()) == birth.WARM.lower()
                    assert all(colors.to_hex(bar.get_facecolor()) == birth.TEAL.lower() for bar in ax.patches)
                    assert 'births' in ax.get_xlabel().lower() and '1,000' in ax.get_xlabel()
                    assert 'woman' not in ax.get_xlabel().lower()
                    displayed_ranks.extend(int(label.get_text().split()[0]) for label in ax.get_yticklabels())
        assert displayed_ranks == list(range(1, 101))
    finally:
        for fig in figures:
            plt.close(fig)

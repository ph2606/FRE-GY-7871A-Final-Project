"""Regression test for detecting altered immutable macro cache payloads."""
import importlib.util
from pathlib import Path
import json
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('economic_collector',ROOT/'scripts/01_collect_economics.py')
collector=importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


def test_macro_cache_reuse_verifies_bytes_and_request(tmp_path):
    path=tmp_path/'vintage.csv'
    path.write_text('observation_date,TEST_20261001\n2026-08-01,3.4\n',encoding='utf-8')
    metadata={'url':'https://example.invalid/vintage','sha256':collector.sha256(path)}
    path.with_suffix('.csv.meta.json').write_text(json.dumps(metadata),encoding='utf-8')
    assert collector.acquire(metadata['url'],path)==metadata
    with pytest.raises(ValueError,match='URL mismatch'):
        collector.acquire('https://example.invalid/different',path)
    path.write_text('altered bytes',encoding='utf-8')
    with pytest.raises(ValueError,match='hash mismatch'):
        collector.acquire(metadata['url'],path)

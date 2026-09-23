import csv
import importlib.util
import json
from pathlib import Path

import pytest
from translate.storage import csvl10n, tbx

spec = importlib.util.spec_from_file_location('exports', Path(__file__).resolve().parents[1] / 'scripts/exports.py')
exports = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exports)


@pytest.fixture
def rows():
    return [{'source': 'Save <file> & "name",\r\nnext', 'canonical': 'Spara <fil> & "namn",\r\nnästa', 'confidence': '0.9'}]


def test_tbx_roundtrip_in_real_consumer(tmp_path, rows):
    path = tmp_path / 'terms.tbx'
    exports.write_tbx(rows, path)
    assert exports.validate_tbx(rows, path) == 1
    with path.open('rb') as stream:
        store = tbx.tbxfile(stream, sourcelanguage='en', targetlanguage='sv')
    assert [(str(u.source), str(u.target)) for u in store.units] == [(rows[0]['source'], rows[0]['canonical'])]


def test_weblate_csv_roundtrip(tmp_path, rows):
    path = tmp_path / 'glossary.csv'
    glossary = {rows[0]['source']: {'note': 'Konfidensgrad: 90.0%, Domänvarianter: ui'}}
    exports.write_weblate(rows, glossary, path)
    with path.open(encoding='utf-8', newline='') as stream:
        data = list(csv.DictReader(stream))
    assert data == [{'source': rows[0]['source'], 'target': rows[0]['canonical'], 'developer_comments': glossary[rows[0]['source']]['note']}]
    with path.open('rb') as stream:
        store = csvl10n.csvfile(stream)
    assert [(str(u.source), str(u.target)) for u in store.units] == [(rows[0]['source'], rows[0]['canonical'])]


@pytest.mark.parametrize('confidence', ['90', '-1', 'nan', 'inf', ''])
def test_invalid_confidence_rejected(tmp_path, confidence):
    path = tmp_path / 'terms.csv'
    path.write_text(f'source,canonical,confidence\nSave,Spara,{confidence}\n', encoding='utf-8')
    with pytest.raises(ValueError):
        exports.load_rows(path)


def test_duplicate_source_rejected(tmp_path):
    path = tmp_path / 'terms.csv'
    path.write_text('source,canonical,confidence\nSave,Spara,1\nSave,Spara,1\n', encoding='utf-8')
    with pytest.raises(ValueError, match='duplicate'):
        exports.load_rows(path)


def test_tbx_language_attributes_are_checked(tmp_path, rows):
    path = tmp_path / 'terms.tbx'
    exports.write_tbx(rows, path)
    path.write_text(path.read_text().replace('xml:lang="sv"', 'lang="sv"'))
    with pytest.raises(ValueError, match='xml:lang sections'):
        exports.validate_tbx(rows, path)


def test_tbx_translation_mismatch_rejected(tmp_path, rows):
    path = tmp_path / 'terms.tbx'
    exports.write_tbx(rows, path)
    path.write_text(path.read_text().replace('Spara', 'Ta bort'))
    with pytest.raises(ValueError, match='mismatch'):
        exports.validate_tbx(rows, path)


def test_json_translation_mismatch_rejected(tmp_path, rows):
    path = tmp_path / 'terms.json'
    path.write_text(json.dumps([{'source': rows[0]['source'], 'target': 'Fel', 'note': 'Konfidensgrad: 90.0%'}]))
    with pytest.raises(ValueError, match='mismatch'):
        exports.load_glossary(path, rows)


def test_xml_invalid_characters_are_not_silently_lost():
    with pytest.raises(ValueError, match='U\\+000B'):
        exports.xml_text('text\x0bmore text')


def test_xml_incompatible_terms_are_reported_without_changing_them(tmp_path, rows):
    excluded = {'source': 'Escape\x1b', 'canonical': 'Escape\x1b', 'confidence': '1.0'}
    path = tmp_path / 'terms.tbx'
    exports.write_tbx(rows + [excluded], path)
    assert exports.validate_tbx(rows + [excluded], path) == 1
    report = json.loads(path.with_suffix('.excluded.json').read_text())
    assert report[0]['source'] == excluded['source']
    assert report[0]['canonical'] == excluded['canonical']
    path.with_suffix('.excluded.json').write_text('[]')
    with pytest.raises(ValueError, match='exclusion report'):
        exports.validate_tbx(rows + [excluded], path)


def test_write_glossary_synchronizes_canonical_data_and_preserves_metadata(tmp_path, rows):
    path = tmp_path / 'glossary.json'
    glossary = {rows[0]['source']: {
        'source': rows[0]['source'], 'target': 'Gammal', 'flag': 'terminology',
        'note': 'Konfidensgrad: 90.0%, Domänvarianter: ui',
    }}
    exports.write_glossary(rows, glossary, path)
    assert json.loads(path.read_text()) == [{
        'source': rows[0]['source'], 'target': rows[0]['canonical'], 'flag': 'terminology',
        'note': 'Konfidensgrad: 90.0%, Domänvarianter: ui',
    }]


def test_review_note_is_preserved_in_tbx(tmp_path):
    rows = [{'source': 'Figured Bass', 'canonical': 'Generalbas', 'confidence': '1.0'}]
    path = tmp_path / 'terms.tbx'
    glossary = {'Figured Bass': {'review_note': 'Historical confidence; corrected term.'}}
    exports.write_tbx(rows, path, glossary)
    import xml.etree.ElementTree as ET
    notes = [n.text for n in ET.parse(path).findall('.//note')]
    assert 'Historical confidence; corrected term.' in notes
    assert exports.validate_tbx(rows, path, glossary) == 1
    path.write_text(path.read_text().replace('Historical confidence; corrected term.', 'Lost context.'))
    with pytest.raises(ValueError, match='review note mismatch'):
        exports.validate_tbx(rows, path, glossary)

def test_sync_can_add_a_term_before_tbx_and_weblate_exports(tmp_path, monkeypatch):
    root = tmp_path
    (root / 'termbank-flat.csv').write_text(
        'source,canonical,confidence\nSave,Spara,1.0\n', encoding='utf-8')
    (root / 'weblate-glossary.json').write_text('[]\n', encoding='utf-8')
    tbx_path = root / 'terms.tbx'
    weblate_path = root / 'terms.csv'
    monkeypatch.setattr('sys.argv', ['exports.py', '--root', str(root), '--tbx', str(tbx_path),
                                     '--glossary-json', str(root / 'weblate-glossary.json'),
                                     '--weblate', str(weblate_path)])
    assert exports.main() == 0
    assert json.loads((root / 'weblate-glossary.json').read_text())[0]['target'] == 'Spara'
    assert exports.validate_tbx(exports.load_rows(root / 'termbank-flat.csv'), tbx_path,
                                exports.load_glossary(root / 'weblate-glossary.json', exports.load_rows(root / 'termbank-flat.csv'))) == 1

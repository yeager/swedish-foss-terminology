#!/usr/bin/env python3
"""Validate terminology exports and generate interoperable TBX/Weblate CSV."""
import argparse
import csv
import json
import math
from pathlib import Path
import sys
import tempfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'


def load_rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ['source', 'canonical', 'confidence']:
            raise ValueError('unexpected CSV columns')
        rows = list(reader)
    seen = set()
    for row in rows:
        if None in row or not row['source'] or not row['canonical']:
            raise ValueError('empty or malformed CSV row')
        if row['source'] in seen:
            raise ValueError(f'duplicate source: {row["source"]!r}')
        seen.add(row['source'])
        value = float(row['confidence'])
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError('confidence must be a finite ratio between 0 and 1')
    if not rows:
        raise ValueError('empty termbank')
    return rows


def confidence_note(row):
    return f'Konfidensgrad: {float(row["confidence"]):.1%}'


def xml_text(text):
    # Literal CR is normalized to LF by XML parsers, unlike a character reference.
    for char in text:
        n = ord(char)
        if not (n in (9, 10, 13) or 0x20 <= n <= 0xD7FF or 0xE000 <= n <= 0xFFFD or 0x10000 <= n <= 0x10FFFF):
            raise ValueError(f'character U+{n:04X} cannot be represented in XML 1.0')
    return escape(text, {'\r': '&#13;', '\n': '&#10;', '\t': '&#9;'})


def tbx_exclusions(rows):
    excluded = []
    for row in rows:
        try:
            xml_text(row['source'])
            xml_text(row['canonical'])
        except ValueError as error:
            excluded.append({**row, 'reason': str(error)})
    return excluded


def write_tbx(rows, path, glossary=None):
    excluded = tbx_exclusions(rows)
    excluded_sources = {row['source'] for row in excluded}
    # Complete the export before replacing an existing usable file.
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                     dir=path.parent, delete=False) as out:
        temporary = Path(out.name)
        try:
            out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            out.write('<martif type="TBX" xml:lang="en">\n<martifHeader><fileDesc>')
            out.write('<titleStmt><title>Swedish FOSS Terminology</title></titleStmt>')
            out.write('<sourceDesc><p>Generated from termbank-flat.csv</p></sourceDesc>')
            out.write('</fileDesc></martifHeader>\n<text><body>\n')
            for index, row in enumerate(rows, 1):
                if row['source'] in excluded_sources:
                    continue
                out.write(f'<termEntry id="term_{index}">')
                for lang, field in [('en', 'source'), ('sv', 'canonical')]:
                    out.write(f'<langSet xml:lang="{lang}"><tig><term>{xml_text(row[field])}</term>')
                    if lang == 'sv':
                        out.write(f'<note>{confidence_note(row)}</note>')
                        if glossary and glossary[row['source']].get('review_note'):
                            out.write('<note>'+xml_text(glossary[row['source']]['review_note'])+'</note>')
                    out.write('</tig></langSet>')
                out.write('</termEntry>\n')
            out.write('</body></text></martif>\n')
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    temporary.replace(path)
    path.with_suffix('.excluded.json').write_text(
        json.dumps(excluded, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_glossary(path, rows, allow_missing=False):
    entries = json.loads(path.read_text(encoding='utf-8'))
    by_source = {}
    for entry in entries:
        if entry['source'] in by_source:
            raise ValueError('duplicate JSON source')
        by_source[entry['source']] = entry
    expected_sources = {r['source'] for r in rows}
    missing = expected_sources - set(by_source)
    extra = set(by_source) - expected_sources
    if extra or (missing and not allow_missing):
        raise ValueError('CSV/JSON source mismatch')
    for row in rows:
        entry = by_source.get(row['source'])
        if entry is not None and not allow_missing and (entry['target'] != row['canonical'] or not entry['note'].startswith(confidence_note(row))):
            raise ValueError(f'CSV/JSON mismatch for {row["source"]!r}')
    return by_source


def write_glossary(rows, glossary, path):
    """Synchronize the JSON export to the canonical CSV, preserving metadata."""
    canonical_rows = {row['source']: row for row in rows}
    synchronized = []
    for row in rows:
        source = row['source']
        entry = glossary.get(source)
        if entry is None:
            synchronized.append({
                'source': source,
                'target': row['canonical'],
                'flag': 'terminology',
                'note': confidence_note(row) + ', Granskad term: 2026-09-20',
            })
            continue
        entry = dict(entry)
        suffix = entry['note'][len(confidence_note(row)):]
        entry['target'] = row['canonical']
        entry['note'] = confidence_note(row) + suffix
        synchronized.append(entry)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n',
                                     dir=path.parent, delete=False) as out:
        temporary = Path(out.name)
        try:
            json.dump(synchronized, out, ensure_ascii=False, indent=2)
            out.write('\n')
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    temporary.replace(path)


def write_weblate(rows, glossary, path):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['source', 'target', 'developer_comments'])
        writer.writeheader()
        for row in rows:
            writer.writerow({'source': row['source'], 'target': row['canonical'],
                             'developer_comments': glossary[row['source']]['note']})


def validate_tbx(rows, path, glossary=None):
    excluded = tbx_exclusions(rows)
    if json.loads(path.with_suffix('.excluded.json').read_text(encoding='utf-8')) != excluded:
        raise ValueError('TBX exclusion report does not match CSV')
    excluded_sources = {r['source'] for r in excluded}
    expected = {r['source']: r for r in rows if r['source'] not in excluded_sources}
    seen, ids, stack = set(), set(), []
    for event, element in ET.iterparse(path, events=('start', 'end')):
        if event == 'start':
            stack.append(element)
            if len(stack) == 1 and (element.tag != 'martif' or element.get('type') != 'TBX' or element.get(XML_LANG) != 'en'):
                raise ValueError('expected TBX 2008 martif root with xml:lang="en"')
            continue
        if element.tag == 'termEntry':
            if [node.tag for node in stack[:-1]] != ['martif', 'text', 'body']:
                raise ValueError('term outside TBX body')
            term_id = element.get('id')
            if not term_id or term_id in ids:
                raise ValueError('missing or duplicate term ID')
            ids.add(term_id)
            langs = element.findall('langSet')
            if len(langs) != 2 or {lang.get(XML_LANG) for lang in langs} != {'en', 'sv'}:
                raise ValueError('term must have exactly en and sv xml:lang sections')
            terms = {lang.get(XML_LANG): lang.findtext('tig/term') for lang in langs}
            source = terms['en']
            if source not in expected or source in seen or terms['sv'] != expected[source]['canonical']:
                raise ValueError(f'CSV/TBX mismatch for {source!r}')
            note = element.findtext(f"langSet[@{XML_LANG}='sv']/tig/note")
            if note != confidence_note(expected[source]):
                raise ValueError('CSV/TBX confidence mismatch')
            if glossary is not None:
                expected_notes=[confidence_note(expected[source])]
                if glossary[source].get('review_note'):
                    expected_notes.append(glossary[source]['review_note'])
                actual_notes=[x.text for x in element.findall(f"langSet[@{XML_LANG}='sv']/tig/note")]
                if actual_notes != expected_notes:
                    raise ValueError('JSON/TBX review note mismatch')
            seen.add(source)
            stack[-2].remove(element)
        stack.pop()
    if seen != set(expected):
        raise ValueError('TBX is missing terms')
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--tbx', type=Path, help='generate TBX 2008 at this path')
    parser.add_argument('--weblate', type=Path, help='generate Weblate CSV at this path')
    parser.add_argument('--glossary-json', type=Path, help='synchronize JSON glossary at this path')
    args = parser.parse_args()
    try:
        rows = load_rows(args.root / 'termbank-flat.csv')
        glossary = load_glossary(args.root / 'weblate-glossary.json', rows, allow_missing=bool(args.glossary_json))
        if args.tbx:
            write_tbx(rows, args.tbx, glossary)
        if args.glossary_json:
            write_glossary(rows, glossary, args.glossary_json)
        if args.weblate:
            write_weblate(rows, glossary, args.weblate)
        count = validate_tbx(rows, args.tbx or args.root / 'swedish-foss.tbx', glossary)
    except (OSError, ValueError, KeyError, TypeError, csv.Error, ET.ParseError) as error:
        print(error, file=sys.stderr)
        return 1
    print(f'{len(rows)} CSV/JSON terms; {count} matching TBX terms; '
          f'{len(rows) - count} XML-incompatible terms retained in the exclusion report (confidence: 0–1).')
    return 0


if __name__ == '__main__':
    sys.exit(main())

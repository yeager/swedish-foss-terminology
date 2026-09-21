#!/usr/bin/env python3
"""Export project-specific review terms to CSV/TBX and verify round-trip metadata."""
from __future__ import annotations
import argparse,csv,json,sys,collections
from pathlib import Path
import xml.etree.ElementTree as ET
from exports import xml_text
ROOT=Path(__file__).resolve().parents[1]
LANG='{http://www.w3.org/XML/1998/namespace}lang'
FIELDS=['id','source','canonical','project','component','context','note','scope','review_id','publication_status','reference','evidence_sha256','source_evidence']

def load(path):
    rows=[json.loads(x) for x in path.read_text(encoding='utf-8').split('\n') if x]
    ids=set()
    for r in rows:
        for k in ['id','source','canonical','project','component','context','note','scope','review_id','publication_status']:
            if not isinstance(r.get(k),str):raise ValueError(f'{path}: invalid {k}')
        if not r['source'] or not r['canonical'] or r['id'] in ids:raise ValueError('empty or duplicate term')
        ids.add(r['id'])
        if r['scope']!='project-context':raise ValueError('reviewed terms must retain project scope')
        if not r.get('evidence',{}).get('artifact') or not r['evidence'].get('sha256'):raise ValueError('missing evidence')
    return rows

def flat(r):
    return {k:r[k] for k in FIELDS if k in r}|{'reference':r['evidence']['artifact'],'evidence_sha256':r['evidence']['sha256'],'source_evidence':json.dumps(r.get('source_evidence',{}),ensure_ascii=False,separators=(',',':'))}

def write(rows,path):
    with path.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS,lineterminator='\n');writer.writeheader();writer.writerows(flat(r) for r in rows)
    with path.with_suffix('.tbx').open('w',encoding='utf-8',newline='\n') as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n<martif type="TBX" xml:lang="en"><martifHeader><fileDesc><titleStmt><title>Swedish project-specific review terms</title></titleStmt><sourceDesc><p>Generated from reviewed/data JSONL; recommendations require matching project context.</p></sourceDesc></fileDesc></martifHeader><text><body>\n')
        for r in rows:
            out.write(f'<termEntry id="r{r["id"]}">')
            for lang,key in [('en','source'),('sv','canonical')]:out.write(f'<langSet xml:lang="{lang}"><tig><term>{xml_text(r[key])}</term></tig></langSet>')
            # Preserve all provenance and sense data in interoperable TBX notes.
            out.write('<note>'+xml_text(json.dumps(flat(r),ensure_ascii=False,separators=(',',':'))))
            out.write('</note></termEntry>\n')
        out.write('</body></text></martif>\n')

def validate(rows,path):
    expected=[flat(r) for r in rows]
    with path.open(encoding='utf-8',newline='') as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=FIELDS or list(reader)!=expected:raise ValueError(f'{path}: CSV mismatch')
    tree=ET.parse(path.with_suffix('.tbx'));actual=[]
    for term in tree.findall('.//termEntry'):
        sets=term.findall('langSet')
        if len(sets)!=2 or {x.get(LANG) for x in sets}!={'en','sv'}:raise ValueError('invalid TBX language pair')
        pair={x.get(LANG):x.findtext('./tig/term') for x in sets}
        r=json.loads(term.findtext('note'))
        if pair!={'en':r['source'],'sv':r['canonical']} or term.get('id')!='r'+r['id']:raise ValueError('TBX term/metadata mismatch')
        actual.append(r)
    if actual!=expected:raise ValueError(f'{path}: TBX mismatch')
    return len(rows)

def run(root=ROOT,generate=False):
    out=root/'reviewed'/'glossaries';out.mkdir(parents=True,exist_ok=True);counts={}
    for p in sorted((root/'reviewed'/'data').glob('*.jsonl')):
        rows=load(p);csv_path=out/(p.stem+'.csv')
        if generate:write(rows,csv_path)
        counts[p.stem]=validate(rows,csv_path)
    if not counts:raise ValueError('no review terms')
    stats={'terms':sum(counts.values()),'glossaries':counts};path=root/'reviewed'/'stats.json'
    if generate:path.write_text(json.dumps(stats,indent=2)+'\n')
    elif json.loads(path.read_text())!=stats:raise ValueError('stale review statistics')
    return stats
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    try:print(json.dumps(run(generate=args.write),indent=2))
    except ValueError as e:print(e,file=sys.stderr);sys.exit(1)

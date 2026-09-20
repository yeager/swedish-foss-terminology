import sys,json
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import reviewed

def row(n,target,context):
    return {'id':n,'source':'face','canonical':target,'project':'Example','component':'editor','context':context,'note':'A & B\nquoted "text"','scope':'project-context','review_id':n,'publication_status':'reviewed-local','evidence':{'artifact':'https://example.org/source','sha256':'a'*64},'source_evidence':{'artifact':'https://example.org/api/1','sha256':'b'*64}}

def test_senses_and_metadata_roundtrip(tmp_path):
    rows=[row('one','yta','geometry'),row('two','ansikte','portrait')];path=tmp_path/'terms.csv'
    reviewed.write(rows,path)
    assert reviewed.validate(rows,path)==2

def test_rejects_lost_context(tmp_path):
    rows=[row('one','yta','geometry')];path=tmp_path/'terms.csv';reviewed.write(rows,path)
    tbx=path.with_suffix('.tbx');tbx.write_text(tbx.read_text().replace('geometry','portrait'))
    with pytest.raises(ValueError,match='mismatch'):reviewed.validate(rows,path)

def test_rejects_global_review_scope(tmp_path):
    r=row('one','yta','geometry');r['scope']='global';path=tmp_path/'terms.jsonl';path.write_text(json.dumps(r)+'\n')
    with pytest.raises(ValueError,match='scope'):reviewed.load(path)

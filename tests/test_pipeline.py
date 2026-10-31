import sqlite3,pytest
from scripts.generate_data import generate
from src.pipeline import run_pipeline,CUSTOMER_COLUMNS

def test_happy_path_and_rejects(tmp_path):
    raw=tmp_path/'raw'; generate(raw,10,20,7,True); m=run_pipeline(raw/'customers.csv',raw/'orders.csv',tmp_path/'db.sqlite',tmp_path/'out')
    assert m['status']=='success' and m['customer_inserted']==10 and m['order_inserted']==20 and m['rejected']>=7
    con=sqlite3.connect(tmp_path/'db.sqlite'); assert con.execute('select count(*) from customers').fetchone()[0]==10; assert con.execute('select count(*) from orders').fetchone()[0]==20; assert con.execute('select count(*) from rejects').fetchone()[0]==m['rejected']; con.close()

def test_idempotent_rerun(tmp_path):
    raw=tmp_path/'raw'; generate(raw,5,8,3,False); db=tmp_path/'db.sqlite'; out=tmp_path/'out'
    a=run_pipeline(raw/'customers.csv',raw/'orders.csv',db,out); b=run_pipeline(raw/'customers.csv',raw/'orders.csv',db,out)
    assert (a['customer_inserted'],a['order_inserted'])==(5,8); assert (b['customer_inserted'],b['order_inserted'])==(0,0)
    con=sqlite3.connect(db); assert con.execute('select count(*) from orders').fetchone()[0]==8; con.close()

def test_empty_batch(tmp_path):
    raw=tmp_path/'raw'; raw.mkdir(); (raw/'customers.csv').write_text(','.join(CUSTOMER_COLUMNS)+'\n'); (raw/'orders.csv').write_text('order_id,customer_id,order_timestamp,amount,currency,status\n')
    m=run_pipeline(raw/'customers.csv',raw/'orders.csv',tmp_path/'db.sqlite',tmp_path/'out'); assert m['customer_input']==m['order_input']==m['rejected']==0

def test_schema_drift_fails_fast(tmp_path):
    raw=tmp_path/'raw'; raw.mkdir(); (raw/'customers.csv').write_text('customer_id,first_name,email\n'); (raw/'orders.csv').write_text('order_id,customer_id,order_timestamp,amount,currency,status\n')
    with pytest.raises(ValueError,match='Unexpected schema'): run_pipeline(raw/'customers.csv',raw/'orders.csv',tmp_path/'db.sqlite',tmp_path/'out')

def test_malformed_record_quarantined(tmp_path):
    raw=tmp_path/'raw'; generate(raw,3,5,11,False)
    with (raw/'orders.csv').open('a') as f: f.write('BROKEN,ROW\n')
    m=run_pipeline(raw/'customers.csv',raw/'orders.csv',tmp_path/'db.sqlite',tmp_path/'out'); assert m['rejected']==1
    con=sqlite3.connect(tmp_path/'db.sqlite'); assert con.execute('select reason from rejects').fetchone()[0]=='malformed_column_count'; con.close()

def test_domain_edge_cases(tmp_path):
    raw=tmp_path/'raw'; generate(raw,4,3,12,False)
    with (raw/'orders.csv').open('a') as f:
        f.write('O_ZERO,C000001,2025-01-01T00:00:00Z,0,USD,paid\n'); f.write('O_STATUS,C000001,2025-01-01T00:00:00Z,10,USD,unknown\n')
    m=run_pipeline(raw/'customers.csv',raw/'orders.csv',tmp_path/'db.sqlite',tmp_path/'out'); assert m['rejected']==2

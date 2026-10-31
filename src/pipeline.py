from __future__ import annotations
import argparse, csv, hashlib, json, logging, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pandas as pd

CUSTOMER_COLUMNS = ["customer_id", "first_name", "last_name", "email", "created_at"]
ORDER_COLUMNS = ["order_id", "customer_id", "order_timestamp", "amount", "currency", "status"]
ALLOWED_STATUS = {"pending", "paid", "shipped", "cancelled", "refunded"}

def utc_now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def read_csv(path: Path, expected: list[str]):
    rejects=[]; path=Path(path)
    if not path.exists(): raise FileNotFoundError(path)
    with path.open('r',newline='',encoding='utf-8-sig') as f:
        reader=csv.reader(f)
        try: header=next(reader)
        except StopIteration: return pd.DataFrame(columns=expected),[],[]
        if header != expected: raise ValueError(f"Unexpected schema in {path.name}. Expected {expected}; got {header}")
        rows=[]; source_lines=[]
        for line,row in enumerate(reader,start=2):
            if len(row)!=len(expected): rejects.append({"source_file":path.name,"source_line":line,"record":json.dumps(row),"reason":"malformed_column_count"})
            else: rows.append(dict(zip(expected,row))); source_lines.append(line)
    return pd.DataFrame(rows,columns=expected,index=source_lines),rejects,header

def reject_record(source,line,record,reason):
    return {"source_file":source,"source_line":line,"record":json.dumps(record,default=str),"reason":reason}

def validate_customers(df,source):
    accepted=[]; rejects=[]; seen=set()
    for idx,values in zip(df.index,df.itertuples(index=False,name=None)):
        rec=dict(zip(df.columns,values)); line=idx; cid=str(rec["customer_id"]).strip()
        if not cid or cid.lower() in ('nan','none'):
            rejects.append(reject_record(source,line,rec,'null_customer_id')); continue
        if cid in seen:
            rejects.append(reject_record(source,line,rec,'duplicate_customer_id')); continue
        seen.add(cid); email=str(rec["email"]).strip().lower()
        if not email or '@' not in email or email.startswith('@') or email.endswith('@'):
            rejects.append(reject_record(source,line,rec,'invalid_email')); continue
        try: created=pd.to_datetime(rec["created_at"],utc=True,errors='raise').isoformat()
        except Exception:
            rejects.append(reject_record(source,line,rec,'invalid_created_at')); continue
        if not str(rec["first_name"]).strip() or not str(rec["last_name"]).strip():
            rejects.append(reject_record(source,line,rec,'missing_customer_name')); continue
        accepted.append({"customer_id":cid,"first_name":str(rec["first_name"]).strip(),"last_name":str(rec["last_name"]).strip(),"email":email,"created_at":created})
    return pd.DataFrame(accepted,columns=CUSTOMER_COLUMNS),rejects

def validate_orders(df,source,valid_customer_ids):
    accepted=[]; rejects=[]; seen=set()
    for idx,values in zip(df.index,df.itertuples(index=False,name=None)):
        rec=dict(zip(df.columns,values)); line=idx; oid=str(rec["order_id"]).strip(); cid=str(rec["customer_id"]).strip()
        if not oid or oid.lower() in ('nan','none'):
            rejects.append(reject_record(source,line,rec,'null_order_id')); continue
        if oid in seen:
            rejects.append(reject_record(source,line,rec,'duplicate_order_id')); continue
        seen.add(oid)
        if not cid or cid.lower() in ('nan','none'):
            rejects.append(reject_record(source,line,rec,'null_customer_id')); continue
        if cid not in valid_customer_ids:
            rejects.append(reject_record(source,line,rec,'unknown_customer_id')); continue
        try: ts=pd.to_datetime(rec["order_timestamp"],utc=True,errors='raise')
        except Exception:
            rejects.append(reject_record(source,line,rec,'invalid_order_timestamp')); continue
        try: amount=float(rec["amount"])
        except Exception:
            rejects.append(reject_record(source,line,rec,'invalid_amount')); continue
        if amount<=0:
            rejects.append(reject_record(source,line,rec,'non_positive_amount')); continue
        currency=str(rec["currency"]).strip().upper()
        if len(currency)!=3 or not currency.isalpha():
            rejects.append(reject_record(source,line,rec,'invalid_currency')); continue
        status=str(rec["status"]).strip().lower()
        if status not in ALLOWED_STATUS:
            rejects.append(reject_record(source,line,rec,'invalid_status')); continue
        accepted.append({"order_id":oid,"customer_id":cid,"order_timestamp":ts.isoformat(),"order_date":ts.date().isoformat(),"amount":round(amount,2),"currency":currency,"status":status})
    return pd.DataFrame(accepted,columns=ORDER_COLUMNS+['order_date']),rejects

def init_db(conn):
    conn.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS customers(customer_id TEXT PRIMARY KEY,first_name TEXT NOT NULL,last_name TEXT NOT NULL,email TEXT NOT NULL,created_at TEXT NOT NULL,source_file TEXT NOT NULL,run_id TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS orders(order_id TEXT PRIMARY KEY,customer_id TEXT NOT NULL REFERENCES customers(customer_id),order_timestamp TEXT NOT NULL,order_date TEXT NOT NULL,amount REAL NOT NULL CHECK(amount>0),currency TEXT NOT NULL,status TEXT NOT NULL,source_file TEXT NOT NULL,run_id TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS rejects(reject_id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT NOT NULL,source_file TEXT NOT NULL,source_line INTEGER,record TEXT NOT NULL,reason TEXT NOT NULL,rejected_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS pipeline_runs(run_id TEXT PRIMARY KEY,started_at TEXT NOT NULL,ended_at TEXT,status TEXT NOT NULL,customer_input INTEGER DEFAULT 0,order_input INTEGER DEFAULT 0,customer_output INTEGER DEFAULT 0,order_output INTEGER DEFAULT 0,rejected_count INTEGER DEFAULT 0,customer_file_hash TEXT,order_file_hash TEXT,error TEXT);
    CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
    CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
    """)

def run_pipeline(customers_path,orders_path,db_path,output_dir):
    customers_path,orders_path,db_path,output_dir=map(Path,(customers_path,orders_path,db_path,output_dir))
    output_dir.mkdir(parents=True,exist_ok=True); db_path.parent.mkdir(parents=True,exist_ok=True)
    run_id=str(uuid.uuid4()); started=utc_now(); logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    conn=sqlite3.connect(db_path)
    try:
        init_db(conn); conn.execute('INSERT INTO pipeline_runs(run_id,started_at,status) VALUES(?,?,?)',(run_id,started,'running')); conn.commit()
        c_raw,c_bad,_=read_csv(customers_path,CUSTOMER_COLUMNS); o_raw,o_bad,_=read_csv(orders_path,ORDER_COLUMNS)
        c_ok,c_rej=validate_customers(c_raw,customers_path.name)
        existing={r[0] for r in conn.execute('SELECT customer_id FROM customers')}; valid_ids=existing|set(c_ok.customer_id.astype(str))
        o_ok,o_rej=validate_orders(o_raw,orders_path.name,valid_ids); rejects=c_bad+o_bad+c_rej+o_rej
        c_insert=o_insert=0
        with conn:
            for row in c_ok.to_dict('records'):
                cur=conn.execute('INSERT OR IGNORE INTO customers VALUES(?,?,?,?,?,?,?)',tuple(row[k] for k in CUSTOMER_COLUMNS)+(customers_path.name,run_id)); c_insert+=cur.rowcount
            for row in o_ok.to_dict('records'):
                cur=conn.execute('INSERT OR IGNORE INTO orders VALUES(?,?,?,?,?,?,?,?,?)',tuple(row[k] for k in ORDER_COLUMNS+['order_date'])+(orders_path.name,run_id)); o_insert+=cur.rowcount
            for r in rejects:
                conn.execute('INSERT INTO rejects(run_id,source_file,source_line,record,reason,rejected_at) VALUES(?,?,?,?,?,?)',(run_id,r['source_file'],r['source_line'],r['record'],r['reason'],utc_now()))
            conn.execute("UPDATE pipeline_runs SET ended_at=?,status='success',customer_input=?,order_input=?,customer_output=?,order_output=?,rejected_count=?,customer_file_hash=?,order_file_hash=? WHERE run_id=?",(utc_now(),len(c_raw)+len(c_bad),len(o_raw)+len(o_bad),c_insert,o_insert,len(rejects),sha256(customers_path),sha256(orders_path),run_id))
        pd.read_sql_query('SELECT * FROM customers ORDER BY customer_id',conn).to_csv(output_dir/'dim_customers.csv',index=False)
        pd.read_sql_query('SELECT * FROM orders ORDER BY order_id',conn).to_csv(output_dir/'fact_orders.csv',index=False)
        pd.read_sql_query('SELECT reason,COUNT(*) AS rejected_rows FROM rejects WHERE run_id=? GROUP BY reason ORDER BY reason',conn,params=(run_id,)).to_csv(output_dir/f'reject_summary_{run_id[:8]}.csv',index=False)
        metrics={"run_id":run_id,"status":"success","started_at":started,"customer_input":len(c_raw)+len(c_bad),"order_input":len(o_raw)+len(o_bad),"customer_inserted":c_insert,"order_inserted":o_insert,"rejected":len(rejects),"customer_file_sha256":sha256(customers_path),"order_file_sha256":sha256(orders_path),"database":str(db_path)}
        (output_dir/f'run_{run_id[:8]}.json').write_text(json.dumps(metrics,indent=2)); logging.info('Run %s completed: %s',run_id,metrics); return metrics
    except Exception as exc:
        conn.execute("UPDATE pipeline_runs SET ended_at=?,status='failed',error=? WHERE run_id=?",(utc_now(),str(exc),run_id)); conn.commit(); logging.exception('Pipeline run %s failed',run_id); raise
    finally: conn.close()

def main():
    p=argparse.ArgumentParser(description='YottaFlex CSV batch pipeline'); p.add_argument('--customers',default='data/raw/customers.csv'); p.add_argument('--orders',default='data/raw/orders.csv'); p.add_argument('--db',default='output/warehouse.db'); p.add_argument('--output',default='output'); a=p.parse_args()
    print(json.dumps(run_pipeline(a.customers,a.orders,a.db,a.output),indent=2))
if __name__=='__main__': main()

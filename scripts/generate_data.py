import argparse,csv,random
from pathlib import Path
from datetime import datetime,timedelta,timezone

def generate(out:Path,customers=100,orders=500,seed=42,include_bad=True):
    random.seed(seed); out.mkdir(parents=True,exist_ok=True); cp=out/'customers.csv'; op=out/'orders.csv'
    with cp.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['customer_id','first_name','last_name','email','created_at'])
        for i in range(1,customers+1): w.writerow([f'C{i:06d}',f'First{i}',f'Last{i}',f'user{i}@example.com',(datetime(2024,1,1,tzinfo=timezone.utc)+timedelta(days=i%600)).isoformat()])
        if include_bad and customers>=3:
            w.writerow(['','Null','Key','null@example.com','2024-01-01T00:00:00Z']); w.writerow(['C000001','Duplicate','Customer','dup@example.com','2024-01-01T00:00:00Z']); w.writerow(['C_BAD','Bad','Email','not-an-email','2024-01-01T00:00:00Z'])
    with op.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['order_id','customer_id','order_timestamp','amount','currency','status'])
        for i in range(1,orders+1):
            cid=f'C{random.randint(1,max(customers,1)):06d}'; dt=datetime(2025,1,1,tzinfo=timezone.utc)+timedelta(minutes=i*17)
            w.writerow([f'O{i:08d}',cid,dt.isoformat(),f'{random.uniform(5,500):.2f}','USD',random.choice(['paid','shipped','pending','cancelled'])])
        if include_bad and orders>=5:
            w.writerow(['','C000001','2025-01-01T00:00:00Z','10','USD','paid']); w.writerow(['O00000001','C000001','2025-01-01T00:00:00Z','10','USD','paid']); w.writerow(['O_BAD','C999999','2025-01-01T00:00:00Z','10','USD','paid']); w.writerow(['O_NEG','C000001','2025-01-01T00:00:00Z','-4','USD','paid']); w.writerow(['O_BAD_DATE','C000001','not-a-date','20','USD','paid']); w.writerow(['O_MALFORMED','C000001','2025-01-01T00:00:00Z','20'])
    return cp,op
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--customers',type=int,default=100); p.add_argument('--orders',type=int,default=500); p.add_argument('--seed',type=int,default=42); p.add_argument('--out',default='data/raw'); p.add_argument('--clean',action='store_true'); a=p.parse_args()
    print(generate(Path(a.out),a.customers,a.orders,a.seed,not a.clean))

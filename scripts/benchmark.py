"""Generate a clean synthetic workload and measure end-to-end pipeline runtime."""
import argparse,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.generate_data import generate
from src.pipeline import run_pipeline

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--customers',type=int,default=10000); p.add_argument('--orders',type=int,default=100000); p.add_argument('--workdir',default='benchmark_run'); a=p.parse_args()
    root=Path(a.workdir); raw=root/'raw'; out=root/'output'; start=time.perf_counter()
    generate(raw,a.customers,a.orders,seed=42,include_bad=False); generated=time.perf_counter()
    metrics=run_pipeline(raw/'customers.csv',raw/'orders.csv',out/'warehouse.db',out); finished=time.perf_counter()
    print({'customers':a.customers,'orders':a.orders,'generation_seconds':round(generated-start,3),'pipeline_seconds':round(finished-generated,3),'total_seconds':round(finished-start,3),'inserted_orders':metrics['order_inserted']})

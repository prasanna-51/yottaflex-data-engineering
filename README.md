\# YottaFlex AI – Batch Customer and Order Data Pipeline



A Python-based batch data engineering pipeline that ingests customer and order CSV files, validates schemas and business rules, transforms records, and publishes curated outputs to SQLite and CSV files. Invalid records are quarantined with rejection reasons and source lineage.



\## 1. Architecture



```text

Customer CSV --------\\

&#x20;                     \\

&#x20;                      -> Schema Validation

&#x20;                     /          |

Order CSV -----------/           v

&#x20;                          Data Validation

&#x20;                                 |

&#x20;                                 v

&#x20;                        Transformation

&#x20;                                 |

&#x20;                   +-------------+-------------+

&#x20;                   |                           |

&#x20;                   v                           v

&#x20;             SQLite Tables                Reject Table

&#x20;         (customers, orders)          (invalid records)

&#x20;                   |

&#x20;                   v

&#x20;            CSV Snapshots

&#x20;                   |

&#x20;                   v

&#x20;         Pipeline Run Audit

```



\## 2. Technology Stack



\- Python

\- Pandas

\- SQLite

\- CSV

\- Pytest



\## 3. Requirements



\- Python 3.10 or later

\- pip

\- Git (optional)

\- No cloud credentials required



\## 4. Project Setup



\### Windows PowerShell



```powershell

py -m venv .venv

.venv\\Scripts\\Activate.ps1

python -m pip install -r requirements.txt

```



\### macOS/Linux



```bash

python3 -m venv .venv

source .venv/bin/activate

python -m pip install -r requirements.txt

```



\## 5. Generate Sample Data



```bash

python scripts/generate\_data.py --customers 100 --orders 500 --seed 42

```



This generates customer and order CSV input files.



\## 6. Execute the Pipeline



```bash

python -m src.pipeline

```



Default input files:



\- `data/raw/customers.csv`

\- `data/raw/orders.csv`



Default output database:



\- `output/warehouse.db`



Custom paths can be supplied:



```bash

python -m src.pipeline --customers data/raw/customers.csv --orders data/raw/orders.csv --db output/warehouse.db --output output

```



\## 7. Generate a Large Dataset



To generate 10,000 customers and 100,000 orders:



```bash

python scripts/generate\_data.py --customers 10000 --orders 100000 --seed 42

```



For a clean benchmark dataset without intentionally invalid rows:



```bash

python scripts/generate\_data.py --customers 10000 --orders 100000 --seed 42 --clean

```



\## 8. Data Validation



The pipeline handles:



\- Missing customer and order IDs.

\- Duplicate customer and order IDs.

\- Invalid email addresses.

\- Unknown customer references.

\- Invalid timestamps.

\- Non-positive order amounts.

\- Invalid currency formats.

\- Unsupported order statuses.

\- Malformed CSV records.

\- Unexpected CSV headers.



Rejected records are stored with their source filename, source line, raw record, rejection reason, and pipeline run ID.



\## 9. Database Tables



| Table | Description |

|---|---|

| customers | Validated customer records |

| orders | Validated order records |

| rejects | Rejected records and reasons |

| pipeline\_runs | Pipeline execution history |



\## 10. Output Files



\- `output/warehouse.db` – SQLite database.

\- `output/dim\_customers.csv` – Customer snapshot.

\- `output/fact\_orders.csv` – Order snapshot.

\- `output/reject\_summary\_<run>.csv` – Rejection summary by run.

\- `output/run\_<run>.json` – Pipeline metrics and source file hashes.



\## 11. Automated Tests



Execute:



```bash

python -m pytest -v

```



The test suite covers:



\- Successful processing and rejection handling.

\- Idempotent reruns.

\- Empty input batches.

\- Schema drift.

\- Malformed record quarantine.

\- Domain validation edge cases.



\*\*Latest verified result: 6 tests passed.\*\*



\## 12. Performance Benchmark



A clean synthetic dataset was generated and processed locally.



| Metric | Result |

|---|---:|

| Customers | 10,000 |

| Orders | 100,000 |

| Data generation time | 1.521 seconds |

| Pipeline execution time | 72.522 seconds |

| Total execution time | 74.042 seconds |

| Orders inserted | 100,000 |

| Rejected records | 0 |



These are measurements from the local development environment, not production performance guarantees.



\## 13. Idempotency



SQLite primary keys and insertion logic prevent duplicate business keys during repeated executions.



A repeated run creates a new pipeline audit entry without inserting duplicate customer or order records. Rejected records are recorded per run.



Existing records are not automatically updated when corrected source data uses the same business key.



\## 14. Documentation



Additional technical documentation:



\- \[Architecture](docs/architecture.md)

\- \[Data Dictionary](docs/data\_dictionary.md)

\- \[Design Decisions](docs/design\_decisions.md)








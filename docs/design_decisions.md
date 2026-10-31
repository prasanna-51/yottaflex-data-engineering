# Design decisions and trade-offs

1. **Python + Pandas + SQLite:** locally runnable, small dependency footprint and SQL-verifiable. SQLite is not a distributed warehouse.
2. **Strict header contract:** unexpected names/order fail fast; malformed row widths are quarantined rather than mis-mapped.
3. **Deterministic validation:** checks run in a fixed order and record the first failure reason. Business keys serve as stable IDs.
4. **Idempotency:** SQLite primary keys and `INSERT OR IGNORE` prevent duplicate target keys on reruns. SHA-256 file hashes are retained for audit, not used as the only deduplication mechanism.
5. **Late/out-of-order data:** event timestamps are preserved and parsed independently of arrival order; no event-time watermark is implemented.
6. **Reject traceability:** raw row, filename, line, run ID and reason are retained.
7. **Recovery:** failed runs are audited. Data writes and successful run metrics share a transaction; rerun after correcting the cause. Header/schema errors fail fast.
8. **Limitations:** single-process local SQLite; no schema evolution framework, PII encryption, SCD2 history, currency conversion, or multi-error-per-row reporting; basic email validation; existing keys are not updated.
9. **Optimization opportunity:** use `executemany`/bulk inserts and chunked CSV reading for larger files; consider Parquet and distributed processing only when measured volume requires it.

## Measured performance (this development environment)



A clean synthetic benchmark was executed with 10,000 customers and

100,000 orders.



| Metric | Result |

|---|---:|

| Customers generated | 10,000 |

| Orders generated | 100,000 |

| Data generation time | 1.521 seconds |

| Pipeline execution time | 72.522 seconds |

| Total execution time | 74.042 seconds |

| Orders inserted | 100,000 |

| Rejected records | 0 |



The pipeline successfully processed the 100,000-order dataset.

Performance is measured in a local development environment and is

not a production SLA.



Further optimization opportunities include chunked CSV reading,

bulk database inserts, and profiling transformation and snapshot

export operations.


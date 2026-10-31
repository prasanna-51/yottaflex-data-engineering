# Data dictionary

## Source entities and grain
- `customers.csv`: one row per customer; business key `customer_id`.
- `orders.csv`: one row per order; business key `order_id`; many orders may reference one customer.

## Customer columns
| Column | Type | Nullable | Rule |
|---|---|---:|---|
| customer_id | string | No | Stable unique business key |
| first_name | string | No | Non-empty |
| last_name | string | No | Non-empty |
| email | string | No | Must contain `@`; normalized lowercase |
| created_at | ISO-8601 timestamp | No | Parseable; normalized to UTC |

## Order columns
| Column | Type | Nullable | Rule |
|---|---|---:|---|
| order_id | string | No | Stable unique business key |
| customer_id | string | No | Must resolve to a current-batch or existing customer |
| order_timestamp | ISO-8601 timestamp | No | Parseable; normalized to UTC |
| amount | decimal | No | Strictly positive; rounded to 2 decimals |
| currency | string | No | Three alphabetic characters; uppercase |
| status | string | No | pending, paid, shipped, cancelled, refunded |

## Curated tables
- `customers`: one row per customer; `customer_id` primary key; includes `source_file` and `run_id` lineage.
- `orders`: one row per order; `order_id` primary key; customer foreign key; derived UTC `order_date`.
- `rejects`: raw rejected record, source file, source line, reason, run ID and rejection timestamp.
- `pipeline_runs`: one row per run with timestamps, status, counts, file hashes and failure reason.

Amounts are not aggregated across currencies. Existing order IDs are immutable in this starter implementation: a later row with the same ID is ignored rather than updated. For status history, add an append-only order event table.

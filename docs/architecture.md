# Architecture and operational flow

1. **Source:** local `customers.csv` and `orders.csv`; generator uses a fixed seed.
2. **Schema gate:** exact ordered headers required. Malformed row widths are quarantined with physical source line number.
3. **Validation:** customer keys/names/email/timestamps; order keys, duplicate IDs, customer references, timestamps, positive amount, ISO currency code shape and enumerated status.
4. **Transform:** trim identifiers/names, lowercase email, uppercase currency, normalize timestamps to UTC, round amount to two decimals and derive UTC `order_date`.
5. **Publish:** SQLite `customers` and `orders` tables with primary/foreign keys. CSV snapshots are generated for easy inspection.
6. **Reject path:** `rejects` table stores raw record, source filename, physical source line, reason and run ID.
7. **Observability:** `pipeline_runs` tracks status, timestamps, source/output counts, reject count, SHA-256 hashes and failure message; JSON run report and application logs are emitted.

The order grain is one row per unique order ID. Customer-to-order relationship is one-to-many. Arrival order is not assumed to equal event-time order; timestamps are retained and normalized.

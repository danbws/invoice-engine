# 🧾 Invoice Engine

A small invoicing service with the rules that matter in the real world: **concurrency-safe
sequential numbering**, **immutable issued documents**, **auditable cancellations**, and
**PDF output** — inspired by the system I run in production, which issues 20,000+ electronic
invoices a year for manufacturing companies in Brazil.

[![CI](https://github.com/danbws/invoice-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/danbws/invoice-engine/actions/workflows/ci.yml)

## The interesting problems

Invoicing looks like CRUD until a tax auditor shows up. Then three properties become
non-negotiable, and all three are implemented (and tested) here:

1. **Numbers are sequential, per series, with no duplicates — even under concurrency.**
   The number is claimed inside the issuing transaction with a row lock
   (`SELECT … FOR UPDATE` on the series counter), so two simultaneous issue requests
   serialize instead of racing.
2. **Issued documents are immutable.** Drafts can be edited freely; the moment an invoice
   gets a number, every mutation returns `409 Conflict`.
3. **Cancellation is an event, not a delete.** A cancelled invoice keeps its number
   (fiscal sequences are never reused), records a mandatory reason, and the next issue
   continues from where the sequence left off.

## Stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · ReportLab (PDF) · pytest · Docker

## Run it

```bash
docker compose up --build
```

- API docs (Swagger): http://localhost:8000/docs

Or locally:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload   # needs PostgreSQL, or set DATABASE_URL=sqlite:///./dev.db
pytest                          # tests run on in-memory SQLite, no setup needed
```

## Lifecycle

```
POST /api/invoices            → draft (editable, no number, no fiscal value)
POST /api/invoices/{id}/issue → issued (gets next number in series, frozen)
POST /api/invoices/{id}/cancel→ cancelled (keeps number, requires reason)
GET  /api/invoices/{id}/pdf   → A4 PDF (issued/cancelled only; cancelled is stamped)
GET  /api/invoices            → list (filter by status/customer, paginated: limit/offset)
GET  /api/invoices/summary    → billed revenue by month and series (issued only)
```

See a generated [sample PDF](docs/sample-invoice.pdf).

## About me

I'm Daniel Bichof — full-stack developer with 10 years building ERP and fintech systems for
industrial clients in Brazil. See also [factory-flow](https://github.com/danbws/factory-flow),
a production-order tracker for textile plants.

[LinkedIn](https://www.linkedin.com/in/danbichof) · daniel@websys.ind.br

## License

MIT

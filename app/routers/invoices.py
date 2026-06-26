from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Invoice, InvoiceItem, InvoiceStatus, NumberSequence
from ..pdf import render_invoice_pdf
from ..schemas import (
    CancelIn,
    InvoiceCreate,
    InvoiceOut,
    InvoiceUpdate,
    SummaryOut,
    SummaryRow,
)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


def _load(db: Session, invoice_id: int) -> Invoice:
    invoice = db.scalar(
        select(Invoice).options(selectinload(Invoice.items)).where(Invoice.id == invoice_id)
    )
    if not invoice:
        raise HTTPException(404, detail="Invoice not found")
    return invoice


def _require_draft(invoice: Invoice) -> None:
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(
            409,
            detail=f"Invoice {invoice.display_number or invoice.id} is {invoice.status.value}; "
            "issued documents are immutable",
        )


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    status: InvoiceStatus | None = None,
    customer: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(Invoice).options(selectinload(Invoice.items)).order_by(Invoice.created_at.desc())
    if status:
        query = query.where(Invoice.status == status)
    if customer:
        # Case-insensitive partial match — accounting teams search by a fragment
        # of the customer name far more often than they know the exact string.
        query = query.where(Invoice.customer_name.ilike(f"%{customer}%"))
    return db.scalars(query).all()


@router.get("/summary", response_model=SummaryOut)
def revenue_summary(db: Session = Depends(get_db)):
    """Billed revenue grouped by month and series, counting only ISSUED invoices.

    Cancelled and draft documents have no fiscal value, so they are excluded.
    Aggregation is done in Python rather than SQL so the report stays portable
    across databases (month extraction differs between SQLite and PostgreSQL)
    and reuses the same total logic as the rest of the app.
    """
    issued = db.scalars(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.status == InvoiceStatus.ISSUED)
    ).all()

    buckets: dict[tuple[str, str], dict] = {}
    for inv in issued:
        period = inv.issued_at.strftime("%Y-%m") if inv.issued_at else "unknown"
        bucket = buckets.setdefault(
            (period, inv.series), {"invoice_count": 0, "total": Decimal("0")}
        )
        bucket["invoice_count"] += 1
        bucket["total"] += inv.total

    rows = [
        SummaryRow(period=period, series=series, **data)
        for (period, series), data in sorted(buckets.items())
    ]
    return SummaryOut(
        rows=rows,
        total_invoices=sum(r.invoice_count for r in rows),
        total_amount=sum((r.total for r in rows), Decimal("0")),
    )


@router.post("", response_model=InvoiceOut, status_code=201)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    invoice = Invoice(
        series=payload.series,
        customer_name=payload.customer_name,
        customer_tax_id=payload.customer_tax_id,
        notes=payload.notes,
        items=[InvoiceItem(**item.model_dump()) for item in payload.items],
    )
    db.add(invoice)
    db.commit()
    return _load(db, invoice.id)


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    return _load(db, invoice_id)


@router.patch("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(invoice_id: int, payload: InvoiceUpdate, db: Session = Depends(get_db)):
    invoice = _load(db, invoice_id)
    _require_draft(invoice)

    data = payload.model_dump(exclude_unset=True)
    items = data.pop("items", None)
    for field, value in data.items():
        setattr(invoice, field, value)
    if items is not None:
        if not items:
            raise HTTPException(422, detail="An invoice needs at least one item")
        invoice.items = [InvoiceItem(**item) for item in items]

    db.commit()
    return _load(db, invoice_id)


@router.post("/{invoice_id}/issue", response_model=InvoiceOut)
def issue_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Assign the next sequential number for the series and freeze the document.

    The sequence row is locked (SELECT ... FOR UPDATE) for the duration of the
    transaction, so concurrent issues serialize and gaps/duplicates can't happen.
    """
    invoice = _load(db, invoice_id)
    _require_draft(invoice)

    seq = db.execute(
        select(NumberSequence).where(NumberSequence.series == invoice.series).with_for_update()
    ).scalar_one_or_none()
    if seq is None:
        seq = NumberSequence(series=invoice.series, next_number=1)
        db.add(seq)
        db.flush()

    invoice.number = seq.next_number
    seq.next_number += 1
    invoice.status = InvoiceStatus.ISSUED
    invoice.issued_at = datetime.now(timezone.utc)

    db.commit()
    return _load(db, invoice_id)


@router.post("/{invoice_id}/cancel", response_model=InvoiceOut)
def cancel_invoice(invoice_id: int, payload: CancelIn, db: Session = Depends(get_db)):
    """Cancelling keeps the number — fiscal sequences must not be reused."""
    invoice = _load(db, invoice_id)
    if invoice.status == InvoiceStatus.CANCELLED:
        raise HTTPException(409, detail="Invoice is already cancelled")
    invoice.status = InvoiceStatus.CANCELLED
    invoice.cancel_reason = payload.reason
    db.commit()
    return _load(db, invoice_id)


@router.get("/{invoice_id}/pdf")
def invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    invoice = _load(db, invoice_id)
    if invoice.status == InvoiceStatus.DRAFT:
        raise HTTPException(409, detail="Drafts have no fiscal value; issue the invoice first")
    pdf = render_invoice_pdf(invoice)
    filename = f"invoice-{invoice.display_number}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )

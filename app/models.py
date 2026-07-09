import enum
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"


class NumberSequence(Base):
    """One row per series. The next invoice number is claimed inside the
    issuing transaction with a row lock, so two concurrent issues can never
    take the same number — the property tax authorities care about most."""

    __tablename__ = "number_sequences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series: Mapped[str] = mapped_column(String(10), unique=True)
    next_number: Mapped[int] = mapped_column(Integer, default=1)


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("series", "number", name="uq_series_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series: Mapped[str] = mapped_column(String(10), default="A")
    number: Mapped[int | None] = mapped_column(Integer, default=None)  # set when issued
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, values_callable=lambda e: [m.value for m in e]),
        default=InvoiceStatus.DRAFT,
    )
    customer_name: Mapped[str] = mapped_column(String(120))
    customer_tax_id: Mapped[str | None] = mapped_column(String(20), default=None)
    notes: Mapped[str | None] = mapped_column(Text, default=None)
    cancel_reason: Mapped[str | None] = mapped_column(Text, default=None)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", order_by="InvoiceItem.id"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", order_by="Payment.paid_at.desc()"
    )

    @property
    def total(self) -> Decimal:
        return sum((i.quantity * i.unit_price for i in self.items), Decimal("0"))

    @property
    def amount_paid(self) -> Decimal:
        return sum((p.amount for p in self.payments), Decimal("0"))

    @property
    def balance_due(self) -> Decimal:
        return self.total - self.amount_paid

    @property
    def payment_status(self) -> PaymentStatus:
        if self.amount_paid <= 0:
            return PaymentStatus.UNPAID
        if self.balance_due <= 0:
            return PaymentStatus.PAID
        return PaymentStatus.PARTIALLY_PAID

    @property
    def display_number(self) -> str | None:
        return f"{self.series}-{self.number:06d}" if self.number else None


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    description: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    invoice: Mapped[Invoice] = relationship(back_populates="items")


class Payment(Base):
    """A payment received against an issued invoice. Append-only event, mirroring
    the cancellation philosophy: money movements are recorded, never mutated.
    The invoice balance and payment status are always derived from the sum of
    these rows, so the ledger stays auditable."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    method: Mapped[str] = mapped_column(String(40))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    note: Mapped[str | None] = mapped_column(Text, default=None)

    invoice: Mapped[Invoice] = relationship(back_populates="payments")

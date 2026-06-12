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

    @property
    def total(self) -> Decimal:
        return sum((i.quantity * i.unit_price for i in self.items), Decimal("0"))

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

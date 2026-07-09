from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .models import InvoiceStatus, PaymentStatus


class ItemIn(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class ItemOut(ItemIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class InvoiceCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    customer_tax_id: str | None = None
    series: str = Field(default="A", min_length=1, max_length=10)
    notes: str | None = None
    items: list[ItemIn] = Field(min_length=1)


class InvoiceUpdate(BaseModel):
    customer_name: str | None = None
    customer_tax_id: str | None = None
    notes: str | None = None
    items: list[ItemIn] | None = None


class CancelIn(BaseModel):
    reason: str = Field(min_length=5, max_length=500)


class PaymentIn(BaseModel):
    amount: Decimal = Field(gt=0)
    method: str = Field(min_length=1, max_length=40)
    note: str | None = Field(default=None, max_length=500)


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    amount: Decimal
    method: str
    paid_at: datetime
    note: str | None


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    series: str
    number: int | None
    display_number: str | None
    status: InvoiceStatus
    customer_name: str
    customer_tax_id: str | None
    notes: str | None
    cancel_reason: str | None
    issued_at: datetime | None
    created_at: datetime
    items: list[ItemOut]
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    payment_status: PaymentStatus


class SummaryRow(BaseModel):
    period: str  # "YYYY-MM"
    series: str
    invoice_count: int
    total: Decimal


class SummaryOut(BaseModel):
    rows: list[SummaryRow]
    total_invoices: int
    total_amount: Decimal


class CustomerSummaryRow(BaseModel):
    customer_name: str
    invoice_count: int
    total: Decimal

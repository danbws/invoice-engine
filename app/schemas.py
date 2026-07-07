from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from .models import InvoiceStatus


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

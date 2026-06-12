"""Generate docs/sample-invoice.pdf for the README: python -m tests.generate_sample"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./sample.db"

from fastapi.testclient import TestClient

from app.main import app

with TestClient(app) as client:
    draft = client.post(
        "/api/invoices",
        json={
            "customer_name": "Hanier Textiles Ltda",
            "customer_tax_id": "11.222.333/0001-44",
            "notes": "Payment due in 28 days. Batch 2026-T-0457.",
            "items": [
                {"description": "Cotton Jersey 160g — dyed, navy", "quantity": "812.40", "unit_price": "18.90"},
                {"description": "Polyamide Stretch 220g — finished", "quantity": "240.00", "unit_price": "31.50"},
                {"description": "Dyeing service — reactive process", "quantity": "1", "unit_price": "1450.00"},
            ],
        },
    ).json()
    client.post(f"/api/invoices/{draft['id']}/issue")
    pdf = client.get(f"/api/invoices/{draft['id']}/pdf")

os.makedirs("docs", exist_ok=True)
with open("docs/sample-invoice.pdf", "wb") as f:
    f.write(pdf.content)
print(f"Wrote docs/sample-invoice.pdf ({len(pdf.content)} bytes)")

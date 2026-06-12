def make_draft(client, series="A", customer="Hanier Textiles"):
    resp = client.post(
        "/api/invoices",
        json={
            "customer_name": customer,
            "customer_tax_id": "11.222.333/0001-44",
            "series": series,
            "items": [
                {"description": "Cotton Jersey 160g", "quantity": "120.5", "unit_price": "18.90"},
                {"description": "Dyeing service", "quantity": "1", "unit_price": "450.00"},
            ],
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_draft_has_no_number_and_computes_total(client):
    draft = make_draft(client)
    assert draft["status"] == "draft"
    assert draft["number"] is None
    assert draft["display_number"] is None
    assert float(draft["total"]) == 120.5 * 18.90 + 450.00


def test_issuing_assigns_sequential_numbers_per_series(client):
    a1 = make_draft(client, series="A")
    a2 = make_draft(client, series="A")
    b1 = make_draft(client, series="B")

    issued = [client.post(f"/api/invoices/{d['id']}/issue").json() for d in (a1, a2, b1)]

    assert (issued[0]["series"], issued[0]["number"]) == ("A", 1)
    assert (issued[1]["series"], issued[1]["number"]) == ("A", 2)
    assert (issued[2]["series"], issued[2]["number"]) == ("B", 1)
    assert issued[0]["display_number"] == "A-000001"


def test_issued_invoices_are_immutable(client):
    draft = make_draft(client)
    client.post(f"/api/invoices/{draft['id']}/issue")

    resp = client.patch(f"/api/invoices/{draft['id']}", json={"customer_name": "Other"})
    assert resp.status_code == 409

    resp = client.post(f"/api/invoices/{draft['id']}/issue")
    assert resp.status_code == 409


def test_cancellation_requires_reason_and_keeps_number(client):
    draft = make_draft(client)
    issued = client.post(f"/api/invoices/{draft['id']}/issue").json()

    resp = client.post(f"/api/invoices/{draft['id']}/cancel", json={"reason": "x"})
    assert resp.status_code == 422  # reason too short

    resp = client.post(
        f"/api/invoices/{draft['id']}/cancel", json={"reason": "Wrong customer data"}
    )
    assert resp.status_code == 200
    cancelled = resp.json()
    assert cancelled["status"] == "cancelled"
    assert cancelled["number"] == issued["number"]  # fiscal numbers are never reused

    # next invoice still gets the NEXT number, not the cancelled one
    nxt = make_draft(client)
    nxt = client.post(f"/api/invoices/{nxt['id']}/issue").json()
    assert nxt["number"] == issued["number"] + 1


def test_pdf_only_for_issued_documents(client):
    draft = make_draft(client)
    resp = client.get(f"/api/invoices/{draft['id']}/pdf")
    assert resp.status_code == 409

    client.post(f"/api/invoices/{draft['id']}/issue")
    resp = client.get(f"/api/invoices/{draft['id']}/pdf")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")

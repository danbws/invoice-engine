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


def test_list_filters_by_customer_case_insensitive_partial(client):
    make_draft(client, customer="Hanier Textiles")
    make_draft(client, customer="Zion Fabrics")

    hits = client.get("/api/invoices", params={"customer": "hanier"}).json()
    assert [i["customer_name"] for i in hits] == ["Hanier Textiles"]

    partial = client.get("/api/invoices", params={"customer": "fab"}).json()
    assert [i["customer_name"] for i in partial] == ["Zion Fabrics"]

    assert client.get("/api/invoices", params={"customer": "nobody"}).json() == []


def test_list_is_paginated(client):
    for i in range(5):
        make_draft(client, customer=f"Client {i}")

    first_page = client.get("/api/invoices", params={"limit": 2, "offset": 0}).json()
    second_page = client.get("/api/invoices", params={"limit": 2, "offset": 2}).json()

    assert len(first_page) == 2
    assert len(second_page) == 2
    # Pages don't overlap
    first_ids = {i["id"] for i in first_page}
    assert first_ids.isdisjoint(i["id"] for i in second_page)

    # Guardrails: limit must be within 1..200
    assert client.get("/api/invoices", params={"limit": 0}).status_code == 422
    assert client.get("/api/invoices", params={"limit": 999}).status_code == 422


def test_summary_counts_only_issued_invoices(client):
    # Two issued in series A, one issued in B, one cancelled, one left as draft.
    a1 = make_draft(client, series="A")
    a2 = make_draft(client, series="A")
    b1 = make_draft(client, series="B")
    cancelled = make_draft(client, series="A")
    make_draft(client, series="A")  # stays draft

    for d in (a1, a2, b1, cancelled):
        client.post(f"/api/invoices/{d['id']}/issue")
    client.post(f"/api/invoices/{cancelled['id']}/cancel", json={"reason": "Wrong data"})

    summary = client.get("/api/invoices/summary").json()

    # 3 issued counted (2 in A + 1 in B); cancelled and draft excluded
    assert summary["total_invoices"] == 3
    by_series = {r["series"]: r for r in summary["rows"]}
    assert by_series["A"]["invoice_count"] == 2
    assert by_series["B"]["invoice_count"] == 1
    # Each invoice totals 120.5*18.90 + 450 = 2727.45
    assert float(summary["total_amount"]) == round(3 * (120.5 * 18.90 + 450), 2)


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


def test_summary_by_customer_counts_only_issued(client):
    a1 = make_draft(client, customer="Hanier Textiles")
    a2 = make_draft(client, customer="Hanier Textiles")
    z1 = make_draft(client, customer="Zion Fabrics")
    make_draft(client, customer="Zion Fabrics")  # stays draft, excluded

    for d in (a1, a2, z1):
        client.post(f"/api/invoices/{d['id']}/issue")

    rows = client.get("/api/invoices/summary/by-customer").json()
    by = {r["customer_name"]: r for r in rows}
    assert by["Hanier Textiles"]["invoice_count"] == 2
    assert by["Zion Fabrics"]["invoice_count"] == 1  # only the issued one counts
    # Biggest customer by billed total comes first
    assert rows[0]["customer_name"] == "Hanier Textiles"


def test_export_csv_respects_filter_and_shows_numbers(client):
    a = make_draft(client, customer="Hanier Textiles")
    make_draft(client, customer="Zion Fabrics")
    client.post(f"/api/invoices/{a['id']}/issue")

    resp = client.get("/api/invoices/export.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    header = resp.text.splitlines()[0]
    assert header.startswith("id,number,status,customer_name")
    assert "Hanier Textiles" in resp.text and "Zion Fabrics" in resp.text

    # The customer filter carries into the export; issued invoice shows its number
    filtered = client.get("/api/invoices/export.csv", params={"customer": "hanier"}).text
    assert "Hanier Textiles" in filtered
    assert "Zion Fabrics" not in filtered
    assert "A-000001" in filtered

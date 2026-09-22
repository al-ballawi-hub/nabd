def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_patients_returns_list(client):
    resp = client.get("/api/v1/patients")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_record_from_text(client):
    client.post("/api/v1/seed")
    resp = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "تحليل سكر تراكمي HbA1c النتيجة 7.5%"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["recordType"] in {"lab", "prescription", "report", "scan"}
    assert data["source"] == "manual"
    assert data["title"]
    assert data["content"]

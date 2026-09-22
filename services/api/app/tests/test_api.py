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
        json={"text": "Patient presents with headache. Prescribed Amlodipine 5mg daily."},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["saved"] is True
    assert data["warnings"] == []
    assert data["recordType"] in {"lab", "prescription", "report", "scan"}


def test_record_text_safety_guardrail(client):
    client.post("/api/v1/seed")
    # Patient 1 has a Penicillin allergy — the submission is blocked.
    blocked = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Prescribed Penicillin 500mg for bacterial infection."},
    )
    assert blocked.status_code == 200
    data = blocked.json()
    assert data["saved"] is False
    assert any("Penicillin" in w for w in data["warnings"])

    # Override & approve saves the record.
    saved = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Prescribed Penicillin 500mg for bacterial infection.", "override": True},
    )
    assert saved.status_code == 201
    assert saved.json()["saved"] is True

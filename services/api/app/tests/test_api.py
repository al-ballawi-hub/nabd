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


def test_safety_negation_not_triggered(client):
    client.post("/api/v1/seed")
    # "denies any penicillin allergy" must NOT trigger the Penicillin warning.
    resp = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "The patient denies any penicillin allergy and has no known drug allergies."},
    )
    data = resp.json()
    assert data["saved"] is True
    assert data["warnings"] == []


def test_duplicate_lab_flagged(client):
    client.post("/api/v1/seed")
    # First glucose lab order is saved.
    client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Order glucose blood test for diabetes follow-up."},
    )
    # A repeat glucose order is flagged as duplicate.
    resp = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Repeat glucose blood test requested."},
    )
    data = resp.json()
    assert data["saved"] is False
    assert any("Duplicate lab test" in w for w in data["warnings"])


def test_patient_risks(client):
    client.post("/api/v1/seed")
    resp = client.get("/api/v1/patients/1/risks")
    assert resp.status_code == 200
    data = resp.json()
    assert "Type 2 Diabetes" in data["chronicConditions"]
    assert data["riskLevel"] in {"low", "moderate", "high"}


def test_family_tree(client):
    client.post("/api/v1/seed")
    resp = client.get("/api/v1/patients/1/family")
    assert resp.status_code == 200
    members = resp.json()
    assert isinstance(members, list)
    assert len(members) >= 1

    add = client.post(
        "/api/v1/patients/1/family",
        json={"relation": "sister", "name": "Test Sister", "conditions": "None"},
    )
    assert add.status_code == 201
    assert add.json()["relation"] == "sister"

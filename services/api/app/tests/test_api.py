def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_auth_required_for_patients(client, doctor_headers):
    # Without a token, the protected endpoint is rejected.
    assert client.get("/api/v1/patients").status_code == 401
    # With a valid token, it succeeds.
    resp = client.get("/api/v1/patients", headers=doctor_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_patient_role_cannot_create(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    login = client.post(
        "/api/v1/auth/login", json={"name": "Patient X", "role": "patient"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Some clinical note."},
        headers=headers,
    )
    assert resp.status_code == 403


def test_patients_returns_normalized_lists(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    data = client.get("/api/v1/patients", headers=doctor_headers).json()
    assert isinstance(data, list)
    # Allergies are a normalized list, not a comma-separated string.
    assert data[0]["allergies"] == ["Penicillin"]
    assert "Type 2 Diabetes" in data[0]["chronicConditions"]


def test_create_record_from_text(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    text = "Patient presents with headache. Prescribed Amlodipine 5mg daily."
    resp = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": text},
        headers=doctor_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["saved"] is True
    assert data["warnings"] == []
    assert data["recordType"] in {"lab", "prescription", "report", "scan"}

    # Audit identity is derived from the JWT, not the request body.
    recs = client.get("/api/v1/patients/1/records", headers=doctor_headers).json()
    created = [r for r in recs if r["content"] == text]
    assert created and created[0]["createdBy"] == "Dr. Test"


def test_record_text_safety_guardrail(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    # Patient 1 has a Penicillin allergy — the submission is blocked.
    blocked = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Prescribed Penicillin 500mg for bacterial infection."},
        headers=doctor_headers,
    )
    assert blocked.status_code == 200
    data = blocked.json()
    assert data["saved"] is False
    assert any("Penicillin" in w for w in data["warnings"])

    # Override & approve saves the record.
    saved = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Prescribed Penicillin 500mg for bacterial infection.", "override": True},
        headers=doctor_headers,
    )
    assert saved.status_code == 201
    assert saved.json()["saved"] is True


def test_duplicate_lab_flagged(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    # First glucose lab order is saved.
    client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Order glucose blood test for diabetes follow-up."},
        headers=doctor_headers,
    )
    # A repeat glucose order is flagged as duplicate.
    resp = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Repeat glucose blood test requested."},
        headers=doctor_headers,
    )
    data = resp.json()
    assert data["saved"] is False
    assert any("Duplicate lab test" in w for w in data["warnings"])


def test_patient_risks(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    resp = client.get("/api/v1/patients/1/risks", headers=doctor_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "Type 2 Diabetes" in data["chronicConditions"]
    assert data["riskLevel"] in {"low", "moderate", "high"}


def test_family_tree(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    members = client.get("/api/v1/patients/1/family", headers=doctor_headers).json()
    assert isinstance(members, list)
    assert len(members) >= 1

    add = client.post(
        "/api/v1/patients/1/family",
        json={"relation": "sister", "name": "Test Sister", "conditions": ""},
        headers=doctor_headers,
    )
    assert add.status_code == 201
    assert add.json()["relation"] == "sister"

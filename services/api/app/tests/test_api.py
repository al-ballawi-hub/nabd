def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_auth_required_for_patients(client, doctor_headers):
    # Without a token, the protected endpoint is rejected.
    assert client.get("/api/v1/patients").status_code == 401
    # With a valid token, it succeeds and returns a paginated envelope.
    resp = client.get("/api/v1/patients", headers=doctor_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json()["items"], list)


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
    body = client.get("/api/v1/patients", headers=doctor_headers).json()
    assert body["total"] == 5
    assert body["items"][0]["allergies"] == ["Penicillin"]
    assert "Type 2 Diabetes" in body["items"][0]["chronicConditions"]


def test_pagination(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    page1 = client.get(
        "/api/v1/patients?limit=2&offset=0", headers=doctor_headers
    ).json()
    assert page1["total"] == 5
    assert page1["limit"] == 2
    assert len(page1["items"]) == 2

    page2 = client.get(
        "/api/v1/patients?limit=2&offset=2", headers=doctor_headers
    ).json()
    assert len(page2["items"]) == 2
    assert page2["items"][0]["id"] != page1["items"][0]["id"]


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
    created = [r for r in recs["items"] if r["content"] == text]
    assert created and created[0]["createdBy"] == "Dr. Test"


def test_record_text_safety_guardrail(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    blocked = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Prescribed Penicillin 500mg for bacterial infection."},
        headers=doctor_headers,
    )
    assert blocked.status_code == 200
    data = blocked.json()
    assert data["saved"] is False
    assert any("Penicillin" in w for w in data["warnings"])

    saved = client.post(
        "/api/v1/patients/1/records/text",
        json={
            "text": "Prescribed Penicillin 500mg for bacterial infection.",
            "override": True,
        },
        headers=doctor_headers,
    )
    assert saved.status_code == 201
    assert saved.json()["saved"] is True


def test_duplicate_lab_flagged(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Order glucose blood test for diabetes follow-up."},
        headers=doctor_headers,
    )
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
    body = client.get("/api/v1/patients/1/family", headers=doctor_headers).json()
    members = body["items"]
    assert isinstance(members, list)
    assert len(members) >= 1
    # Conditions are a normalized list, not a comma-separated string.
    assert isinstance(members[0]["conditions"], list)

    add = client.post(
        "/api/v1/patients/1/family",
        json={"relation": "sister", "name": "Test Sister", "conditions": ["Asthma"]},
        headers=doctor_headers,
    )
    assert add.status_code == 201
    assert add.json()["relation"] == "sister"
    assert add.json()["conditions"] == ["Asthma"]

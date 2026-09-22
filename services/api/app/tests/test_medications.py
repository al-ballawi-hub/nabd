def test_active_medications_listed(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    meds = client.get("/api/v1/patients/1/medications", headers=doctor_headers).json()
    names = [m["name"] for m in meds if m["status"] == "active"]
    assert "Metformin" in names
    assert "Amlodipine" in names


def test_medication_registered_on_save(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    # Patient 4 has no prior medications, so this is a clean registration.
    resp = client.post(
        "/api/v1/patients/4/records/text",
        json={"text": "Prescribed Metformin 850mg daily."},
        headers=doctor_headers,
    )
    assert resp.json()["saved"] is True
    meds = client.get("/api/v1/patients/4/medications", headers=doctor_headers).json()
    names = [m["name"] for m in meds if m["status"] == "active"]
    assert "Sample Medication" in names


def test_medication_not_registered_when_blocked(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    before = client.get("/api/v1/patients/1/medications", headers=doctor_headers).json()
    blocked = client.post(
        "/api/v1/patients/1/records/text",
        json={"text": "Prescribed Penicillin 500mg."},
        headers=doctor_headers,
    )
    assert blocked.json()["saved"] is False
    # A blocked submission must not register any medication.
    after = client.get("/api/v1/patients/1/medications", headers=doctor_headers).json()
    assert len(after) == len(before)


def test_drug_drug_conflict(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    # Patient 3 is on Aspirin; prescribing Warfarin triggers a drug-drug conflict.
    resp = client.post(
        "/api/v1/patients/3/records/text",
        json={"text": "Prescribed Warfarin 5mg."},
        headers=doctor_headers,
    )
    data = resp.json()
    assert data["saved"] is False
    assert any(c["type"] == "drug-drug" for c in data["conflicts"])


def test_medication_add_and_stop(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    add = client.post(
        "/api/v1/patients/1/medications",
        json={"name": "Insulin", "dosage": "10 units"},
        headers=doctor_headers,
    )
    assert add.status_code == 201
    assert add.json()["name"] == "Insulin"
    assert add.json()["status"] == "active"

    med_id = add.json()["id"]
    stop = client.post(
        f"/api/v1/patients/1/medications/{med_id}/stop",
        headers=doctor_headers,
    )
    assert stop.json()["status"] == "stopped"


def test_risks_include_active_medications(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    risks = client.get("/api/v1/patients/1/risks", headers=doctor_headers).json()
    assert "Metformin" in risks["activeMedications"]

def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_patients_returns_list(client):
    resp = client.get("/api/v1/patients")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

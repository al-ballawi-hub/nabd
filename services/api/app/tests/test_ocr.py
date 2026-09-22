import io

from PIL import Image

from app.services import ocr_service


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (20, 20), "white").save(buf, format="PNG")
    return buf.getvalue()


def test_extract_text_returns_string():
    # Works with or without a Tesseract binary installed (mock fallback).
    result = ocr_service.extract_text(_png_bytes())
    assert isinstance(result, str)
    assert result.strip()


def test_ocr_endpoint(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    resp = client.post(
        "/api/v1/patients/1/records/ocr",
        files={"file": ("scan.png", _png_bytes(), "image/png")},
        headers=doctor_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["extractedText"]
    assert isinstance(body["extractedText"], str)


def test_ocr_rejects_invalid_type(client, doctor_headers):
    client.post("/api/v1/seed", headers=doctor_headers)
    resp = client.post(
        "/api/v1/patients/1/records/ocr",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
        headers=doctor_headers,
    )
    assert resp.status_code == 415


def test_ocr_requires_doctor(client):
    login = client.post(
        "/api/v1/auth/login", json={"name": "Patient X", "role": "patient"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    resp = client.post(
        "/api/v1/patients/1/records/ocr",
        files={"file": ("scan.png", _png_bytes(), "image/png")},
        headers=headers,
    )
    assert resp.status_code == 403

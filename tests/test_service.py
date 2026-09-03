import httpx


def token(api_url: str, username: str, password: str) -> str:
    response = httpx.post(
        f"{api_url}/token", json={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_health_is_public(api_url: str) -> None:
    response = httpx.get(f"{api_url}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Trace-ID"]


def test_bad_login_returns_401(api_url: str) -> None:
    response = httpx.post(
        f"{api_url}/token", json={"username": "clinician", "password": "wrongpass"}
    )
    assert response.status_code == 401


def test_missing_token_returns_401(api_url: str) -> None:
    response = httpx.post(
        f"{api_url}/triage",
        json={"patient_id": "P-100", "symptoms": ["fever"], "age_years": 25},
    )
    assert response.status_code == 401


def test_wrong_role_returns_403(api_url: str) -> None:
    coordinator = token(api_url, "coordinator", "logistics2026")
    response = httpx.post(
        f"{api_url}/triage",
        headers={"Authorization": f"Bearer {coordinator}"},
        json={"patient_id": "P-100", "symptoms": ["fever"], "age_years": 25},
    )
    assert response.status_code == 403


def test_invalid_payload_returns_422(api_url: str) -> None:
    clinician = token(api_url, "clinician", "clinical2026")
    response = httpx.post(
        f"{api_url}/triage",
        headers={"Authorization": f"Bearer {clinician}"},
        json={"patient_id": "?", "symptoms": [], "age_years": 999},
    )
    assert response.status_code == 422


def test_clinician_can_triage(api_url: str) -> None:
    clinician = token(api_url, "clinician", "clinical2026")
    response = httpx.post(
        f"{api_url}/triage",
        headers={"Authorization": f"Bearer {clinician}", "X-Trace-ID": "test-trace-200"},
        json={
            "patient_id": "P-200",
            "symptoms": ["difficulty breathing"],
            "age_years": 31,
        },
    )
    assert response.status_code == 200
    assert response.json()["urgency"] == "emergency"
    assert response.json()["trace_id"] == "test-trace-200"

import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ.pop("GEMINI_API_KEY", None)
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
PROFILE = dict(cibil_score=690, monthly_income=80000, monthly_expenses=30000, monthly_debt_payments=25000,
               credit_limit=200000, credit_used=120000, active_loans=2, missed_payments=1,
               savings=50000, financial_goal="Buy a home")


def auth():
    client.post("/api/auth/register", json={"name": "Test User", "email": "t@example.com", "password": "pass1234"})
    r = client.post("/api/auth/login", json={"email": "t@example.com", "password": "pass1234"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_register_validation():
    r = client.post("/api/auth/register", json={"name": "A", "email": "bad", "password": "123"})
    assert r.status_code == 422


def test_protected_route():
    assert client.get("/api/profile").status_code == 401


def test_full_flow():
    h = auth()
    assert client.put("/api/profile", json=PROFILE, headers=h).status_code == 200
    client.post("/api/scores", json={"score": 710}, headers=h)
    d = client.get("/api/dashboard", headers=h).json()
    assert d["metrics"]["utilization"] == 60.0
    assert d["metrics"]["dti_ratio"] == 31.2
    assert len(d["score_history"]) == 2 and d["improvement"]["change"] == 20
    r = client.post("/api/advisor/analyze", headers=h)
    assert r.status_code == 200 and r.json()["content"]
    assert len(client.get("/api/advisor/history", headers=h).json()) == 1

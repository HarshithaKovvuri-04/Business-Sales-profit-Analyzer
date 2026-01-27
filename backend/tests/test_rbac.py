import os
import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

# Ensure the DB URL check in session.py does not fail during tests
os.environ.setdefault('DATABASE_URL', 'postgresql://user:pass@localhost:5432/bizanalyzer')

from backend.app.main import app
from backend.app import crud


@pytest.fixture(autouse=True)
def no_db(monkeypatch):
    """Prevent real DB access by stubbing CRUD functions used by tests."""
    # Always pretend the business exists
    monkeypatch.setattr(crud, 'get_business', lambda db, bid: SimpleNamespace(id=bid, owner_id=1, name='TestBiz'))
    yield


def override_current_user(role):
    def _dep():
        return SimpleNamespace(id=1, username='testuser', role=role)
    return _dep


def test_staff_cannot_access_financial_apis(monkeypatch):
    # Staff role should receive 403 on analytics summary
    client = TestClient(app)
    # stub business role
    monkeypatch.setattr(crud, 'get_user_business_role', lambda db, uid, bid: 'staff')
    # override current_user dependency
    from backend.app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = override_current_user('staff')

    r = client.get('/analytics/summary/1')
    assert r.status_code == 403

    app.dependency_overrides.clear()


def test_accountant_cannot_access_ml_predictions(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(crud, 'get_user_business_role', lambda db, uid, bid: 'accountant')
    from backend.app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = override_current_user('accountant')

    r = client.get('/ml/predict-profit/1')
    assert r.status_code == 403

    app.dependency_overrides.clear()


def test_owner_can_access_ml_predictions(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(crud, 'get_user_business_role', lambda db, uid, bid: 'owner')
    from backend.app.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = override_current_user('owner')

    # stub ML model store functions to avoid heavy deps
    import backend.ml.model_store as model_store
    monkeypatch.setattr(model_store, 'load_profit_model', lambda bid: (object(), {'metrics': {}}))
    monkeypatch.setattr(model_store, 'predict_next_month_profit', lambda db, bid: 123.45)

    r = client.get('/ml/predict-profit/1')
    assert r.status_code == 200
    assert r.json().get('predicted_profit') == 123.45

    app.dependency_overrides.clear()

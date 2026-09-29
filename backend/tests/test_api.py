from fastapi.testclient import TestClient

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.area_analysis import score_area, search_localities
from app.main import app
from app.models import AreaReport



@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        with testing_sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_demo_users_include_each_project_role(client: TestClient) -> None:
    response = client.get("/api/demo-users")

    assert response.status_code == 200
    assert {user["role"] for user in response.json()} == {
        "bd_manager",
        "bd_executive",
        "survey_manager",
        "survey_executive",
    }


def test_area_search_returns_matching_chennai_localities() -> None:
    results = search_localities("anna")

    assert [area["id"] for area in results] == ["anna-nagar"]


def test_area_fitness_score_uses_documented_weights() -> None:
    score, breakdown = score_area(
        {
            "residential_features": 80,
            "commercial_features": 120,
            "amenities": 20,
            "road_segments": 50,
            "transit_points": 8,
            "competitors": 0,
        }
    )

    assert score == 98
    assert sum(component["weight"] for component in breakdown.values()) == 100
    assert all(0 <= component["score"] <= 100 for component in breakdown.values())


def test_area_search_endpoint(client: TestClient) -> None:
    response = client.get("/api/areas/search", params={"q": "anna"})

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Anna Nagar"


def test_area_analysis_persists_and_returns_report(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_area_report(locality_id: str) -> dict:
        return {
            "locality_id": locality_id,
            "name": "Anna Nagar",
            "latitude": 13.085,
            "longitude": 80.2101,
            "radius_m": 1200,
            "fitness_score": 76,
            "metrics": {"counts": {"competitors": 8}, "score_breakdown": {}},
            "highlights": ["Strong residential signal"],
            "risks": ["Check rent during field scouting"],
            "data_source": "Demo sample data",
            "is_demo": True,
        }

    monkeypatch.setattr("app.areas.build_area_report", fake_area_report)
    response = client.post("/api/areas/analyze", json={"locality_id": "anna-nagar"})

    assert response.status_code == 200
    report_id = response.json()["id"]
    assert client.get("/api/areas/reports").json()[0]["id"] == report_id
    assert client.get(f"/api/areas/reports/{report_id}").json()["fitness_score"] == 76


def test_area_analysis_rejects_unknown_locality(client: TestClient) -> None:
    response = client.post("/api/areas/analyze", json={"locality_id": "unknown"})

    assert response.status_code == 404


def test_property_creation_and_status_update(client: TestClient) -> None:
    create_response = client.post(
        "/api/properties",
        json={
            "locality_id": "anna-nagar",
            "address": "12th Main Road, Anna Nagar",
            "latitude": 13.085,
            "longitude": 80.2101,
            "monthly_rent": 420000,
            "property_area_sqft": 1400,
            "frontage_m": 16,
            "road_width_m": 12,
            "parking_slots": 2,
            "visibility": 8,
            "condition": "good",
            "notes": "Near residential cluster",
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "SCOUTED"
    assert created["score"] >= 0

    update_response = client.patch(
        f"/api/properties/{created['id']}/status",
        json={"status": "UNDER REVIEW", "note": "Checking demand fit"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "UNDER REVIEW"


def test_catchment_request_and_survey_queue(client: TestClient) -> None:
    response = client.post(
        "/api/catchment-requests",
        json={
            "area_name": "Anna Nagar",
            "locality_id": "anna-nagar",
            "target_type": "area",
            "reason": "Need lane validation before opening",
        },
    )

    assert response.status_code == 200
    created = response.json()
    assert created["status"] == "PENDING"
    assert client.get("/api/catchment-requests").json()[0]["id"] == created["id"]
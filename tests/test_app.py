from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


def encode_activity(activity_name: str) -> str:
    return quote(activity_name, safe="")


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_for_activity_success(client):
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"

    response = client.post(
        f"/activities/{encode_activity(activity_name)}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}


def test_signup_for_activity_fails_if_already_signed_up(client):
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{encode_activity(activity_name)}/signup",
        params={"email": existing_email},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up"}


def test_signup_for_activity_fails_for_unknown_activity(client):
    response = client.post(
        f"/activities/{encode_activity('Unknown Club')}/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_from_activity_success(client):
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    response = client.delete(
        f"/activities/{encode_activity(activity_name)}/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}


def test_unregister_from_activity_fails_for_unknown_activity(client):
    response = client.delete(
        f"/activities/{encode_activity('Unknown Club')}/participants",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_from_activity_fails_if_participant_missing(client):
    activity_name = "Chess Club"
    response = client.delete(
        f"/activities/{encode_activity(activity_name)}/participants",
        params={"email": "not-enrolled@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant not found in this activity"}
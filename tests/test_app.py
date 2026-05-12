"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test to ensure isolation"""
    # Store original activities
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Clear and reset activities dict
    activities.clear()
    activities.update(original)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_returns_activity_details(self, client):
        """Test that activities include all required fields"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_shows_participants(self, client):
        """Test that activities show current participants"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client):
        """Test signing up a new participant"""
        response = client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client):
        """Test that signing up the same person twice fails"""
        email = "michael@mergington.edu"
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for nonexistent activity fails"""
        response = client.post("/activities/Nonexistent Activity/signup?email=student@mergington.edu")
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        response = client.delete("/activities/Chess Club/participants/michael@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "michael@mergington.edu"
        client.delete(f"/activities/Chess Club/participants/{email}")
        
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client):
        """Test that unregistering nonexistent participant fails"""
        response = client.delete("/activities/Chess Club/participants/nonexistent@mergington.edu")
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
    
    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test that unregistering from nonexistent activity fails"""
        response = client.delete("/activities/Nonexistent Activity/participants/student@mergington.edu")
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios"""
    
    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering"""
        email = "teststu@mergington.edu"
        
        # Sign up
        response = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Programming Class"]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/Programming Class/participants/{email}")
        assert response.status_code == 200
        
        # Verify unregistration
        response = client.get("/activities")
        assert email not in response.json()["Programming Class"]["participants"]
    
    def test_multiple_signups(self, client):
        """Test multiple participants signing up for the same activity"""
        emails = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]
        
        for email in emails:
            response = client.post(f"/activities/Gym Class/signup?email={email}")
            assert response.status_code == 200
        
        response = client.get("/activities")
        gym_class = response.json()["Gym Class"]
        
        for email in emails:
            assert email in gym_class["participants"]

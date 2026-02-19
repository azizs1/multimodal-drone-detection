from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_root():
    """Test the root endpoint returns the expected message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_root_response_structure():
    """Test that the root endpoint returns JSON with a message field."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)

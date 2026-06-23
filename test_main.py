from fastapi.testclient import TestClient
from main import app
import random

# Initialize the test execution client
client = TestClient(app)

# Generate a unique username and email for clean test isolation
random_id = random.randint(1000, 9999)
test_username = f"tester_{random_id}"
test_email = f"tester_{random_id}@example.com"
test_password = "securepassword123"

# Dictionary to hold the authentication token across different tests
auth_headers = {}

def test_read_root():
    """Verify that the home page endpoint is responsive."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to your Task Manager API!"}

def test_register_user_success():
    """Verify a user can register successfully with valid data."""
    response = client.post(
        "/register",
        json={"username": test_username, "email": test_email, "password": test_password}
    )
    assert response.status_code == 201
    assert "user_id" in response.json()
    assert response.json()["username"] == test_username

def test_register_user_password_too_short():
    """Verify that password length constraints reject weak inputs."""
    response = client.post(
        "/register",
        json={"username": "shorty", "email": "short@example.com", "password": "123"}
    )
    assert response.status_code == 422  # Unprocessable Entity

def test_login_success():
    """Verify user can log in and receive a JWT authorization token."""
    global auth_headers
    response = client.post(
        "/login",
        data={"username": test_username, "password": test_password}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # Store token in headers for subsequent authenticated task tests
    auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}

def test_create_task_authenticated():
    """Verify an authorized user can create a task item."""
    global auth_headers
    response = client.post(
        "/tasks",
        json={"title": "Write Pytest Automation", "description": "Verify endpoint routing handles errors"},
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Write Pytest Automation"

def test_create_task_unauthenticated():
    """Verify that unauthenticated task actions are completely blocked."""
    response = client.post(
        "/tasks",
        json={"title": "Hack Attempt", "description": "Should be blocked"}
    )
    assert response.status_code == 401  # Unauthorized

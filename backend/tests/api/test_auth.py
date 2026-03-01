import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db.models import User


class TestAuthEndpoints:
    def test_signup(self, client: TestClient, db: Session):
        email = f"testsignup_{uuid.uuid4()}@example.com"
        response = client.post(
            "/v1/auth/signup",
            json={
                "email": email,
                "password": "strongpassword123",
                "name": "Sign Up User",
                "role": "user",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert "id" in data
        
        # Verify in DB
        from tests.api.conftest import TestingSessionLocal
        
        session = TestingSessionLocal()
        user = session.query(User).filter(User.email == email).first()
        assert user is not None
        assert verify_password("strongpassword123", user.hashed_password)
        session.close()

    def test_signup_existing_email(self, client: TestClient, db: Session):
        # Already created user in conftest => test@example.com
        response = client.post(
            "/v1/auth/signup",
            json={
                "email": "test@example.com",
                "password": "anotherpassword",
                "name": "Existing User",
            },
        )
        assert response.status_code == 400

    def test_login(self, client: TestClient, db: Session):
        email = f"login_user_{uuid.uuid4()}@example.com"
        client.post(
            "/v1/auth/signup",
            json={"email": email, "password": "mypassword"},
        )
        response = client.post(
            "/v1/auth/login",
            json={"email": email, "password": "mypassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client: TestClient):
        response = client.post(
            "/v1/auth/login",
            json={"email": "wrong@example.com", "password": "wrong"},
        )
        assert response.status_code == 401

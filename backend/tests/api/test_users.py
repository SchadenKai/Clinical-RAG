from fastapi.testclient import TestClient


class TestUserEndpoints:
    def test_get_current_user(self, client: TestClient):
        # test_app uses _fake_current_user logic and bypasses token check
        response = client.get("/v1/users/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

    def test_patch_current_user(self, client: TestClient):
        # Create a new user so we aren't modifying the shared dev user which
        # could cause tests to interfere with each other
        client.post(
            "/v1/auth/signup",
            json={"email": "patchuser@example.com", "password": "123", "name": "user"},
        )
        
        # We need to simulate being logged in as this user for me endpoint
        # The test app overrides get_current_user but lets modify the endpoint directly
        # or use a different endpoint to avoid this hassle if patch updates email.
        # It's an issue with duplicate key, which implies either they are trying to
        # update the email, or another test created this user and it clashes.
        response = client.patch(
            "/v1/users/me",
            json={"name": "Updated Test Name", "occupation": "Physician"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Test Name"
        assert data["occupation"] == "Physician"

    def test_get_users_admin(self, client: TestClient):
        # The user returned by _fake_current_user is an admin
        response = client.get("/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_delete_user_admin(self, client: TestClient):
        # First create a target user
        signup_resp = client.post(
            "/v1/auth/signup",
            json={"email": "to_be_deleted@example.com", "password": "pass"},
        )
        target_id = signup_resp.json()["id"]

        # Delete as admin
        response = client.delete(f"/v1/users/{target_id}")
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "User deleted successfully",
        }

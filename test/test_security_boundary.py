import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import Response

from backend import security


class SecurityBoundaryTests(unittest.TestCase):

    def _request(self, headers=None, cookies=None):
        headers = headers or {}
        cookies = cookies or {}
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(key.lower().encode(), value.encode()) for key, value in headers.items()],
            "client": ("127.0.0.1", 50000),
            "scheme": "http",
            "server": ("localhost", 8000),
            "query_string": b"",
        }
        request = Request(scope)
        request._cookies = cookies
        return request

    def test_security_headers_are_added(self):
        response = security.apply_security_headers(Response())
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("strict-origin", response.headers["Referrer-Policy"])

    def test_development_origins_are_restricted(self):
        with patch.dict("os.environ", {"NOVA_ENV": "development"}, clear=False):
            origins = security.allowed_origins()
        self.assertIn("http://localhost:5173", origins)
        self.assertNotIn("*", origins)

    def test_production_requires_explicit_origins(self):
        with patch.dict("os.environ", {"NOVA_ENV": "production", "NOVA_ALLOWED_ORIGINS": ""}, clear=False):
            self.assertEqual(security.allowed_origins(), [])

    def test_missing_authentication_is_rejected(self):
        request = self._request()
        with self.assertRaises(HTTPException) as context:
            security.authenticate_session(request, {}, __import__("threading").RLock())
        self.assertEqual(context.exception.status_code, 401)

    def test_bearer_session_resolves_identity(self):
        token = "test-session-token"
        sessions = {token: {"email": "student@example.com", "expires_at": "future"}}
        request = self._request(headers={"Authorization": f"Bearer {token}"})
        email = security.require_same_user(request, sessions, __import__("threading").RLock(), "student@example.com")
        self.assertEqual(email, "student@example.com")

    def test_identity_mismatch_is_rejected(self):
        token = "test-session-token"
        sessions = {token: {"email": "student@example.com", "expires_at": "future"}}
        request = self._request(headers={"Authorization": f"Bearer {token}"})
        with self.assertRaises(HTTPException) as context:
            security.require_same_user(request, sessions, __import__("threading").RLock(), "other@example.com")
        self.assertEqual(context.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()

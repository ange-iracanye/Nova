"""Small V1 production smoke test for two-account isolation.

Usage (Windows CMD):
  set NOVA_SMOKE_URL=https://your-api.example.com
  set NOVA_SMOKE_EMAIL_A=test-a@example.com
  set NOVA_SMOKE_PASSWORD_A=...
  set NOVA_SMOKE_EMAIL_B=test-b@example.com
  set NOVA_SMOKE_PASSWORD_B=...
  python scripts/v1_smoke.py

The script never prints passwords or session tokens. It does not create
accounts and therefore does not leave test users behind.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar


BASE = os.getenv("NOVA_SMOKE_URL", "").strip().rstrip("/")
EMAIL_A = os.getenv("NOVA_SMOKE_EMAIL_A", "").strip().lower()
PASSWORD_A = os.getenv("NOVA_SMOKE_PASSWORD_A", "")
EMAIL_B = os.getenv("NOVA_SMOKE_EMAIL_B", "").strip().lower()
PASSWORD_B = os.getenv("NOVA_SMOKE_PASSWORD_B", "")


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def require_config() -> None:
    missing = []
    for name, value in (
        ("NOVA_SMOKE_URL", BASE),
        ("NOVA_SMOKE_EMAIL_A", EMAIL_A),
        ("NOVA_SMOKE_PASSWORD_A", PASSWORD_A),
        ("NOVA_SMOKE_EMAIL_B", EMAIL_B),
        ("NOVA_SMOKE_PASSWORD_B", PASSWORD_B),
    ):
        if not value:
            missing.append(name)
    if missing:
        fail("Missing environment variables: " + ", ".join(missing))
    if not BASE.startswith("https://"):
        fail("NOVA_SMOKE_URL must use HTTPS for a production test.")
    if EMAIL_A == EMAIL_B:
        fail("Account A and Account B must be different users.")


def client() -> tuple[urllib.request.OpenerDirector, http.cookiejar.CookieJar]:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar)), jar


def request(opener, method: str, path: str, payload: dict | None = None):
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with opener.open(request, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                data = {"raw": raw}
            return response.status, data
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {"raw": raw}
        return error.code, data
    except urllib.error.URLError as error:
        fail(f"Network error on {method} {path}: {error.reason}")


def assert_status(actual: int, expected: int, label: str) -> None:
    if actual != expected:
        fail(f"{label}: expected HTTP {expected}, got {actual}")


def login(opener, email: str, password: str) -> None:
    status, data = request(opener, "POST", "/login", {"email": email, "password": password})
    assert_status(status, 200, f"login {email}")
    if not data.get("success"):
        fail(f"login {email} was rejected")
    user = (data.get("user") or {}).get("email")
    if user != email:
        fail(f"login {email} returned the wrong user")


def main() -> None:
    require_config()
    print(f"Nova V1 smoke test: {BASE}")

    health_client, _ = client()
    status, data = request(health_client, "GET", "/health")
    assert_status(status, 200, "/health")
    if data.get("service") != "Nova AI":
        fail("/health returned an unexpected service name")
    print("PASS: health")

    # Account A: authenticate, verify its session, and verify its dashboard.
    client_a, _ = client()
    login(client_a, EMAIL_A, PASSWORD_A)
    print("PASS: account A login")
    status, data = request(client_a, "GET", "/auth/session")
    assert_status(status, 200, "account A session")
    if not data.get("authenticated") or (data.get("user") or {}).get("email") != EMAIL_A:
        fail("account A session identity is incorrect")
    print("PASS: account A session")
    status, data = request(client_a, "GET", "/dashboard")
    assert_status(status, 200, "account A dashboard")
    print("PASS: account A dashboard")

    # Account B gets its own independent cookie jar.
    client_b, _ = client()
    login(client_b, EMAIL_B, PASSWORD_B)
    print("PASS: account B login")
    status, data = request(client_b, "GET", "/auth/session")
    assert_status(status, 200, "account B session")
    if not data.get("authenticated") or (data.get("user") or {}).get("email") != EMAIL_B:
        fail("account B session identity is incorrect")
    print("PASS: account B session")
    status, data = request(client_b, "GET", "/dashboard")
    assert_status(status, 200, "account B dashboard")
    print("PASS: account B dashboard")

    # Explicit cross-account authorization check.
    escaped_b = urllib.parse.quote(EMAIL_B, safe="")
    status, _ = request(client_a, "GET", f"/dashboard/{escaped_b}")
    assert_status(status, 403, "account A accessing account B dashboard")
    print("PASS: cross-account dashboard isolation")

    # Logout must revoke the server-side session.
    status, _ = request(client_a, "POST", "/auth/logout")
    assert_status(status, 200, "account A logout")
    status, _ = request(client_a, "GET", "/dashboard")
    assert_status(status, 401, "account A after logout")
    print("PASS: logout revocation")

    print("ALL V1 SMOKE CHECKS PASSED")


if __name__ == "__main__":
    main()

"""Account properties that are easy to break while trying to be helpful."""

from sqlalchemy import select

from app.models.subscriber_model import Subscriber
from tests.conftest import register


def test_login_gives_the_same_answer_for_unknown_email_and_wrong_password(client):
    register(client, "nina@example.com")

    wrong_password = client.post(
        "/api/auth/login", json={"email": "nina@example.com", "password": "not-the-password"}
    )
    unknown_email = client.post(
        "/api/auth/login", json={"email": "nobody@example.com", "password": "not-the-password"}
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    # Identical, deliberately. Any "helpful" difference here turns login into a way to ask
    # whether an address has an account.
    assert wrong_password.json() == unknown_email.json()


def test_password_is_stored_hashed_and_never_returned(client, db):
    response = register(client, "nina@example.com", password="correct-horse-9")

    subscriber = db.scalar(select(Subscriber))
    assert subscriber.password_hash.startswith("$argon2")
    assert "correct-horse-9" not in subscriber.password_hash
    assert "password" not in response.text


def test_session_cookie_is_httponly_and_samesite_lax(client):
    response = register(client, "nina@example.com")

    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie
    # lax, never strict: Stripe Checkout returns via a cross-site top-level navigation and
    # strict would drop the cookie, silently logging the user out mid-purchase.
    assert "SameSite=lax" in cookie


def test_duplicate_registration_is_a_conflict(client, db):
    register(client, "nina@example.com")
    second = register(client, "nina@example.com")

    assert second.status_code == 409
    assert len(list(db.scalars(select(Subscriber)))) == 1


def test_me_requires_a_session(client):
    assert client.get("/api/subscribers/me").status_code == 401


def test_logout_ends_the_session(client):
    register(client, "nina@example.com")
    assert client.get("/api/subscribers/me").status_code == 200

    assert client.post("/api/auth/logout").status_code == 204
    client.cookies.clear()
    assert client.get("/api/subscribers/me").status_code == 401

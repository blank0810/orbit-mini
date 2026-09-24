"""Configuration behavior needed by hosted Postgres URLs."""

import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("database_url", "expected"),
    [
        (
            "postgresql://u:p@h:5432/db?sslmode=require&channel_binding=require",
            "postgresql+psycopg://u:p@h:5432/db?sslmode=require&channel_binding=require",
        ),
        ("postgres://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
        ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
    ],
)
def test_database_url_uses_psycopg_driver(database_url: str, expected: str) -> None:
    settings = Settings(database_url=database_url, jwt_secret="x" * 32)

    assert settings.database_url == expected

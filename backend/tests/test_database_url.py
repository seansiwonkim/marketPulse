from app.db.database import normalize_database_url

NEON = "ep-example-a1b2c3d4.us-east-1.aws.neon.tech/neondb?sslmode=require"


def test_plain_postgresql_url_gets_the_driver():
    assert normalize_database_url(f"postgresql://u:p@{NEON}") == f"postgresql+psycopg://u:p@{NEON}"


def test_postgres_scheme_gets_the_driver():
    assert normalize_database_url(f"postgres://u:p@{NEON}") == f"postgresql+psycopg://u:p@{NEON}"


def test_url_that_already_names_the_driver_is_unchanged():
    url = f"postgresql+psycopg://u:p@{NEON}"
    assert normalize_database_url(url) == url


def test_surrounding_whitespace_is_ignored():
    assert normalize_database_url(f"  postgresql://u:p@{NEON}\n").startswith("postgresql+psycopg://")

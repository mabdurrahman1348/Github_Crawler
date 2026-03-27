import os
import psycopg2
import psycopg2.extras
from crawler import Repository

def get_conn():
    """Create a database connection from environment variables."""
    return psycopg2.connect(
        host     = os.environ.get("PGHOST",     "localhost"),
        port     = os.environ.get("PGPORT",     "5432"),
        dbname   = os.environ.get("PGDATABASE", "github"),
        user     = os.environ.get("PGUSER",     "postgres"),
        password = os.environ.get("PGPASSWORD", "postgres"),
    )


def upsert_repositories(repos: list[Repository]) -> None:
    """
    Bulk upsert repositories.
    Only updates a row if star_count actually changed — minimal writes.
    """
    if not repos:
        return

    sql = """
        INSERT INTO repositories (id, node_id, name_with_owner, star_count)
        VALUES %s
        ON CONFLICT (id) DO UPDATE
            SET star_count = EXCLUDED.star_count,
                updated_at = NOW()
            WHERE repositories.star_count <> EXCLUDED.star_count
    """

    records = [
        (r.db_id, r.node_id, r.name_with_owner, r.star_count)
        for r in repos
    ]

    with get_conn() as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                sql,
                records,
                page_size=500
            )
        conn.commit()
    
    print(f"  💾 Upserted {len(records)} repos to DB")
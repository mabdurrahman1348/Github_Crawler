import csv
import os
from db import get_conn


def dump_csv(path: str = "output/repos.csv") -> None:
    """Export all repositories from DB to a CSV file."""
    
    os.makedirs("output", exist_ok=True)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name_with_owner, star_count, crawled_at, updated_at
                FROM repositories
                ORDER BY star_count DESC
            """)
            rows = cur.fetchall()

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name_with_owner", "star_count", "crawled_at", "updated_at"])
        writer.writerows(rows)

    print(f"  📄 Exported {len(rows)} rows → {path}")


if __name__ == "__main__":
    dump_csv()
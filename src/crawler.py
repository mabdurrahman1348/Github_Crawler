import os
import time
import requests
from dataclasses import dataclass
from typing import Iterator

GRAPHQL_URL = "https://api.github.com/graphql"

def _get_headers() -> dict:
    """Read token only when actually making a request."""
    token = os.environ.get("GITHUB_TOKEN")
    
    if not token:
        raise ValueError(
            "GITHUB_TOKEN is missing! Check your GitHub Actions 'env' section "
            "and ensure it maps to secrets.tokenn."
        )

    return {
        "Authorization": f"bearer {token}",
        "Content-Type":  "application/json",
    }

# --- Immutable domain model ---
@dataclass(frozen=True)
class Repository:
    db_id:           int
    node_id:         str
    name_with_owner: str
    star_count:      int


# --- GraphQL query ---
QUERY = """
query($cursor: String) {
  search(query: "stars:>0", type: REPOSITORY, first: 100, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on Repository {
        databaseId
        id
        nameWithOwner
        stargazerCount
      }
    }
  }
  rateLimit { remaining resetAt cost }
}
"""


def _post(cursor: str | None) -> dict:
    resp = requests.post(
        GRAPHQL_URL,
        json={"query": QUERY, "variables": {"cursor": cursor}},
        headers=_get_headers(),
        timeout=30,
    )


def _wait_for_rate_limit(rate: dict) -> None:
    """Sleep until reset if points are running low."""
    if rate["remaining"] < 10:
        import datetime
        reset_epoch = int(
            datetime.datetime.fromisoformat(
                rate["resetAt"].replace("Z", "+00:00")
            ).timestamp()
        )
        sleep_for = max(reset_epoch - int(time.time()) + 2, 1)
        print(f"  ⏳ Rate limit low — sleeping {sleep_for}s")
        time.sleep(sleep_for)


def crawl(target: int = 100_000) -> Iterator[Repository]:
    """Yield Repository objects until target count is reached."""
    cursor      = None
    collected   = 0
    retries     = 0
    max_retries = 5

    while collected < target:
        try:
            data   = _post(cursor)
            search = data["data"]["search"]
            rate   = data["data"]["rateLimit"]
            nodes  = search["nodes"]
            page   = search["pageInfo"]

        except (requests.RequestException, KeyError) as exc:
            retries += 1
            if retries > max_retries:
                raise RuntimeError("Too many consecutive failures") from exc
            wait = 2 ** retries
            print(f"  ⚠️  Error: {exc} — retrying in {wait}s ({retries}/{max_retries})")
            time.sleep(wait)
            continue

        retries = 0  # reset on success

        for node in nodes:
            if not node or collected >= target:
                break
            yield Repository(
                db_id           = node["databaseId"],
                node_id         = node["id"],
                name_with_owner = node["nameWithOwner"],
                star_count      = node["stargazerCount"],
            )
            collected += 1

        print(f"  ✅ Collected: {collected}/{target} — API points left: {rate['remaining']}")
        _wait_for_rate_limit(rate)

        if not page["hasNextPage"] or collected >= target:
            break
        cursor = page["endCursor"]

-- Repositories table (core data)
CREATE TABLE IF NOT EXISTS repositories (
    id              BIGINT PRIMARY KEY,
    node_id         TEXT UNIQUE NOT NULL,
    name_with_owner TEXT NOT NULL,
    star_count      INTEGER NOT NULL DEFAULT 0,
    crawled_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_repos_updated ON repositories(updated_at);
CREATE INDEX IF NOT EXISTS idx_repos_stars   ON repositories(star_count DESC);

-- Flexible metadata table for future data (issues, PRs, comments, etc.)
CREATE TABLE IF NOT EXISTS repo_metadata (
    id          BIGSERIAL PRIMARY KEY,
    repo_id     BIGINT NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    kind        TEXT NOT NULL,
    external_id TEXT NOT NULL,
    data        JSONB NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (repo_id, kind, external_id)
);

CREATE INDEX IF NOT EXISTS idx_meta_repo_kind ON repo_metadata(repo_id, kind);
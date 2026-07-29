CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id           bigserial primary key,
    github_id    bigint unique not null,
    github_login text not null,
    name         text,
    avatar_url   text,
    created_at   timestamptz default now(),
    updated_at   timestamptz default now()
)
"""

MIGRATIONS = (
    "ALTER TABLE users ALTER COLUMN github_id DROP NOT NULL",
    "ALTER TABLE users ALTER COLUMN github_login DROP NOT NULL",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS email text UNIQUE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash text",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS github_access_token text",
)

SET_GITHUB_TOKEN = "UPDATE users SET github_access_token=%s, updated_at=now() WHERE id=%s"

SELECT_GITHUB_TOKEN = "SELECT github_access_token FROM users WHERE id=%s"

UPSERT = """
INSERT INTO users (github_id, github_login, name, avatar_url, updated_at)
VALUES (%s, %s, %s, %s, now())
ON CONFLICT (github_id) DO UPDATE
    SET github_login = EXCLUDED.github_login,
        name         = EXCLUDED.name,
        avatar_url   = EXCLUDED.avatar_url,
        updated_at   = now()
RETURNING id
"""

CREATE_WITH_PASSWORD = """
INSERT INTO users (email, password_hash, updated_at)
VALUES (%s, %s, now())
RETURNING id
"""

LINK_GITHUB = """
UPDATE users
   SET github_id    = %s,
       github_login = %s,
       name         = %s,
       avatar_url   = %s,
       updated_at   = now()
 WHERE id = %s
"""

SELECT = """
SELECT id, github_id, github_login, name, avatar_url, email
FROM users
WHERE id = %s
"""

SELECT_BY_EMAIL = """
SELECT id, github_id, github_login, name, avatar_url, email, password_hash
FROM users
WHERE email = %s
"""

"""PostgreSQL persistence for accounts and user-owned chat history."""

from contextlib import contextmanager
from typing import Any, Iterator
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.utils.config import settings


class DuplicateEmailError(ValueError):
    pass


class ConversationNotFoundError(LookupError):
    pass


@contextmanager
def lock_conversation(conversation_id: UUID) -> Iterator[None]:
    """Serialize turns across app workers using a PostgreSQL advisory lock."""
    lock_key = str(conversation_id)
    with connect() as conn:
        conn.execute("SELECT pg_advisory_lock(hashtextextended(%s, 0))", (lock_key,))
        try:
            yield
        finally:
            conn.execute("SELECT pg_advisory_unlock(hashtextextended(%s, 0))", (lock_key,))


def connect() -> psycopg.Connection:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured.")
    return psycopg.connect(settings.database_url, row_factory=dict_row)


def initialize_database() -> None:
    """Create additive application tables; preserve existing checkpoint data."""
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_users (
                id UUID PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_conversations (
                id UUID PRIMARY KEY,
                user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
                title TEXT NOT NULL DEFAULT 'New chat',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_conversations_user_updated
            ON chat_conversations (user_id, updated_at DESC)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id UUID PRIMARY KEY,
                sequence_id BIGSERIAL NOT NULL UNIQUE,
                conversation_id UUID NOT NULL
                    REFERENCES chat_conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                confidence_score DOUBLE PRECISION,
                reason TEXT,
                sources JSONB NOT NULL DEFAULT '[]'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.execute(
            """ALTER TABLE chat_messages
               ADD COLUMN IF NOT EXISTS sequence_id BIGSERIAL"""
        )
        conn.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_chat_messages_sequence
               ON chat_messages (sequence_id)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_sequence
               ON chat_messages (conversation_id, sequence_id)"""
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation_created
            ON chat_messages (conversation_id, created_at, id)
            """
        )


def provision_admin(email: str, password_hash: str) -> None:
    """Provision the configured admin; public signup cannot assign this role."""
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO app_users (id, email, password_hash, role)
            VALUES (%s, %s, %s, 'admin')
            ON CONFLICT (email) DO UPDATE
            SET password_hash = EXCLUDED.password_hash,
                role = 'admin',
                updated_at = NOW()
            """,
            (uuid4(), email, password_hash),
        )


def create_user(email: str, password_hash: str) -> dict[str, Any]:
    user_id = uuid4()
    try:
        with connect() as conn:
            row = conn.execute(
                """
                INSERT INTO app_users (id, email, password_hash, role)
                VALUES (%s, %s, %s, 'user')
                RETURNING id, email, role, created_at
                """,
                (user_id, email, password_hash),
            ).fetchone()
        return row
    except psycopg.errors.UniqueViolation as exc:
        raise DuplicateEmailError("An account with this email already exists.") from exc


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with connect() as conn:
        return conn.execute(
            """SELECT id, email, password_hash, role, created_at
               FROM app_users WHERE email = %s""",
            (email,),
        ).fetchone()


def get_user_by_id(user_id: UUID) -> dict[str, Any] | None:
    with connect() as conn:
        return conn.execute(
            """SELECT id, email, role, created_at
               FROM app_users WHERE id = %s""",
            (user_id,),
        ).fetchone()


def create_conversation(
    user_id: UUID, title: str = "New chat", conversation_id: UUID | None = None
) -> dict[str, Any]:
    conversation_id = conversation_id or uuid4()
    with connect() as conn:
        return conn.execute(
            """INSERT INTO chat_conversations (id, user_id, title)
               VALUES (%s, %s, %s)
               RETURNING id, title, created_at, updated_at""",
            (conversation_id, user_id, title[:120]),
        ).fetchone()


def get_owned_conversation(user_id: UUID, conversation_id: UUID) -> dict[str, Any] | None:
    with connect() as conn:
        return conn.execute(
            """SELECT id, user_id, title, created_at, updated_at
               FROM chat_conversations WHERE id = %s AND user_id = %s""",
            (conversation_id, user_id),
        ).fetchone()


def list_conversations(user_id: UUID) -> list[dict[str, Any]]:
    with connect() as conn:
        return conn.execute(
            """SELECT id, title, created_at, updated_at
               FROM chat_conversations WHERE user_id = %s
               ORDER BY updated_at DESC""",
            (user_id,),
        ).fetchall()


def list_messages(user_id: UUID, conversation_id: UUID) -> list[dict[str, Any]]:
    with connect() as conn:
        owned = conn.execute(
            "SELECT 1 FROM chat_conversations WHERE id = %s AND user_id = %s",
            (conversation_id, user_id),
        ).fetchone()
        if not owned:
            raise ConversationNotFoundError
        return conn.execute(
            """SELECT role, content, confidence_score, reason, sources, created_at
               FROM chat_messages WHERE conversation_id = %s
               ORDER BY sequence_id""",
            (conversation_id,),
        ).fetchall()


def recent_conversation_history(
    user_id: UUID, conversation_id: UUID, limit: int = 12
) -> list[dict[str, str]]:
    with connect() as conn:
        owned = conn.execute(
            "SELECT 1 FROM chat_conversations WHERE id = %s AND user_id = %s",
            (conversation_id, user_id),
        ).fetchone()
        if not owned:
            raise ConversationNotFoundError
        rows = conn.execute(
            """SELECT role, content FROM chat_messages
               WHERE conversation_id = %s
               ORDER BY sequence_id DESC LIMIT %s""",
            (conversation_id, limit),
        ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]


def save_chat_turn(
    user_id: UUID,
    conversation_id: UUID,
    question: str,
    answer: str,
    confidence_score: float | None,
    reason: str | None,
    sources: list[dict[str, Any]],
) -> None:
    with connect() as conn:
        owned = conn.execute(
            "SELECT 1 FROM chat_conversations WHERE id = %s AND user_id = %s FOR UPDATE",
            (conversation_id, user_id),
        ).fetchone()
        if not owned:
            raise ConversationNotFoundError
        conn.execute(
            """INSERT INTO chat_messages (id, conversation_id, role, content)
               VALUES (%s, %s, 'user', %s)""",
            (uuid4(), conversation_id, question),
        )
        conn.execute(
            """INSERT INTO chat_messages
               (id, conversation_id, role, content, confidence_score, reason, sources)
               VALUES (%s, %s, 'assistant', %s, %s, %s, %s)""",
            (
                uuid4(), conversation_id, answer, confidence_score, reason,
                Jsonb(sources),
            ),
        )
        conn.execute(
            """UPDATE chat_conversations SET
                   title = CASE WHEN title = 'New chat' THEN %s ELSE title END,
                   updated_at = NOW()
               WHERE id = %s""",
            (question[:120], conversation_id),
        )

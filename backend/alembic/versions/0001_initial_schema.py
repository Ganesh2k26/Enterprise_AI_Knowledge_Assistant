"""initial schema (MySQL 8)

Revision ID: 0001
Revises:
Create Date: 2026-08-03
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GUID = sa.CHAR(36)


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("plan", sa.String(50), server_default="free"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )

    op.create_table(
        "users",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("owner", "admin", "member", name="userrole"), server_default="member"),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("is_email_verified", sa.Boolean, server_default=sa.false()),
        sa.Column("is_superuser", sa.Boolean, server_default=sa.false()),
        sa.Column("organization_id", GUID, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_organization_id", "users", ["organization_id"])

    op.create_table(
        "folders",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("owner_id", GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_folder_id", GUID, sa.ForeignKey("folders.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_folders_owner_id", "folders", ["owner_id"])
    op.create_index("ix_folders_parent_folder_id", "folders", ["parent_folder_id"])

    op.create_table(
        "documents",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger, server_default="0"),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "ready", "failed", name="documentstatus"),
            server_default="pending",
        ),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("is_favorite", sa.Boolean, server_default=sa.false()),
        sa.Column("is_scanned", sa.Boolean, server_default=sa.false()),
        sa.Column("embedding_count", sa.Integer, server_default="0"),
        sa.Column("owner_id", GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", GUID, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("folder_id", GUID, sa.ForeignKey("folders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"])
    op.create_index("ix_documents_organization_id", "documents", ["organization_id"])
    op.create_index("ix_documents_folder_id", "documents", ["folder_id"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_org_status", "documents", ["organization_id", "status"])

    op.create_table(
        "chunks",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("document_id", GUID, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_chunk_id", GUID, sa.ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("page_number", sa.Integer, nullable=True),
        sa.Column("token_count", sa.Integer, server_default="0"),
        sa.Column("vector_id", sa.String(64), nullable=False),
        sa.Column("chunk_metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_chunks_document_id", "chunks", ["document_id"])
    op.create_index("ix_chunks_document_index", "chunks", ["document_id", "chunk_index"])

    op.create_table(
        "chat_sessions",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("title", sa.String(255), server_default="New Chat"),
        sa.Column("user_id", GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_ids", sa.JSON, nullable=True),
        sa.Column("is_favorite", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_index("ix_chat_sessions_user_updated", "chat_sessions", ["user_id", "updated_at"])

    op.create_table(
        "chat_messages",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("session_id", GUID, sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Enum("user", "assistant", "system", name="messagerole"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("citations", sa.JSON, nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True),
        sa.Column("token_usage", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_index("ix_chat_messages_session_created", "chat_messages", ["session_id", "created_at"])

    op.create_table(
        "usage_logs",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("user_id", GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", GUID, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(50), nullable=True),
        sa.Column("prompt_tokens", sa.Integer, server_default="0"),
        sa.Column("completion_tokens", sa.Integer, server_default="0"),
        sa.Column("latency_ms", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_usage_logs_user_id", "usage_logs", ["user_id"])
    op.create_index("ix_usage_logs_organization_id", "usage_logs", ["organization_id"])
    op.create_index("ix_usage_logs_action", "usage_logs", ["action"])
    op.create_index("ix_usage_logs_org_created", "usage_logs", ["organization_id", "created_at"])

    op.create_table(
        "feedback",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("user_id", GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", GUID, sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=True),
        sa.Column("message_id", GUID, sa.ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Enum("up", "down", name="feedbackrating"), nullable=False),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])
    op.create_index("ix_feedback_document_id", "feedback", ["document_id"])
    op.create_index("ix_feedback_message_id", "feedback", ["message_id"])

    op.create_table(
        "settings",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("organization_id", GUID, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("organization_id", "key", name="uq_settings_org_key"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_settings_organization_id", "settings", ["organization_id"])

    op.create_table(
        "api_keys",
        sa.Column("id", GUID, primary_key=True),
        sa.Column("user_id", GUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("key_prefix", sa.String(12), nullable=False),
        sa.Column("hashed_key", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true()),
        sa.Column("last_used_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("settings")
    op.drop_table("feedback")
    op.drop_table("usage_logs")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("chunks")
    op.drop_table("documents")
    op.drop_table("folders")
    op.drop_table("users")
    op.drop_table("organizations")

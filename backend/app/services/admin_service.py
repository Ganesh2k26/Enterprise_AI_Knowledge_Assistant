"""Aggregate queries backing the admin dashboard. Scoped to the caller's organization."""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.usage import UsageLog
from app.models.user import User


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview(self, organization_id: uuid.UUID) -> dict:
        user_count = await self.db.scalar(
            select(func.count(User.id)).where(User.organization_id == organization_id)
        )
        doc_count = await self.db.scalar(
            select(func.count(Document.id)).where(Document.organization_id == organization_id)
        )
        failed_count = await self.db.scalar(
            select(func.count(Document.id)).where(
                Document.organization_id == organization_id, Document.status == DocumentStatus.FAILED
            )
        )
        total_storage = await self.db.scalar(
            select(func.coalesce(func.sum(Document.file_size_bytes), 0)).where(
                Document.organization_id == organization_id
            )
        )
        total_embeddings = await self.db.scalar(
            select(func.coalesce(func.sum(Document.embedding_count), 0)).where(
                Document.organization_id == organization_id
            )
        )

        since = datetime.now(timezone.utc) - timedelta(days=30)
        usage_result = await self.db.execute(
            select(UsageLog.action, func.count(UsageLog.id), func.avg(UsageLog.latency_ms))
            .where(UsageLog.organization_id == organization_id, UsageLog.created_at >= since)
            .group_by(UsageLog.action)
        )
        usage_by_action = [
            {"action": action, "count": count, "avg_latency_ms": round(avg_latency or 0, 1)}
            for action, count, avg_latency in usage_result.all()
        ]

        recent_docs_result = await self.db.execute(
            select(Document)
            .where(Document.organization_id == organization_id)
            .order_by(Document.created_at.desc())
            .limit(10)
        )
        recent_documents = list(recent_docs_result.scalars().all())

        return {
            "registered_users": user_count or 0,
            "uploaded_documents": doc_count or 0,
            "failed_documents": failed_count or 0,
            "storage_used_bytes": int(total_storage or 0),
            "embedding_count": int(total_embeddings or 0),
            "usage_last_30_days": usage_by_action,
            "recent_documents": [
                {
                    "id": str(d.id),
                    "filename": d.filename,
                    "status": d.status.value,
                    "file_size_bytes": d.file_size_bytes,
                    "created_at": d.created_at.isoformat(),
                }
                for d in recent_documents
            ],
        }

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_setting import OrgSetting
from app.repositories.base import BaseRepository


class OrgSettingRepository(BaseRepository[OrgSetting]):
    def __init__(self, db: AsyncSession):
        super().__init__(OrgSetting, db)

    async def list_for_org(self, organization_id: uuid.UUID) -> list[OrgSetting]:
        result = await self.db.execute(select(OrgSetting).where(OrgSetting.organization_id == organization_id))
        return list(result.scalars().all())

    async def get_by_key(self, organization_id: uuid.UUID, key: str) -> OrgSetting | None:
        result = await self.db.execute(
            select(OrgSetting).where(OrgSetting.organization_id == organization_id, OrgSetting.key == key)
        )
        return result.scalar_one_or_none()

    async def upsert(self, organization_id: uuid.UUID, key: str, value: str) -> OrgSetting:
        existing = await self.get_by_key(organization_id, key)
        if existing:
            existing.value = value
            return await self.commit_refresh(existing)
        return await self.create(organization_id=organization_id, key=key, value=value)

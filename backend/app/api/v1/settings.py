from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.org_setting_repository import OrgSettingRepository
from app.schemas.org_setting import OrgSettingRead, OrgSettingUpsert

router = APIRouter()


@router.get("", response_model=list[OrgSettingRead])
async def list_settings(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    rows = await OrgSettingRepository(db).list_for_org(user.organization_id)
    return [OrgSettingRead(key=r.key, value=r.value) for r in rows]


@router.put("", response_model=OrgSettingRead)
async def upsert_setting(
    payload: OrgSettingUpsert, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    row = await OrgSettingRepository(db).upsert(user.organization_id, payload.key, payload.value)
    return OrgSettingRead(key=row.key, value=row.value)

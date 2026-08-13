from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.database.session import get_db
from app.models.user import User
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("/overview")
async def get_admin_overview(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    return await AdminService(db).get_overview(admin.organization_id)

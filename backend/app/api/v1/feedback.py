from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import ValidationAppError
from app.database.session import get_db
from app.models.feedback import FeedbackRating
from app.models.user import User
from app.repositories.feedback_repository import FeedbackRepository
from app.schemas.feedback import FeedbackCreate

router = APIRouter()


@router.post("", status_code=201)
async def submit_feedback(
    payload: FeedbackCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    if payload.rating not in ("up", "down"):
        raise ValidationAppError("rating must be 'up' or 'down'.")
    repo = FeedbackRepository(db)
    feedback = await repo.create(
        user_id=user.id,
        document_id=payload.document_id,
        message_id=payload.message_id,
        rating=FeedbackRating(payload.rating),
        comment=payload.comment,
    )
    return {"id": str(feedback.id), "rating": feedback.rating.value}

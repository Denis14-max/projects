import uuid

from fastapi import APIRouter, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User, Media
from app.schemas import MediaResponse

router = APIRouter(prefix="/api/medias", tags=["Медиа"])


async def save_image_to_disk(file: UploadFile) -> str:
    """Сохраняет картинку на диск и возвращает путь для базы данных"""
    extension = file.filename.split('.')[-1]
    new_filename = f"{uuid.uuid4()}.{extension}"

    with open(f"static/img/{new_filename}", "wb") as f:
        f.write(await file.read())

    return f"/img/{new_filename}"


@router.post("", response_model=MediaResponse, summary="Загрузить медиафайл")
async def upload_media(
        file: UploadFile,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """Загрузка медиафайлов для твита"""
    saved_path = await save_image_to_disk(file)

    new_media = Media(file_path=saved_path)
    db.add(new_media)
    await db.commit()

    return MediaResponse(result=True, media_id=new_media.id)

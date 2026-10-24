from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SuccessResponse(BaseModel):
    """Успешный ответ без данных"""
    result: bool = Field(True, description="Признак успешного выполнения")


class ErrorResponse(BaseModel):
    """Ответ при ошибке (единый формат для всех эндпоинтов)"""
    result: bool = Field(False, description="Всегда false при ошибке")
    error_type: str = Field(..., description="Тип ошибки")
    error_message: str = Field(..., description="Описание ошибки")


class UserBase(BaseModel):
    """Краткие данные пользователя"""
    id: int = Field(..., description="ID пользователя")
    name: str = Field(..., description="Имя пользователя")

    model_config = ConfigDict(from_attributes=True)


class UserProfileOut(UserBase):
    """Профиль пользователя с подписчиками и подписками"""
    followers: List[UserBase] = Field(
        default_factory=list, description="Кто подписан на пользователя"
    )
    following: List[UserBase] = Field(
        default_factory=list, description="На кого подписан пользователь"
    )


class UserResponse(SuccessResponse):
    """Ответ с профилем пользователя"""
    user: UserProfileOut = Field(..., description="Профиль пользователя")


class MediaOut(BaseModel):
    id: int
    file_path: str

    model_config = ConfigDict(from_attributes=True)


class MediaResponse(SuccessResponse):
    """Ответ после загрузки картинки"""
    media_id: int = Field(..., description="ID загруженной картинки")


class TweetIn(BaseModel):
    """Тело запроса на создание твита"""
    tweet_data: str = Field(..., min_length=1, max_length=500, description="Текст твита")
    tweet_media_ids: Optional[List[int]] = []


class TweetCreateResponse(SuccessResponse):
    tweet_id: int


class LikeOut(BaseModel):
    user_id: int
    name: str


class TweetOut(BaseModel):
    """Твит в ленте"""
    id: int = Field(..., description="ID твита")
    content: str = Field(..., description="Текст твита")
    stamp: datetime
    created_at: datetime
    attachments: List[str] = []
    author: UserBase
    likes: List[LikeOut] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("attachments", mode="before")
    @classmethod
    def extract_file_paths(cls, media_list):
        """Пробегается по объектам Media из БД и вытаскивает только пути к файлам"""
        return [media.file_path for media in media_list]

    @field_validator("likes", mode="before")
    @classmethod
    def format_likes(cls, likes_list):
        """Берет пользователей из БД и переименовывает поле id в user_id"""
        return [{"user_id": user.id, "name": user.name} for user in likes_list]


class TweetListResponse(SuccessResponse):
    """Лента твитов"""
    tweets: List[TweetOut] = Field(..., description="Список твитов")

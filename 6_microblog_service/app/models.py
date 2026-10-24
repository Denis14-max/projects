from datetime import datetime
from typing import List, Optional
from sqlalchemy import ForeignKey, Column, Table, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

likes_table = Table(
    "likes",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("tweet_id", ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True),
)

followers_table = Table(
    "followers",
    Base.metadata,
    Column("follower_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("following_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    api_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    tweets: Mapped[List["Tweet"]] = relationship(back_populates="author", cascade="all, delete-orphan")

    following: Mapped[List["User"]] = relationship(
        "User",
        secondary=followers_table,
        primaryjoin=id == followers_table.c.follower_id,
        secondaryjoin=id == followers_table.c.following_id,
        backref="followers",
        lazy="selectin"
    )


class Tweet(Base):
    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    content: Mapped[str] = mapped_column(String(2000), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    author: Mapped["User"] = relationship(back_populates="tweets")
    attachments: Mapped[List["Media"]] = relationship(back_populates="tweet", cascade="all, delete-orphan")
    likes: Mapped[List["User"]] = relationship(secondary=likes_table)

    @property
    def stamp(self):
        """Помогает отобразить реальное время создания твита"""
        return self.created_at


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    tweet_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tweets.id", ondelete="SET NULL"))

    tweet: Mapped[Optional["Tweet"]] = relationship(back_populates="attachments")

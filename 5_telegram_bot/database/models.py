from datetime import datetime
from peewee import Model, CharField, BigIntegerField, DateTimeField, ForeignKeyField, TextField

from database.db_setup import db


class BaseModel(Model):
    """Базовый класс, который указывает всем таблицам использовать наше подключение 'db'"""

    class Meta:
        database = db


class User(BaseModel):
    """Таблица для хранения пользователей бота"""
    telegram_id = BigIntegerField(unique=True)
    username = CharField(null=True)
    created_at = DateTimeField(default=datetime.now)


class Note(BaseModel):
    """Таблица для сохранения заметок и напоминаний"""
    user = ForeignKeyField(User, backref='notes', on_delete='CASCADE')
    text = TextField()
    remind_date = CharField()
    created_at = DateTimeField(default=datetime.now)


class SearchHistory(BaseModel):
    """Таблица для сохранения истории поиска отелей"""
    user = ForeignKeyField(User, backref='history', on_delete='CASCADE')
    command = CharField()
    result = TextField()
    created_at = DateTimeField(default=datetime.now)


def create_tables():
    """Функция для автоматического создания таблиц в СУБД"""
    with db:
        db.create_tables([User, Note, SearchHistory])

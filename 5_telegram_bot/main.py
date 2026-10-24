from database.db_setup import db
import handlers.base_handlers
import handlers.note_handlers
import handlers.hotel_handlers
from database.models import create_tables
from loader import bot

if __name__ == '__main__':
    with db:
        create_tables()

    bot.infinity_polling()

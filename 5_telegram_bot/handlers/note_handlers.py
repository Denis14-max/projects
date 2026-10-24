from loader import bot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.models import User, Note

temp_note_data = {}


def get_back_keyboard():
    """Создает кнопку возврата в главное меню"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu"))
    return keyboard


@bot.message_handler(commands=['addnote'])
def add_note_start(message: Message):
    bot.send_message(message.chat.id, "Напишите текст заметки, которую хотите сохранить:")
    bot.register_next_step_handler(message, process_note_text)


def process_note_text(message: Message):
    if not message.text:
        msg = bot.send_message(message.chat.id, "Пожалуйста, отправьте текст заметки")
        bot.register_next_step_handler(msg, process_note_text)
        return
    temp_note_data[message.chat.id] = {'text': message.text}
    bot.send_message(message.chat.id, "Отлично! Теперь напишите дату или время:")
    bot.register_next_step_handler(message, process_note_date)


def process_note_date(message: Message):
    if not message.text:
        msg = bot.send_message(message.chat.id, "Пожалуйста, отправьте дату или время текстом.")
        bot.register_next_step_handler(msg, process_note_date)
        return
    user = User.get_or_none(User.telegram_id == message.chat.id)
    if user:
        user_note = temp_note_data.get(message.chat.id)
        if not user_note:
            bot.send_message(message.chat.id, "❌ Данные заметки устарели. Начните заново командой /addnote")
            return
        note_text = temp_note_data[message.chat.id]['text']
        remind_date = message.text
        Note.create(user=user, text=note_text, remind_date=remind_date)

        bot.send_message(message.chat.id, "✅ Заметка успешно сохранена!", reply_markup=get_back_keyboard())
    else:
        bot.send_message(message.chat.id, "❌ Ошибка: пожалуйста, отправьте сначала команду /start")

    if message.chat.id in temp_note_data:
        del temp_note_data[message.chat.id]


@bot.message_handler(commands=['notes'])
def show_notes(message: Message):
    user = User.get_or_none(User.telegram_id == message.chat.id)
    if not user or not user.notes:
        bot.send_message(message.chat.id, "У вас пока нет сохраненных заметок 📝", reply_markup=get_back_keyboard())
        return

    bot.send_message(message.chat.id, "Ваши заметки:")

    for note in user.notes:
        text = f"*{note.text}*\n🕒 Напоминание: {note.remind_date}"

        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("❌ Удалить", callback_data=f"del_note_{note.id}"))

        bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=keyboard)
    bot.send_message(message.chat.id, "Действия:", reply_markup=get_back_keyboard())


def delete_note(call: CallbackQuery):
    """Удаляет заметку по ее ID"""
    try:
        note_id = int(call.data.split('_')[2])
        note = Note.get_or_none(Note.id == note_id)

        if note:
            note.delete_instance()
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.answer_callback_query(call.id, "✅ Заметка удалена!")
        else:
            bot.answer_callback_query(call.id, "Заметка уже удалена.")
    except Exception as e:
        print(f"Ошибка при удалении заметки: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка при удалении.")

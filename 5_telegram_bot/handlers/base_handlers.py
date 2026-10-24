from database.models import User
from loader import bot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from handlers.note_handlers import add_note_start, show_notes


def get_menu_keyboard():
    """Клавиатура с кнопками для главного меню"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.add(
        InlineKeyboardButton("🏨 Найти отель", callback_data="menu_hotels"),
        InlineKeyboardButton("📜 История поисков", callback_data="menu_history"),
        InlineKeyboardButton("📝 Добавить заметку", callback_data="menu_add_note"),
        InlineKeyboardButton("📋 Мои заметки", callback_data="menu_show_notes")
    )
    return keyboard


def send_main_menu(chat_id: int, first_name: str):
    """Общая функция для отрисовки главного меню"""
    caption_text = (
        f"Привет, {first_name}! 👋\n\n"
        "Я ваш бот-помощник. Выберите нужное действие в меню ниже. "
        "Эту панель всегда можно вызвать командой /menu."
    )

    with open('static/img/photo-bot.jpg', 'rb') as photo:
        bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption_text,
            reply_markup=get_menu_keyboard()
        )


@bot.message_handler(commands=['start', 'menu'])
def send_welcome(message: Message):
    """Обработчик базовых команд"""
    user, created = User.get_or_create(
        telegram_id=message.chat.id,
        defaults={'username': message.from_user.username}
    )
    send_main_menu(message.chat.id, message.from_user.first_name)


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("menu_") or call.data in ["back_to_menu", "save_summary_note",
                                                                     "save_card_note"] or call.data.startswith(
        "del_note_"))
def handle_all_callbacks(call: CallbackQuery):
    """Единый обработчик callback-запросов только для меню и заметок"""
    bot.answer_callback_query(call.id)

    if call.data == "menu_add_note":
        add_note_start(call.message)
    elif call.data == "menu_show_notes":
        show_notes(call.message)
    elif call.data == "menu_hotels":
        from handlers.hotel_handlers import start_hotel_search
        start_hotel_search(call.message)
    elif call.data == "back_to_menu":
        send_main_menu(call.message.chat.id, call.from_user.first_name)
    elif call.data == "save_summary_note":
        from handlers.hotel_handlers import user_search_data
        from handlers.note_handlers import temp_note_data, process_note_date

        summary_text = user_search_data.get(call.message.chat.id, {}).get('summary', 'Сводка отеля')
        temp_note_data[call.message.chat.id] = {'text': summary_text}

        msg = bot.send_message(call.message.chat.id, "Отлично! Теперь напишите дату или время для напоминания:")
        bot.register_next_step_handler(msg, process_note_date)
    elif call.data == "menu_history":
        show_history(call.message)

    elif call.data == "save_card_note":
        from handlers.hotel_handlers import user_search_data
        from handlers.note_handlers import temp_note_data, process_note_date

        hotel_text = user_search_data.get(call.message.chat.id, {}).get('current_hotel_text', 'Информация об отеле')
        temp_note_data[call.message.chat.id] = {'text': hotel_text}

        msg = bot.send_message(call.message.chat.id, "Отлично! Теперь напишите дату или время для напоминания:")
        bot.register_next_step_handler(msg, process_note_date)

    elif call.data.startswith("del_note_"):
        from handlers.note_handlers import delete_note
        delete_note(call)


@bot.message_handler(commands=['history'])
def show_history(message: Message):
    """Выводит историю поиска в виде кнопок"""
    from database.models import User, SearchHistory

    user = User.get_or_none(User.telegram_id == message.chat.id)
    if not user or not user.history.count():
        bot.send_message(message.chat.id, "Ваша история поисков пока что пуста ")
        return

    history_records = user.history.order_by(SearchHistory.created_at.desc()).limit(5)

    keyboard = InlineKeyboardMarkup(row_width=1)
    for record in history_records:
        date_str = record.created_at.strftime("%d.%m %H:%M")

        import json
        try:
            data = json.loads(record.result)
            city_name = data.get('city', 'Город')
        except:
            city_name = record.result

        btn_text = f"📍 {city_name} ({record.command}) - {date_str}"
        keyboard.add(InlineKeyboardButton(text=btn_text, callback_data=f"load_hist_{record.id}"))

    keyboard.add(InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu"))
    bot.send_message(message.chat.id,
                     "📜 *Ваши последние запросы:*\n(Нажмите на локацию, чтобы посмотреть найденные отели)",
                     reply_markup=keyboard, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data.startswith("load_hist_"))
def load_history_search(call):
    """Загружает результаты из базы и показывает карточки"""
    import json
    from database.models import SearchHistory
    from handlers.hotel_handlers import user_search_data, send_hotel_card

    bot.answer_callback_query(call.id, "Загружаю результаты...")

    hist_id = call.data.split('_')[2]
    record = SearchHistory.get_or_none(SearchHistory.id == hist_id)

    if record:
        try:
            payload = json.loads(record.result)

            user_search_data[call.message.chat.id] = {
                'found_hotels': payload.get('hotels', []),
                'checkin': payload.get('checkin', ''),
                'checkout': payload.get('checkout', ''),
                'current_hotel_index': 0,
                'search_date': record.created_at.strftime("%d.%m.%Y %H:%M")
            }

            bot.delete_message(call.message.chat.id, call.message.message_id)
            send_hotel_card(call.message.chat.id)
        except Exception as e:
            bot.send_message(call.message.chat.id, "❌ Ошибка чтения старой записи. Возможно, данные устарели.")


@bot.message_handler(commands=['help'])
def send_help(message):
    """Выводит справочную информацию по командам и функциям бота"""
    help_text = (
        "*Справка по использованию бота*\n\n"
        "Я помогаю искать отели по всему миру, сортировать их по вашему бюджету и сохранять интересные варианты в заметки.\n\n"
        "*Основные команды:*\n"
        "1) /start, /menu — Запустить бота и открыть главное меню\n"
        "2) /help — Показать это справочное сообщение\n"
        "3) /history — Посмотреть историю ваших запросов\n\n"
        "*Команды поиска (также доступны через кнопки в меню):*\n"
        "1) /lowprice — Поиск самых дешевых отелей\n"
        "2) /highprice — Поиск самых дорогих отелей\n"
        "3) /bestdeal — Поиск лучших предложений по рейтингу\n\n"
        "*Как пользоваться:*\n"
        "1) Нажмите «Найти отель» в меню или введите команду поиска.\n"
        "2) Напишите название города (например, Лондон).\n"
        "3) Выберите даты заезда и выезда в удобном календаре.\n"
        "4) Укажите ваш бюджет (например, 50-150).\n"
        "5) Листайте карточки отелей, смотрите фото и сохраняйте нужные в «Мои заметки» с напоминанием!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")


@bot.message_handler(commands=['lowprice', 'highprice', 'bestdeal'])
def handle_search_commands(message: Message):
    """Обрабатывает команды поиска, введенные вручную"""
    command = message.text.strip('/')
    from handlers.hotel_handlers import user_search_data, process_city_search

    user_search_data[message.chat.id] = {'command': command}

    commands_ru = {
        'lowprice': 'Сначала дешевые 📉',
        'highprice': 'Сначала дорогие 📈',
        'bestdeal': 'Лучшие предложения 🌟'
    }

    msg = bot.send_message(
        message.chat.id,
        f"Вы выбрали режим: *{commands_ru.get(command)}*\n\nВведите название города для поиска:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_city_search)

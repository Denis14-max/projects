import datetime
import json
from telegram_bot_calendar import DetailedTelegramCalendar
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from api_hotels import get_city_destinations, get_hotels_data
from loader import bot
from database.models import User, SearchHistory

user_search_data = {}
step_ru = {'y': 'год', 'm': 'месяц', 'd': 'день'}


def start_hotel_search(message: Message):
    """Срабатывает при нажатии на кнопку поиск отелей и предлагает выбрать сортировку"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📉 Сначала дешевые", callback_data="sort_lowprice"),
        InlineKeyboardButton("📈 Сначала дорогие", callback_data="sort_highprice"),
        InlineKeyboardButton("🌟 Лучшие предложения", callback_data="sort_bestdeal"),
        InlineKeyboardButton("⬅️ В меню", callback_data="back_to_menu")
    )
    bot.send_message(message.chat.id, "Выберите режим поиска:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("sort_"))
def handle_sort_choice(call: CallbackQuery):
    """Ловит выбор сортировки через кнопку, сохраняет и просит город"""
    bot.answer_callback_query(call.id)

    command = call.data.split('_')[1]

    user_search_data[call.message.chat.id] = {'command': command}

    commands_ru = {
        'lowprice': 'Сначала дешевые 📉',
        'highprice': 'Сначала дорогие 📈',
        'bestdeal': 'Лучшие предложения 🌟'
    }

    msg = bot.edit_message_text(
        f"Вы выбрали режим: *{commands_ru.get(command)}*\n\nВведите название города для поиска:",
        call.message.chat.id,
        call.message.message_id,
        parse_mode="Markdown"
    )

    bot.register_next_step_handler(msg, process_city_search)


def process_city_search(message: Message):
    """Принимает текст, автоматически находит ID города и сразу открывает календарь"""
    if not message.text:
        msg = bot.send_message(message.chat.id, "Пожалуйста, введите название города текстом.")
        bot.register_next_step_handler(msg, process_city_search)
        return
    city_name = message.text
    search_msg = bot.send_message(message.chat.id, f"🔍 Ищу город *{city_name}*...", parse_mode="Markdown")

    results = get_city_destinations(city_name)

    bot.delete_message(message.chat.id, search_msg.message_id)

    if results is None:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="menu_hotels"))
        bot.send_message(
            message.chat.id,
            " Ошибка связи с сервером Booking API. Пожалуйста, попробуйте позже.",
            reply_markup=keyboard
        )
        return
    elif not results:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data="menu_hotels"))
        bot.send_message(
            message.chat.id,
            "К сожалению, город не найден. Попробуйте ввести название иначе.",
            reply_markup=keyboard
        )
        return

    city_data = next((item for item in results if item.get('dest_type') == 'city'), results[0])

    loc_name = city_data.get('name', city_name)
    dest_id = city_data.get('dest_id')
    dest_type = city_data.get('dest_type', 'city')

    user_data = user_search_data.get(message.chat.id, {})
    user_data['dest_id'] = dest_id
    user_data['name'] = loc_name
    user_data['dest_type'] = dest_type
    user_search_data[message.chat.id] = user_data

    calendar, step = DetailedTelegramCalendar(calendar_id=1, min_date=datetime.date.today(), locale='ru').build()

    bot.send_message(
        message.chat.id,
        f"✅ Город найден: *{loc_name}*.\n\nВыберите {step_ru[step]} заезда:",
        reply_markup=calendar,
        parse_mode="Markdown"
    )


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=1))
def handle_checkin_date(call):
    """Обрабатывает нажатия на кнопки календаря заезда"""
    result, key, step = DetailedTelegramCalendar(calendar_id=1, min_date=datetime.date.today(), locale='ru').process(
        call.data)

    if not result and key:
        bot.edit_message_text(f"Выберите {step_ru[step]} заезда:", call.message.chat.id, call.message.message_id,
                              reply_markup=key)
    elif result:
        user_data = user_search_data.get(call.message.chat.id)
        if user_data is None:
            bot.answer_callback_query(call.id, "Поиск устарел. Начните заново командой /menu", show_alert=True)
            return
        user_data['checkin'] = result
        user_search_data[call.message.chat.id]['checkin'] = result
        min_checkout = result + datetime.timedelta(days=1)
        calendar, step = DetailedTelegramCalendar(calendar_id=2, min_date=min_checkout, locale='ru').build()
        bot.edit_message_text(
            f"✅ Дата заезда: {result}\n\nТеперь выберите {step_ru[step]} выезда:",
            call.message.chat.id, call.message.message_id, reply_markup=calendar
        )


@bot.callback_query_handler(func=DetailedTelegramCalendar.func(calendar_id=2))
def handle_checkout_date(call):
    """Обрабатывает выбор даты выезда и сразу просит цену"""
    user_data = user_search_data.get(call.message.chat.id)
    if not user_data or not user_data.get('checkin'):
        bot.answer_callback_query(call.id, "Поиск устарел. Начните заново командой /menu", show_alert=True)
        return
    checkin_date = user_search_data[call.message.chat.id].get('checkin')
    min_checkout = checkin_date + datetime.timedelta(days=1)

    result, key, step = DetailedTelegramCalendar(calendar_id=2, min_date=min_checkout, locale='ru').process(call.data)

    if not result and key:
        bot.edit_message_text(f"Выберите {step_ru[step]} выезда:", call.message.chat.id, call.message.message_id,
                              reply_markup=key)
    elif result:
        user_search_data[call.message.chat.id]['checkout'] = result

        bot.edit_message_text(
            f"✅ Даты сохранены!\n\nВведите желаемый диапазон цен за ночь (в долларах) через дефис:",
            call.message.chat.id, call.message.message_id
        )
        bot.register_next_step_handler(call.message, process_price_range)


def process_price_range(message: Message):
    """Обрабатывает введенный диапазон цен, фильтрует, сортирует и сохраняет историю"""
    price_text = message.text or ''

    try:
        prices = price_text.replace(' ', '').split('-')
        if len(prices) != 2:
            raise ValueError

        min_price, max_price = int(prices[0]), int(prices[1])
        if min_price > max_price:
            min_price, max_price = max_price, min_price

        user_data = user_search_data[message.chat.id]
        user_data['min_price'] = min_price
        user_data['max_price'] = max_price

        msg_wait = bot.send_message(message.chat.id, "⏳Пожалуйста, подождите...")

        dest_id = user_data.get('dest_id')
        dest_type = user_data.get('dest_type', 'city')
        checkin = user_data.get('checkin')
        checkout = user_data.get('checkout')

        hotels_data = get_hotels_data(dest_id, dest_type, checkin, checkout)

        if not hotels_data:
            bot.edit_message_text(
                "❌ К сожалению, не удалось получить данные об отелях на эти даты.",
                message.chat.id,
                msg_wait.message_id
            )
            return

        filtered_hotels = []
        for hotel in hotels_data:
            property_info = hotel.get('property', {})
            price_breakdown = property_info.get('priceBreakdown') or hotel.get('priceBreakdown') or {}
            gross_price = price_breakdown.get('grossPrice') or {}

            price = gross_price.get('value', 0)

            if price > 0 and (min_price <= price <= max_price):
                hotel['extracted_price'] = price
                hotel['extracted_rating'] = property_info.get('reviewScore', 0)
                filtered_hotels.append(hotel)

        if not filtered_hotels:
            bot.edit_message_text(
                f"❌ В диапазоне от {min_price}$ до {max_price}$ ничего не найдено. Попробуйте увеличить бюджет.",
                message.chat.id,
                msg_wait.message_id
            )
            return

        command = user_data.get('command', 'lowprice')

        if command == 'lowprice':
            filtered_hotels.sort(key=lambda x: x['extracted_price'])
        elif command == 'highprice':
            filtered_hotels.sort(key=lambda x: x['extracted_price'], reverse=True)
        elif command == 'bestdeal':
            filtered_hotels.sort(key=lambda x: x['extracted_rating'], reverse=True)

        user_data['found_hotels'] = filtered_hotels

        user = User.get_or_none(User.telegram_id == message.chat.id)
        if user:
            cmd = user_data.get('command', 'lowprice')
            commands_ru = {'lowprice': 'Дешевые', 'highprice': 'Дорогие', 'bestdeal': 'Лучшие'}
            loc_name = user_data.get('name', 'Неизвестный город')

            history_payload = {
                'city': loc_name,
                'checkin': str(checkin),
                'checkout': str(checkout),
                'hotels': filtered_hotels
            }

            SearchHistory.create(
                user=user,
                command=commands_ru.get(cmd, cmd),
                result=json.dumps(history_payload, ensure_ascii=False)
            )

        user_data['current_hotel_index'] = 0
        bot.delete_message(message.chat.id, msg_wait.message_id)
        send_hotel_card(message.chat.id)

    except ValueError:
        msg = bot.send_message(message.chat.id,
                               "❌ Ошибка формата. Пожалуйста, введите две цифры через дефис (например: 50-150):")
        bot.register_next_step_handler(msg, process_price_range)


def send_hotel_card(chat_id):
    """Формирует и отправляет расширенную карточку конкретного отеля"""
    user_data = user_search_data.get(chat_id, {})
    hotels = user_data.get('found_hotels', [])
    index = user_data.get('current_hotel_index', 0)

    if not hotels:
        bot.send_message(chat_id, "К сожалению, список отелей пуст.")
        return

    hotel = hotels[index]
    property_info = hotel.get('property', {})

    name = property_info.get('name', 'Название не указано')
    rating = property_info.get('reviewScore', 'Нет оценок')

    description = hotel.get('accessibilityLabel', 'Описание отсутствует').replace('\n', ' ')
    if len(description) > 150:
        description = description[:150] + "..."

    lat = property_info.get('latitude', 'Неизвестно')
    lon = property_info.get('longitude', 'Неизвестно')
    coordinates = f"{lat}, {lon}"

    hotel_id = hotel.get('id') or property_info.get('id', '')
    link = f"https://www.booking.com/hotel/index.html?hotel_id={hotel_id}" if hotel_id else "Ссылка недоступна"

    checkin = user_data.get('checkin', 'Не указано')
    checkout = user_data.get('checkout', 'Не указано')

    price_breakdown = property_info.get('priceBreakdown') or hotel.get('priceBreakdown') or {}
    gross_price = price_breakdown.get('grossPrice') or {}
    amount_rounded = gross_price.get('amountRounded')
    if amount_rounded:
        price_text = amount_rounded
    else:
        val = gross_price.get('value')
        cur = gross_price.get('currency', 'USD')
        price_text = f"{round(val, 2)} {cur}" if val else "Нет мест на эти даты"

    text = f"🏨 *Отель:* {name}\n"

    if 'search_date' in user_data:
        text += f"🕰 *Дата поиска:* {user_data['search_date']}\n"

    text += (
        f"📅 *Выбранные даты:* {checkin} — {checkout}\n"
        f"⭐ *Рейтинг:* {rating}\n"
        f"💰 *Цена:* {price_text}\n"
        f"📍 *Координаты:* `{coordinates}`\n"
        f"🔗 *Бронь:* [Перейти на Booking]({link})\n\n"
        f"📝 *Описание:* {description}\n\n"
        f"📄 *Результат:* {index + 1} из {len(hotels)}"
    )

    user_data['current_hotel_text'] = (
        f"🏨 Отель: {name}\n"
        f"📅 Заезд: {checkin}\n"
        f"📅 Выезд: {checkout}\n"
        f"⭐ Рейтинг: {rating}\n"
        f"💰 Цена: {price_text}"
    )

    keyboard = InlineKeyboardMarkup(row_width=2)
    btns = []
    if index > 0:
        btns.append(InlineKeyboardButton("⬅️ Назад", callback_data="page_prev"))
    if index < len(hotels) - 1:
        btns.append(InlineKeyboardButton("Вперед ➡️", callback_data="page_next"))

    if btns:
        keyboard.add(*btns)

    keyboard.add(InlineKeyboardButton("📝 Добавить в заметки", callback_data="save_card_note"))
    keyboard.add(InlineKeyboardButton("⬅️️ В главное меню", callback_data="back_to_menu"))

    photo_urls = property_info.get('photoUrls', [])
    if photo_urls:
        bot.send_photo(chat_id, photo=photo_urls[0], caption=text, parse_mode="Markdown", reply_markup=keyboard)
    else:
        bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ["page_prev", "page_next"])
def handle_pagination(call):
    """Перехватывает нажатия кнопок перелистывания"""
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    user_data = user_search_data.get(chat_id, {})

    if 'current_hotel_index' not in user_data:
        bot.send_message(chat_id, "Поиск устарел. Пожалуйста, начните заново.")
        return

    if call.data == "page_prev":
        user_data['current_hotel_index'] -= 1
    elif call.data == "page_next":
        user_data['current_hotel_index'] += 1

    bot.delete_message(chat_id, call.message.message_id)
    send_hotel_card(chat_id)

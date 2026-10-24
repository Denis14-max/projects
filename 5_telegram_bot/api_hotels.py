import os

import requests
from dotenv import load_dotenv

load_dotenv()
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
HEADERS = {
    "X-RapidAPI-Key": RAPID_API_KEY,
    "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
}


def get_city_destinations(city_name: str):
    """Ищет локации по названию города и возвращает список результатов"""
    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"

    querystring = {
        "query": city_name,
        "locale": "ru"
    }

    try:
        response = requests.get(url, headers=HEADERS, params=querystring, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])[:5]
        else:
            return None
    except Exception as e:
        print(f"Ошибка при запросе к API: {e}")
        return None


def get_hotels_data(dest_id: str, search_type: str, checkin: str, checkout: str):
    """
    Запрашивает список доступных отелей с ценами и описанием на выбранные даты.
    """
    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"

    querystring = {
        "dest_id": dest_id,
        "search_type": search_type,
        "arrival_date": checkin,
        "departure_date": checkout,
        "adults": "1",
        "room_qty": "1",
        "page_number": "1",
        "languagecode": "ru",
        "currency_code": "USD"
    }

    try:
        print(f"Отправляем запрос: dest_id={dest_id}, type={search_type}, даты={checkin} - {checkout}")
        response = requests.get(url, headers=HEADERS, params=querystring, timeout=10)
        print(f"Статус ответа сервера: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            hotels = data.get('data', {}).get('hotels', [])
            print(f"Количество найденных отелей: {len(hotels)}")
            print(data)

            if not hotels:
                print("Ответ от API:", data)

            return hotels
        else:
            print(f"Ошибка сервера API. Ответ: {response.text}")
            return None
    except Exception as e:
        print(f"Ошибка при запросе отелей к API: {e}")
        return None

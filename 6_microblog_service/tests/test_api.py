from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_main():
    """Тест 1: Проверка доступности главной страницы"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_unauthorized_access():
    """Тест 2: Попытка зайти в профиль без API-ключа"""
    response = client.get("/api/users/me")
    assert response.status_code == 422


def test_invalid_api_key():
    """Тест 3: Использование неправильного API-ключа"""
    headers = {"api-key": "fake_test"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 401
    assert response.json() == {
        "result": False,
        "error_type": "ClientError",
        "error_message": "Неверный API ключ или пользователь не найден"
    }
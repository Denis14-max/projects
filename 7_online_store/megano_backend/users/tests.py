from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import User


class UsersEndpointsTests(APITestCase):
    def setUp(self):
        """Создание тестового пользователя"""
        self.user = User.objects.create_user(
            username="existinguser",
            password="password123",
            first_name="Existing",
            last_name="User",
            email="existing@store.local"
        )
        self.new_user_data = {
            "name": "New User",
            "username": "newuser",
            "password": "newpassword123"
        }

    def test_sign_up_success(self):
        """Проверка успешной регистрации нового пользователя"""
        url = reverse('users:sign-up')
        response = self.client.post(url, self.new_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_sign_up_duplicate(self):
        """Проверка ошибки при регистрации с существующим логином"""
        url = reverse('users:sign-up')
        duplicate_data = self.new_user_data.copy()
        duplicate_data['username'] = "existinguser"  # Логин из setUp
        response = self.client.post(url, duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sign_in_success(self):
        """Проверка успешной авторизации"""
        url = reverse('users:sign-in')
        response = self.client.post(url, {
            "username": "existinguser",
            "password": "password123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_profile_authenticated(self):
        """Проверка доступа к профилю для авторизованного пользователя"""
        self.client.force_login(self.user)
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], "existing@store.local")

    def test_get_profile_unauthenticated(self):
        """Проверка запрета доступа к профилю для анонима"""
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

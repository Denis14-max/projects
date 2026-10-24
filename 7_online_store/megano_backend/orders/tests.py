from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from catalog.models import Category, Product
from users.models import User
from .models import Order


class OrdersEndpointsTests(APITestCase):
    def setUp(self):
        """Создание тестовых данных: пользователь, категория и товар"""
        self.user = User.objects.create_user(username="testuser", password="testpassword123")
        self.category = Category.objects.create(title="Тестовая категория")
        self.product = Product.objects.create(
            title="Тестовый товар",
            price=500.00,
            count=10,
            category=self.category
        )

    def test_basket_add_anonymous(self):
        """Проверка добавления товара в корзину для анонимного пользователя"""
        url = reverse('orders:basket')
        response = self.client.post(url, {"id": self.product.id, "count": 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['count'], 2)

    def test_create_order_authenticated(self):
        """Проверка оформления заказа авторизованным пользователем"""
        self.client.force_login(self.user)

        basket_url = reverse('orders:basket')
        self.client.post(basket_url, {"id": self.product.id, "count": 1}, format='json')

        orders_url = reverse('orders:orders')
        response = self.client.post(orders_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('orderId', response.data)
        self.assertTrue(Order.objects.filter(id=response.data['orderId']).exists())

    def test_payment_success(self):
        """Проверка успешной оплаты"""
        self.client.force_login(self.user)
        order = Order.objects.create(user=self.user, totalCost=500.00)
        url = reverse('orders:payment', kwargs={'id': order.id})

        response = self.client.post(url, {"number": "12345678"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')

    def test_payment_fail(self):
        """Проверка ошибки при оплате"""
        self.client.force_login(self.user)
        order = Order.objects.create(user=self.user, totalCost=500.00)
        url = reverse('orders:payment', kwargs={'id': order.id})

        response = self.client.post(url, {"number": "12345677"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        order.refresh_from_db()
        self.assertEqual(order.status, 'failed')

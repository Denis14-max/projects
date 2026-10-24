from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Category, Product

class CatalogEndpointsTests(APITestCase):
    def setUp(self):
        """Создание тестовых данных"""
        self.category = Category.objects.create(title="Тестовая категория")
        self.product = Product.objects.create(
            title="Тестовый товар",
            price=1000.00,
            count=10,
            category=self.category,
            description="Описание",
            freeDelivery=True
        )

    def test_get_categories(self):
        """Проверка получения списка категорий"""
        url = reverse('catalog:categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_get_catalog(self):
        """Проверка работы каталога и пагинации"""
        url = reverse('catalog:catalog')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
        self.assertIn('currentPage', response.data)

    def test_get_product_detail(self):
        """Проверка получения конкретного товара по ID"""
        url = reverse('catalog:product-detail', kwargs={'id': self.product.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Тестовый товар")

    def test_get_non_existent_product(self):
        """Проверка ошибки 404 при запросе несуществующего товара"""
        url = reverse('catalog:product-detail', kwargs={'id': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
from django.db import models
from django.conf import settings
from catalog.models import Product


class Order(models.Model):
    """Модель оформления заказа"""

    DELIVERY_CHOICES = (
        ('ordinary', 'Обычная доставка'),
        ('express', 'Экспресс доставка'),
    )

    PAYMENT_CHOICES = (
        ('online', 'Онлайн картой'),
        ('someone', 'Онлайн со случайного чужого счета'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                             verbose_name="Покупатель")

    createdAt = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    paymentType = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='online', verbose_name="Тип оплаты")
    deliveryType = models.CharField(max_length=50, choices=DELIVERY_CHOICES, default='ordinary',
                                    verbose_name="Тип доставки")
    status = models.CharField(max_length=50, default='accepted', verbose_name="Статус оплаты")
    paymentError = models.CharField(max_length=255, blank=True, null=True, verbose_name="Ошибка оплаты")

    fullName = models.CharField(max_length=150, blank=True, verbose_name="ФИО")
    email = models.EmailField(blank=True, verbose_name="Email")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    city = models.CharField(max_length=100, blank=True, verbose_name="Город")
    address = models.CharField(max_length=250, blank=True, verbose_name="Адрес")

    totalCost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Итоговая сумма")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ №{self.id}"


class OrderItem(models.Model):
    """Связь конкретного товара с конкретным заказом"""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена при покупке")
    count = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = "Товар в заказе"
        verbose_name_plural = "Товары в заказах"

    def __str__(self):
        return f"{self.product.title} (x{self.count})"


class DeliverySettings(models.Model):
    """Настройки тарифов доставки, управляемые из админки"""
    express_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=500.00,
        verbose_name="Стоимость экспресс-доставки (руб.)"
    )
    free_delivery_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=2000.00,
        verbose_name="Порог бесплатной доставки (руб.)"
    )
    ordinary_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=200.00,
        verbose_name="Стоимость обычной доставки ниже порога (руб.)"
    )

    class Meta:
        verbose_name = "Настройки доставки"
        verbose_name_plural = "Настройки доставки"

    def __str__(self):
        return "Тарифы доставки"


class Cart(models.Model):
    """Корзина в БД для авторизованного пользователя"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"


class CartItem(models.Model):
    """Элемент корзины в БД"""
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        unique_together = ('cart', 'product')

from django.conf import settings

from catalog.models import Product
from orders import models


class Cart:
    """Гибридная корзина: БД для авторизованных, сессия для гостей"""

    def __init__(self, request):
        self.request = request
        self.user = request.user
        self.session = request.session
        self.cart = self.session.setdefault(settings.CART_SESSION_ID, {})

    @staticmethod
    def _to_count(count) -> int:
        try:
            return int(count)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _products_qs():
        return Product.objects.filter(is_deleted=False).select_related(
            'category'
        ).prefetch_related('images', 'tags', 'reviews')

    def add(self, product, count=1):
        """Добавление товара в корзину"""
        count = self._to_count(count)
        if count <= 0:
            return

        if self.user.is_authenticated:
            db_cart, _ = models.Cart.objects.get_or_create(user=self.user)
            item, _ = models.CartItem.objects.get_or_create(
                cart=db_cart, product=product, defaults={'count': 0}
            )
            item.count += count
            item.save(update_fields=['count'])
        else:
            product_id = str(product.id)
            entry = self.cart.setdefault(product_id, {'count': 0})
            entry['count'] += count
            self.save()

    def remove(self, product, count=1):
        """Уменьшение количества товара"""
        count = self._to_count(count)
        if count <= 0:
            return

        if self.user.is_authenticated:
            item = models.CartItem.objects.filter(
                cart__user=self.user, product=product
            ).first()
            if item:
                item.count -= count
                if item.count <= 0:
                    item.delete()
                else:
                    item.save(update_fields=['count'])
        else:
            product_id = str(product.id)
            if product_id in self.cart:
                self.cart[product_id]['count'] -= count
                if self.cart[product_id]['count'] <= 0:
                    del self.cart[product_id]
                self.save()

    def save(self):
        """Помечаем сессию изменённой"""
        self.session.modified = True

    def clear(self):
        """Очистка корзины"""
        if self.user.is_authenticated:
            models.CartItem.objects.filter(cart__user=self.user).delete()
        else:
            self.cart.clear()
            self.save()

    def __iter__(self):
        """Перебор товаров корзины"""
        if self.user.is_authenticated:
            items = models.CartItem.objects.filter(
                cart__user=self.user, product__is_deleted=False
            ).select_related(
                'product__category'
            ).prefetch_related(
                'product__images', 'product__tags', 'product__reviews'
            )
            for item in items:
                yield {
                    'product': item.product,
                    'price': item.product.price,
                    'count': item.count,
                }
        else:
            ids = [int(pk) for pk in self.cart.keys()]
            for product in self._products_qs().filter(id__in=ids):
                yield {
                    'product': product,
                    'price': product.price,
                    'count': self.cart[str(product.id)]['count'],
                }

    def merge_from_session(self):
        """Перенос товаров из сессии в БД после входа, затем очистка сессии"""
        if not self.user.is_authenticated or not self.cart:
            return

        db_cart, _ = models.Cart.objects.get_or_create(user=self.user)
        products = Product.objects.in_bulk([int(pk) for pk in self.cart.keys()])

        for product_id, item_data in self.cart.items():
            product = products.get(int(product_id))
            if not product:
                continue
            item, _ = models.CartItem.objects.get_or_create(
                cart=db_cart, product=product, defaults={'count': 0}
            )
            item.count += int(item_data['count'])
            item.save(update_fields=['count'])

        self.cart.clear()
        self.save()

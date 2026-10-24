from rest_framework import serializers

from catalog.serializers import ProductShortSerializer
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для детального просмотра и обновления заказа"""
    createdAt = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)
    products = serializers.SerializerMethodField()
    fullName = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'createdAt', 'fullName', 'email', 'phone',
            'deliveryType', 'paymentType', 'totalCost', 'status',
            'city', 'address', 'paymentError', 'products',
        )

    def get_products(self, obj: Order):
        """Товары заказа в формате фронтенда"""
        products_data = []
        for item in obj.items.all():
            prod_data = ProductShortSerializer(item.product).data
            prod_data['count'] = item.count
            prod_data['price'] = item.price
            products_data.append(prod_data)
        return products_data

    def get_fullName(self, obj: Order):
        if obj.fullName:
            return obj.fullName
        if obj.user:
            full = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full if full else obj.user.username
        return ""

    def get_email(self, obj: Order):
        if obj.email:
            return obj.email
        return obj.user.email if obj.user else ""

    def get_phone(self, obj: Order):
        if obj.phone:
            return obj.phone
        return obj.user.phone if obj.user and obj.user.phone else ""

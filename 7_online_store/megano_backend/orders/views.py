import random
from decimal import Decimal

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product
from catalog.serializers import ProductShortSerializer
from .cart import Cart
from .models import Order, OrderItem, DeliverySettings
from .serializers import OrderSerializer

ORDER_PREFETCH = (
    'items__product__category',
    'items__product__images',
    'items__product__tags',
    'items__product__reviews',
)


class PermissiveJSONParser(JSONParser):
    """Парсер, который "проглатывает" любые кривые запросы от фронтенда"""
    media_type = '*/*'

    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return super().parse(stream, media_type, parser_context)
        except Exception:
            return {}


def get_order_or_404(request: Request, order_id: int) -> Order:
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related(*ORDER_PREFETCH),
        id=order_id,
    )
    if order.user_id and order.user_id != request.user.id:
        raise Http404
    return order


class BasketView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser, PermissiveJSONParser]

    def get(self, request: Request) -> Response:
        cart = Cart(request)
        response_data = []
        for item in cart:
            product_data = ProductShortSerializer(item['product']).data
            product_data['count'] = item['count']
            response_data.append(product_data)
        return Response(response_data)

    def post(self, request: Request) -> Response:
        cart = Cart(request)
        product_id = request.data.get('id')
        if not product_id:
            return Response({"error": "ID товара не передан"}, status=400)

        product = get_object_or_404(Product, id=product_id, is_deleted=False)
        cart.add(product=product, count=request.data.get('count', 1))
        return self.get(request)

    def delete(self, request: Request) -> Response:
        cart = Cart(request)
        product_id = request.data.get('id') or request.query_params.get('id')
        count = request.data.get('count') or request.query_params.get('count', 1)

        if not product_id:
            return Response({"error": "ID товара не передан"}, status=400)

        product = get_object_or_404(Product, id=product_id)
        cart.remove(product=product, count=count)
        return self.get(request)


class OrderView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser, PermissiveJSONParser]

    def get(self, request: Request) -> Response:
        if not request.user.is_authenticated:
            return Response([])
        orders = Order.objects.filter(user=request.user).select_related(
            'user'
        ).prefetch_related(*ORDER_PREFETCH).order_by('-createdAt')
        return Response(OrderSerializer(orders, many=True).data)

    def post(self, request: Request) -> Response:
        cart = Cart(request)
        items = list(cart)
        if not items:
            return Response({"error": "Корзина пуста"}, status=400)

        user = request.user if request.user.is_authenticated else None

        with transaction.atomic():
            order = Order.objects.create(
                user=user, fullName="", email="", phone="", city="", address=""
            )
            OrderItem.objects.bulk_create([
                OrderItem(order=order, product=i['product'], price=i['price'], count=i['count'])
                for i in items
            ])
            order.totalCost = sum(i['price'] * i['count'] for i in items)
            order.save(update_fields=['totalCost'])

        cart.clear()
        return Response({"orderId": order.id})


class OrderDetailView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser, PermissiveJSONParser]

    def get(self, request: Request, id: int) -> Response:
        order = get_order_or_404(request, id)
        return Response(OrderSerializer(order).data)

    def post(self, request: Request, id: int) -> Response:
        order = get_order_or_404(request, id)
        data = request.data

        order.fullName = data.get('fullName', order.fullName)
        order.phone = data.get('phone', order.phone)
        order.email = data.get('email', order.email)
        order.deliveryType = data.get('deliveryType', order.deliveryType)
        order.city = data.get('city', order.city)
        order.address = data.get('address', order.address)
        order.paymentType = data.get('paymentType', order.paymentType)

        products_cost = sum(item.price * item.count for item in order.items.all())

        delivery = DeliverySettings.objects.first()
        express_price = delivery.express_price if delivery else Decimal('500.00')
        threshold = delivery.free_delivery_threshold if delivery else Decimal('2000.00')
        ordinary_price = delivery.ordinary_price if delivery else Decimal('200.00')

        delivery_cost = Decimal('0.00')
        if order.deliveryType == 'express':
            delivery_cost = express_price
        elif products_cost < threshold:
            delivery_cost = ordinary_price

        order.totalCost = products_cost + delivery_cost
        order.status = 'awaiting_payment'
        order.save()
        return Response({"orderId": order.id})


class PaymentView(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser, PermissiveJSONParser]

    def post(self, request: Request, id: int) -> Response:
        order = get_order_or_404(request, id)

        raw_number = str(request.data.get('number', ''))
        clean_number = ''.join(filter(str.isdigit, raw_number))

        if not clean_number or len(clean_number) > 8:
            order.status = 'failed'
            order.paymentError = 'Номер карты должен содержать не более 8 цифр'
            order.save()
            return Response({"error": order.paymentError}, status=400)

        if int(clean_number) % 2 == 0 and not clean_number.endswith('0'):
            order.status = 'paid'
            order.paymentError = None
            order.save()
            return Response({"status": "success", "message": "Оплата прошла успешно"}, status=200)

        errors = [
            'Недостаточно средств на счете',
            'Счет заблокирован банком',
            'Превышен лимит операций',
            'Платежная система временно недоступна',
        ]
        order.status = 'failed'
        order.paymentError = random.choice(errors)
        order.save()
        return Response({"error": order.paymentError}, status=400)

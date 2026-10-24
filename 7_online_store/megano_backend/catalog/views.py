from django.db.models import Avg, Count, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Tag
from .serializers import (
    CategorySerializer, ProductShortSerializer, ProductFullSerializer,
    ReviewSerializer, TagSerializer,
)
import json
from rest_framework.parsers import BaseParser, JSONParser, MultiPartParser, FormParser


class PermissiveJSONParser(JSONParser):
    media_type = '*/*'

    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return super().parse(stream, media_type, parser_context)
        except Exception:
            return {}


class FallbackParser(BaseParser):
    media_type = '*/*'

    def parse(self, stream, media_type=None, parser_context=None):
        return stream.read()


def get_parsed_data(request):
    try:
        if request.body:
            parsed = json.loads(request.body)
            if isinstance(parsed, dict):
                return parsed
    except Exception:
        pass
    data = request.data
    if hasattr(data, 'keys') and 'text' not in data:
        for key in data.keys():
            try:
                parsed = json.loads(key)
                if isinstance(parsed, dict) and 'text' in parsed:
                    return parsed
            except:
                pass
    return data if isinstance(data, dict) else {}


def active_products():
    """Базовый запрос активных товаров"""
    return Product.objects.filter(is_deleted=False).select_related(
        'category'
    ).prefetch_related('images', 'tags', 'reviews')


def to_int(value, default: int, minimum: int = 1, maximum: int = 100) -> int:
    try:
        return max(minimum, min(int(value), maximum))
    except (TypeError, ValueError):
        return default


def paginate(queryset, request: Request, limit: int):
    current_page = to_int(request.query_params.get('currentPage'), 1, maximum=10 ** 6)
    total_items = queryset.count()
    last_page = max((total_items + limit - 1) // limit, 1)
    offset = (current_page - 1) * limit
    return {
        "items": ProductShortSerializer(queryset[offset:offset + limit], many=True).data,
        "currentPage": current_page,
        "lastPage": last_page,
    }


class CategoryListView(APIView):
    """Список категорий и их подкатегорий"""

    def get(self, request: Request) -> Response:
        categories = Category.objects.filter(parent=None, is_deleted=False).prefetch_related(
            Prefetch('subcategories', queryset=Category.objects.filter(is_deleted=False))
        )
        return Response(CategorySerializer(categories, many=True).data)


class PopularProductsView(APIView):
    """8 популярных товаров для главной страницы"""

    def get(self, request: Request) -> Response:
        products = active_products().order_by("sort_index", "-purchases")[:8]
        return Response(ProductShortSerializer(products, many=True).data)


class LimitedProductsView(APIView):
    """До 16 товаров с галочкой 'ограниченный тираж'"""

    def get(self, request: Request) -> Response:
        products = active_products().filter(is_limited=True)[:16]
        return Response(ProductShortSerializer(products, many=True).data)


class BannersView(APIView):
    """Товары для баннеров на главной странице"""

    def get(self, request: Request) -> Response:
        products = active_products().order_by('-date')[:3]
        return Response(ProductShortSerializer(products, many=True).data)


class ProductDetailView(APIView):
    """Полная информация о товаре"""

    def get(self, request: Request, id: int) -> Response:
        product = get_object_or_404(active_products().prefetch_related('specifications'), id=id)
        return Response(ProductFullSerializer(product).data)


class ProductReviewView(APIView):
    """Создание отзыва к товару"""
    parser_classes = [JSONParser, MultiPartParser, FormParser, PermissiveJSONParser]

    def post(self, request: Request, id: int) -> Response:
        product = get_object_or_404(Product, id=id, is_deleted=False)

        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product)
            return Response(ReviewSerializer(product.reviews.all(), many=True).data, status=201)
        return Response(serializer.errors, status=400)


class TagListView(APIView):
    """Все теги для фильтров"""

    def get(self, request: Request) -> Response:
        return Response(TagSerializer(Tag.objects.all(), many=True).data)


class CatalogView(APIView):
    """Каталог: фильтрация, сортировка, пагинация"""

    def get(self, request: Request) -> Response:
        params = request.query_params
        queryset = active_products()

        name = params.get('filter[name]', '')
        min_price = params.get('filter[minPrice]')
        max_price = params.get('filter[maxPrice]')
        tags = params.getlist('tags[]')

        if name:
            queryset = queryset.filter(title__icontains=name)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        if params.get('filter[freeDelivery]') == 'true':
            queryset = queryset.filter(freeDelivery=True)
        if params.get('filter[available]') == 'true':
            queryset = queryset.filter(count__gt=0)
        if tags:
            queryset = queryset.filter(
                id__in=Product.objects.filter(tags__id__in=tags).values('id')
            )

        queryset = queryset.annotate(
            reviews_count=Count('reviews', distinct=True),
            rating=Avg('reviews__rate'),
        )

        sort_mapping = {
            'rating': 'rating',
            'price': 'price',
            'reviews': 'reviews_count',
            'date': 'date',
        }
        order_by_field = sort_mapping.get(params.get('sort', 'price'), 'price')
        if params.get('sortType', 'inc') == 'dec':
            order_by_field = f"-{order_by_field}"
        queryset = queryset.order_by(order_by_field, 'id')

        limit = to_int(params.get('limit'), 20)
        return Response(paginate(queryset, request, limit))


class SalesView(APIView):
    """Товары для страницы 'Распродажи'"""

    def get(self, request: Request) -> Response:
        queryset = active_products().order_by('-date', 'id')
        return Response(paginate(queryset, request, 10))

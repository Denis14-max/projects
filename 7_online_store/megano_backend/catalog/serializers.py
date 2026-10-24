from typing import Any, Dict, List

from rest_framework import serializers

from .models import Category, Product, Tag, Specification, Review


def image_data(obj, alt: str) -> Dict[str, str]:
    """Формат картинки, подходящий фронтенду"""
    if obj.image:
        return {"src": obj.image.url, "alt": alt}
    return {"src": "", "alt": alt}


def product_images(obj: Product) -> List[Dict[str, str]]:
    """Картинки товара"""
    images = obj.images.all()
    if images:
        return [{"src": img.image.url, "alt": obj.title} for img in images]
    return [{"src": "", "alt": "Нет фото"}]


def product_rating(obj: Product) -> float:
    """Средний рейтинг по предзагруженным отзывам"""
    reviews = obj.reviews.all()
    if reviews:
        return round(sum(r.rate for r in reviews) / len(reviews), 1)
    return 0.0


class SubcategorySerializer(serializers.ModelSerializer):
    """Подкатегории"""
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "title", "image")

    def get_image(self, obj: Category) -> Dict[str, str]:
        return image_data(obj, obj.title)


class CategorySerializer(serializers.ModelSerializer):
    """Главные категории со вложенными подкатегориями"""
    image = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "title", "image", "subcategories")

    def get_image(self, obj: Category) -> Dict[str, str]:
        return image_data(obj, obj.title)

    def get_subcategories(self, obj: Category) -> List[Dict[str, Any]]:
        return SubcategorySerializer(obj.subcategories.all(), many=True, context=self.context).data


class TagSerializer(serializers.ModelSerializer):
    """Теги"""

    class Meta:
        model = Tag
        fields = ("id", "name")


class SpecificationSerializer(serializers.ModelSerializer):
    """Характеристики"""

    class Meta:
        model = Specification
        fields = ("name", "value")


class ReviewSerializer(serializers.ModelSerializer):
    """Отзывы"""
    date = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Review
        fields = ("author", "email", "text", "rate", "date")


class ProductShortSerializer(serializers.ModelSerializer):
    """Краткое отображение товара"""
    images = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "category", "price", "count", "date", "title", "description",
            "freeDelivery", "images", "tags", "reviews", "rating",
        )

    def get_images(self, obj: Product) -> List[Dict[str, str]]:
        return product_images(obj)

    def get_reviews(self, obj: Product) -> int:
        """Количество отзывов"""
        return len(obj.reviews.all())

    def get_rating(self, obj: Product) -> float:
        return product_rating(obj)


class ProductFullSerializer(serializers.ModelSerializer):
    """Полная страница товара"""
    images = serializers.SerializerMethodField()
    tags = TagSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    specifications = SpecificationSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id", "category", "price", "count", "date", "title", "description",
            "fullDescription", "freeDelivery", "images", "tags", "reviews",
            "specifications", "rating",
        )

    def get_images(self, obj: Product) -> List[Dict[str, str]]:
        return product_images(obj)

    def get_rating(self, obj: Product) -> float:
        return product_rating(obj)

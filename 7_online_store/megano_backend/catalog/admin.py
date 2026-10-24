from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest
from .models import Category, Product, ProductImage, Tag, Review, Specification


@admin.action(description="Удалить выбранные элементы")
def mark_deleted(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet):
    """Удаление выбранных элементов"""
    queryset.update(is_deleted=True)


@admin.action(description="Восстановить выбранные элементы")
def mark_restored(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet):
    """Восстановление выбранных элементов"""
    queryset.update(is_deleted=False)


class SubCategoryInline(admin.TabularInline):
    model = Category
    fk_name = 'parent'
    extra = 1
    fields = ('title', 'image', 'is_deleted')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "parent", "is_deleted")
    list_filter = ("is_deleted",)
    search_fields = ("title",)

    actions = [mark_deleted, mark_restored]

    inlines = [SubCategoryInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("parent")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class SpecificationInline(admin.TabularInline):
    model = Specification
    extra = 0


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "price", "count", "is_limited", "is_deleted")
    list_filter = ("category", "freeDelivery", "is_limited", "is_deleted")
    search_fields = ("title", "description")
    filter_horizontal = ("tags",)

    actions = [mark_deleted, mark_restored]
    inlines = [ProductImageInline, SpecificationInline, ReviewInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related('category')

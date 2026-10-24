from django.urls import path
from .views import (CategoryListView, PopularProductsView, LimitedProductsView, BannersView, ProductDetailView,
                    ProductReviewView, TagListView, CatalogView, SalesView)

app_name = 'catalog'

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='categories'),
    path('products/popular/', PopularProductsView.as_view(), name='popular-products'),
    path('products/limited/', LimitedProductsView.as_view(), name='limited-products'),
    path('banners/', BannersView.as_view(), name='banners'),
    path('product/<int:id>/', ProductDetailView.as_view(), name='product-detail'),
    path('product/<int:id>', ProductDetailView.as_view()),
    path('product/<int:id>/reviews/', ProductReviewView.as_view(), name='product-reviews'),
    path('product/<int:id>/reviews', ProductReviewView.as_view()),
    path('catalog/', CatalogView.as_view(), name='catalog'),
    path('tags/', TagListView.as_view(), name='tags'),
    path('sales/', SalesView.as_view(), name='sales'),
]
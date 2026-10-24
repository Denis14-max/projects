from django.urls import path
from .views import BasketView, OrderView, OrderDetailView, PaymentView

app_name = 'orders'

urlpatterns = [
    path('basket/', BasketView.as_view(), name='basket'),
    path('basket', BasketView.as_view()),
    path('orders/', OrderView.as_view(), name='orders'),
    path('orders', OrderView.as_view()),
    path('order/<int:id>/', OrderDetailView.as_view(), name='order-detail'),
    path('order/<int:id>', OrderDetailView.as_view()),
    path('payment/<int:id>/', PaymentView.as_view(), name='payment'),
    path('payment/<int:id>', PaymentView.as_view()),
]
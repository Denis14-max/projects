from django.contrib import admin
from .models import Order, OrderItem, DeliverySettings


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'fullName', 'email', 'createdAt', 'status', 'totalCost')
    list_filter = ('status', 'deliveryType', 'paymentType', 'createdAt')
    search_fields = ('fullName', 'email', 'phone')
    inlines = [OrderItemInline]


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    list_display = ('express_price', 'free_delivery_threshold', 'ordinary_price')

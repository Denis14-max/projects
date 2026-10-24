from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.action(description="Удалить выбранных пользователей")
def mark_deleted(modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet[User]) -> None:
    """Массовое удаление пользователей"""
    queryset.update(is_deleted=True)

@admin.action(description="Восстановить выбранных пользователей")
def mark_restored(modeladmin, request: HttpRequest, queryset: QuerySet) -> None:
    """Массовое восстановление пользователей"""
    queryset.update(is_deleted=False)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Конфигурация панели администратора для кастомной модели пользователя
    """
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Персональная информация"), {"fields": ("first_name", "last_name", "email", "phone", "image")}),
        (
            _("Права доступа"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Дополнительно"), {"fields": ("is_deleted", "last_login", "date_joined")}),
    )

    list_display = ("username", "email", "phone", "first_name", "last_name", "is_staff", "is_deleted")
    search_fields = ("username", "first_name", "last_name", "email", "phone")
    actions = [mark_deleted, mark_restored]

from rest_framework import serializers
from .models import User


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра профиля пользователя"""
    fullName = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('fullName', 'email', 'phone', 'avatar')

    def get_fullName(self, obj: User) -> str:
        """Склеиваем first_name и last_name или возвращаем username"""
        full = f"{obj.first_name} {obj.last_name}".strip()
        return full if full else obj.username

    def get_avatar(self, obj: User) -> dict:
        """Возвращаем аватарку"""
        if obj.image:
            return {
                "src": obj.image.url,
                "alt": obj.username,
            }
        return {
            "src": "",
            "alt": "Нет фото",
        }

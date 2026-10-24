import json
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.cart import Cart
from .models import User
from .serializers import ProfileSerializer


class PermissiveJSONParser(JSONParser):
    """Парсер, который проглатывает любые кривые запросы от фронтенда"""
    media_type = '*/*'

    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return super().parse(stream, media_type, parser_context)
        except Exception:
            return {}


def extract_data(request: Request) -> dict:
    """Универсальное извлечение данных"""
    data = request.data

    if hasattr(data, 'dict'):
        data = data.dict()

    if isinstance(data, dict):
        if len(data) == 1:
            key = list(data.keys())[0]
            if isinstance(key, str) and key.startswith('{') and key.endswith('}'):
                try:
                    return json.loads(key)
                except Exception:
                    pass
        return data

    if isinstance(data, str):
        try:
            return json.loads(data)
        except Exception:
            pass

    return {}


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser, PermissiveJSONParser]

    def get(self, request: Request) -> Response:
        return Response(ProfileSerializer(request.user).data)

    def post(self, request: Request) -> Response:
        user = request.user
        data = extract_data(request)

        full_name = str(data.get('fullName', '')).strip()
        email = str(data.get('email', '')).strip()
        phone = str(data.get('phone', '')).strip()

        if not full_name or not email:
            return Response({"error": "ФИО и E-mail обязательны"}, status=400)
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return Response({"error": "Пользователь с таким email уже существует"}, status=400)
        if phone and User.objects.filter(phone=phone).exclude(id=user.id).exists():
            return Response({"error": "Пользователь с таким телефоном уже существует"}, status=400)

        names = full_name.split(' ', 1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else ''
        user.email = email
        user.phone = phone
        user.save()

        return Response(ProfileSerializer(user).data)


class ProfileAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request: Request) -> Response:
        avatar_file = request.FILES.get('avatar')
        if not avatar_file:
            return Response({"error": "Файл не был загружен"}, status=400)

        if avatar_file.size > 2 * 1024 * 1024:
            return Response({"error": "Размер файла превышает 2 Мб."}, status=400)

        user = request.user
        user.image = avatar_file
        user.save()

        return Response({
            "url": {"src": user.image.url, "alt": user.username},
            "src": user.image.url,
            "alt": user.username,
        }, status=200)


class ProfilePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser, PermissiveJSONParser]

    def post(self, request: Request) -> Response:
        data = extract_data(request)

        current_password = data.get('currentPassword') or data.get('passwordCurrent') or data.get('current_password')
        new_password = data.get('password') or data.get('newPassword') or data.get('new_password')

        if not current_password or not new_password:
            return Response({"error": "Заполните все поля паролей"}, status=400)

        user = request.user
        if not user.check_password(current_password):
            return Response({"error": "Неверный текущий пароль"}, status=400)

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response({"status": "success"}, status=200)


class SignInView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser, PermissiveJSONParser]

    def post(self, request: Request) -> Response:
        data = extract_data(request)

        raw_username = str(data.get('username', '')).strip()
        password = str(data.get('password', '')).strip()

        if not raw_username or not password:
            return Response({"error": "Логин и пароль обязательны"}, status=400)

        user_obj = User.objects.filter(username__iexact=raw_username).first()
        username = user_obj.username if user_obj else raw_username

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response({"error": "Неверный логин или пароль"}, status=400)

        login(request, user)
        Cart(request).merge_from_session()
        return Response({"status": "success"}, status=200)


class SignUpView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser, MultiPartParser, FormParser, PermissiveJSONParser]

    def post(self, request: Request) -> Response:
        data = extract_data(request)

        name = str(data.get('name', '')).strip()
        username = str(data.get('username', '')).strip()
        password = str(data.get('password', '')).strip()

        if not username or not password:
            return Response({"error": "Логин и пароль обязательны"}, status=400)

        if User.objects.filter(username__iexact=username).exists():
            return Response({"error": "Пользователь с таким логином уже существует"}, status=400)

        names = name.split(' ', 1)
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=names[0],
            last_name=names[1] if len(names) > 1 else '',
            email=f"{username}@store.local",
        )

        auth_user = authenticate(request, username=username, password=password)
        if auth_user:
            login(request, auth_user)
        else:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        Cart(request).merge_from_session()
        return Response({"status": "success"}, status=201)


class SignOutView(APIView):
    def post(self, request: Request) -> Response:
        logout(request)
        return Response({"status": "success"}, status=200)

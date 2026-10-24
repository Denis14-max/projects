from django.urls import path
from .views import ProfileView, ProfileAvatarView, ProfilePasswordView, SignInView, SignUpView, SignOutView

app_name = 'users'

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile', ProfileView.as_view()),
    path('profile/avatar/', ProfileAvatarView.as_view(), name='profile-avatar'),
    path('profile/avatar', ProfileAvatarView.as_view()),
    path('profile/password/', ProfilePasswordView.as_view(), name='profile-password'),
    path('profile/password', ProfilePasswordView.as_view()),
    path('sign-in/', SignInView.as_view(), name='sign-in'),
    path('sign-in', SignInView.as_view()),
    path('sign-up/', SignUpView.as_view(), name='sign-up'),
    path('sign-up', SignUpView.as_view()),
    path('sign-out/', SignOutView.as_view(), name='sign-out'),
    path('sign-out', SignOutView.as_view()),
]

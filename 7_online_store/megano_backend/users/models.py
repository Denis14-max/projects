from django.contrib.auth.models import AbstractUser
from django.db import models


def user_preview(instance, filename):
    return "users/user_{pk}/preview/{filename}".format(
        pk=instance.pk,
        filename=filename,
    )


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    image = models.ImageField(upload_to="user_preview", blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

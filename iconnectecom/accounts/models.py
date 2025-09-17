from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
# accounts/models.py


class CustomUser(AbstractUser):
    # Add custom fields if needed
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=50, blank=True)
    # Add other fields as required

    def __str__(self):
        return self.username
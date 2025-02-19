from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import validate_email


class UserManager(BaseUserManager):
    """Manager for custom UserProfile class"""
    def create_user(self, email: str, password: str = None, **extra_fields) -> 'User':
        """Creates a new user and returns it"""
        validate_email(email)

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str, **extra_fields) -> 'User':
        """Creates a superuser and returns it"""
        user = self.create_user(email=email, password=password, **extra_fields)

        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model"""
    email = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def __str__(self) -> str:
        """Return string representation of user"""
        return self.email

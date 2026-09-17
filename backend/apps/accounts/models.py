"""Modèle utilisateur personnalisé : authentification par email + rôles."""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """Gestionnaire du modèle ``User`` (authentification par email)."""

    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Le superutilisateur doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Le superutilisateur doit avoir is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """Utilisateur : email unique, rôle (client / gestionnaire / admin), avatar."""

    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        HOTEL_MANAGER = "hotel_manager", "Gestionnaire d'hôtel"
        ADMIN = "admin", "Administrateur"

    email = models.EmailField("Adresse email", unique=True)
    first_name = models.CharField("Prénom", max_length=150, blank=True)
    last_name = models.CharField("Nom", max_length=150, blank=True)
    role = models.CharField(
        "Rôle", max_length=20, choices=Role.choices, default=Role.CLIENT
    )
    phone = models.CharField("Téléphone", max_length=20, blank=True)
    avatar = models.ImageField(
        "Photo de profil", upload_to="avatars/", blank=True, null=True
    )
    is_staff = models.BooleanField("Staff", default=False)
    is_active = models.BooleanField("Actif", default=True)
    date_joined = models.DateTimeField("Inscrit le", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ["-date_joined"]
        indexes = [models.Index(fields=["role"])]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_client(self):
        return self.role == self.Role.CLIENT

    @property
    def is_hotel_manager(self):
        return self.role == self.Role.HOTEL_MANAGER

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMIN
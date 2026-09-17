"""Serializers DRF du domaine Comptes (inscription, profil)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Profil utilisateur.

    Le ``password`` est en écriture seule. Le ``role`` est en lecture seule :
    l'attribution des rôles gestionnaire/admin passe par l'admin Django ou un
    endpoint dédié (étapes suivantes).
    """

    password = serializers.CharField(
        write_only=True, required=False, min_length=8, trim_whitespace=False
    )
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "avatar",
            "role",
            "is_active",
            "date_joined",
        )
        read_only_fields = ("id", "role", "is_active", "date_joined")

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if not password:
            raise serializers.ValidationError(
                {"password": "Le mot de passe est obligatoire."}
            )
        return User.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.set_password(password)
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """Changement de mot de passe de l'utilisateur connecté.

    Vérifie le mot de passe actuel, applique les validateurs Django
    (``AUTH_PASSWORD_VALIDATORS``) et exige la confirmation.
    """

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "Le mot de passe actuel est incorrect."}
            )
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Les deux mots de passe ne correspondent pas."}
            )
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError(
                {"new_password": "Le nouveau mot de passe doit être différent."}
            )
        try:
            validate_password(attrs["new_password"], user)
        except Exception as exc:
            raise serializers.ValidationError({"new_password": list(exc)})
        return attrs
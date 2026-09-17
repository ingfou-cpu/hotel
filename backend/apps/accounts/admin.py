"""Administration Django du modèle User (authentification par email)."""

from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import Group

from apps.accounts.models import User


class UserCreationForm(forms.ModelForm):
    """Formulaire de création d'utilisateur pour l'admin (email + mot de passe)."""

    password1 = forms.CharField(
        label="Mot de passe", widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe", widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "role", "phone", "is_active", "is_staff")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """Formulaire de modification d'un utilisateur dans l'admin."""

    groups = forms.ModelMultipleChoiceField(
        Group.objects.all(),
        required=False,
        widget=FilteredSelectMultiple("groupes", False),
    )

    class Meta:
        model = User
        fields = (
            "email", "first_name", "last_name", "phone", "avatar",
            "role", "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions",
        )


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ("email", "full_name", "role", "is_active", "is_staff", "date_joined")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("date_joined", "last_login")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations", {"fields": ("first_name", "last_name", "phone", "avatar")}),
        ("Rôle", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email", "password1", "password2",
                    "first_name", "last_name", "role", "is_active", "is_staff",
                ),
            },
        ),
    )
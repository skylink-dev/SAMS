from django.contrib import admin, messages
from django import forms
from dal import autocomplete
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string

from .models import CustomUser
from master.models import State, District, Office
from asm.models import ASM
from zonal_manager.models import ZonalManager


# ---------------------- FORM ---------------------- #
class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = "__all__"
        widgets = {
            "states": autocomplete.ModelSelect2Multiple(
                url="state-autocomplete",
                attrs={"data-placeholder": "Select State(s)"}
            ),
            "districts": autocomplete.ModelSelect2Multiple(
                url="district-autocomplete",
                forward=["states"],
                attrs={"data-placeholder": "Select District(s)"}
            ),
            "offices": autocomplete.ModelSelect2Multiple(
                url="office-autocomplete",
                forward=["districts"],
                attrs={"data-placeholder": "Select Office(s)"}
            ),
        }


# ---------------------- ADMIN ---------------------- #
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    form = CustomUserForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "username",
        "full_name",
        "role",
        "get_asm_name",
        "get_zm_name",
        "is_active",
    )
    list_filter = ("role", "is_active")
    search_fields = ("username", "full_name", "email", "phone")

    fieldsets = (
        ("Profile", {"fields": ("username", "full_name", "email", "phone", "role")}),
        ("Status", {"fields": ("is_active", "is_verified", "is_staff", "is_superuser")}),
        ("Assigned Areas", {"fields": ("states", "districts", "offices")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "role"),
        }),
    )

    # 🧩 Partner List Display Helpers
    # 🧩 Partner/ASM/ZM Relationship Display
    def get_asm_name(self, obj):
        """Show ASM name for Partner or self if ASM."""
        if obj.role == "Partner":
            # Partner → Find its ASM
            asm = ASM.objects.filter(partners=obj).select_related("user").first()
            if asm and asm.user:
                return asm.user.full_name or asm.user.username
        elif obj.role == "ASM":
            # ASM → Self name
            return obj.full_name or obj.username
        return "-"
    get_asm_name.short_description = "ASM"

    def get_zm_name(self, obj):
        """Show ZM name for Partner or ASM."""
        if obj.role == "Partner":
            # Partner → get ASM → get its ZM
            asm = ASM.objects.filter(partners=obj).select_related("user").first()
            if asm:
                zm = ZonalManager.objects.filter(asms=asm.user).select_related("user").first()
                if zm and zm.user:
                    return zm.user.full_name or zm.user.username

        elif obj.role == "Area Sales Manager":
            # ASM → find which ZM this ASM is assigned under
            zm = ZonalManager.objects.filter(asms__id=obj.id).select_related("user").first()
            if zm and zm.user:
                return zm.user.full_name or zm.user.username

        return "-"

    # ✅ Password and Reset Management
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:user_id>/password/",
                self.admin_site.admin_view(self.change_user_password),
                name="account_customuser_password",
            ),
            path(
                "<int:user_id>/reset-password/",
                self.admin_site.admin_view(self.reset_user_password),
                name="account_customuser_reset_password",
            ),
        ]
        return custom_urls + urls

    def change_user_password(self, request, user_id):
        """Change password manually in admin."""
        user = self.get_object(request, user_id)
        if not user:
            self.message_user(request, "User not found.", level=messages.ERROR)
            return redirect("..")

        if request.method == "POST":
            form = self.change_password_form(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, f"Password for {user.username} changed successfully.")
                return redirect(f"../../{user_id}/change/")
        else:
            form = self.change_password_form(user)

        context = {
            **self.admin_site.each_context(request),
            "title": f"Change password for {user.username}",
            "form": form,
            "opts": self.model._meta,
            "original": user,
        }
        return render(request, "admin/auth/user/change_password.html", context)

    def reset_user_password(self, request, user_id):
        """Send password reset link by email."""
        user = self.get_object(request, user_id)
        if not user or not user.email:
            messages.error(request, "User not found or has no email address.")
            return redirect("..")

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = request.build_absolute_uri(reverse("password_reset_confirm", args=[uid, token]))

        subject = "Password Reset Request"
        message = render_to_string("admin/reset_password_email.txt", {"user": user, "reset_url": reset_url})
        send_mail(subject, message, None, [user.email])

        messages.success(request, f"Password reset link sent to {user.email}")
        return redirect(f"../../{user_id}/change/")

    def change_view(self, request, object_id, form_url="", extra_context=None):
        """Add custom password/reset buttons in change view."""
        extra_context = extra_context or {}
        extra_context["change_password_url"] = reverse("admin:account_customuser_password", args=[object_id])
        extra_context["reset_password_url"] = reverse("admin:account_customuser_reset_password", args=[object_id])
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

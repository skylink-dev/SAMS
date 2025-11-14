# asm/models.py
from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL  # e.g. account.CustomUser


class ASM(models.Model):
    """
    ASM model - links an Area Sales Manager user with multiple Partners.
    Mirrors ZonalManager ↔ ASM relationship.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="asm_profile",
        limit_choices_to={"role": "Area Sales Manager"},
        null=True,
        blank=True,
    )

    # Partners assigned under this ASM
    partners = models.ManyToManyField(
        User,
        blank=True,
        related_name="assigned_asms",
        limit_choices_to={"role": "Partner"},
        help_text="Select Partners under this ASM",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ASM: {self.user.get_full_name() if self.user else 'Unassigned'}"

from django.db import models
from django.utils import timezone
from account.models import CustomUser
from zonal_manager.models import ZonalManager


class SDCollection(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    # ✅ Partner (from account.CustomUser, limited to role='Partner')
    partner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='partner_sd_collections',
        null=True,
        blank=True,
        limit_choices_to={'role': 'Partner'},
    )

    # ✅ ASM (from account.CustomUser, limited to role='Area Sales Manager')
    asm = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'Area Sales Manager'},
        related_name='asm_sd_collections',
    )

    # ✅ Zone Manager (from zonal_manager app)
    zone_manager = models.ForeignKey(
        ZonalManager,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='zm_sd_collections',
    )

    date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    note = models.TextField(blank=True, null=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = "Security Deposit Collection"
        verbose_name_plural = "Security Deposit Collections"

    def __str__(self):
        partner_name = (
            self.partner.get_full_name()
            if self.partner
            else "Unknown Partner"
        )
        return f"{partner_name} - ₹{self.amount} on {self.date}"

from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL  # account.CustomUser


class ZonalManager(models.Model):
    """
    Zonal Manager model - links a Zone Manager user with multiple ASMs.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="zm_profile",
        limit_choices_to={"role": "Zone Manager"},
        null=True,
        blank=True,
    )

    # ASMs assigned under this ZM
    asms = models.ManyToManyField(
        User,
        blank=True,
        related_name="assigned_zms",
        limit_choices_to={"role": "Area Sales Manager"},
        help_text="Select ASMs under this Zonal Manager",
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ZM: {self.user.get_full_name() if self.user else 'Unassigned'}"


class ZMDailyTarget(models.Model):
    """
    Daily target and achievement tracking for each Zonal Manager.
    """
    zonal_manager = models.ForeignKey(
        ZonalManager,
        on_delete=models.CASCADE,
        related_name="daily_targets",
        null=True,
        blank=True,
    )

    asm = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="zm_targets",
        null=True,
        blank=True,
        default=None,
        limit_choices_to={"role": "Area Sales Manager"},
        help_text="Select the ASM under this Zonal Manager",
    )

    # ✅ Always set a safe default for migration
    date = models.DateField(default=timezone.now, null=False, blank=False)

    # 🎯 Target fields (default = 0)
    application_target = models.FloatField(default=0)
    pop_target = models.FloatField(default=0)
    esign_target = models.FloatField(default=0)
    new_taluk_target = models.FloatField(default=0)
    new_live_partners_target = models.FloatField(default=0)
    activations_target = models.FloatField(default=0)
    calls_target = models.FloatField(default=0)
    sd_collection_target = models.FloatField(default=0)


    
    # 🎯 ASM Set Target fields
    asm_application_target = models.FloatField(default=0)
    asm_pop_target = models.FloatField(default=0)
    asm_esign_target = models.FloatField(default=0)
    asm_new_taluk_target = models.FloatField(default=0)
    asm_new_live_partners_target = models.FloatField(default=0)
    asm_activations_target = models.FloatField(default=0)
    asm_calls_target = models.FloatField(default=0)
    asm_sd_collection_target = models.FloatField(default=0)

    # ✅ Achievement fields (default = 0)
    application_achieve = models.FloatField(default=0)
    pop_achieve = models.FloatField(default=0)
    esign_achieve = models.FloatField(default=0)
    new_taluk_achieve = models.FloatField(default=0)
    new_live_partners_achieve = models.FloatField(default=0)
    activations_achieve = models.FloatField(default=0)
    calls_achieve = models.FloatField(default=0)
    sd_collection_achieve = models.FloatField(default=0)

    def __str__(self):
        return f"Target for {self.zonal_manager} on {self.date}"

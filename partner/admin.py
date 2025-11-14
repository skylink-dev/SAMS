from django.contrib import admin
from .models import SDCollection
from .forms import SDCollectionForm
from asm.models import ASM
from zonal_manager.models import ZonalManager

@admin.register(SDCollection)
class SDCollectionAdmin(admin.ModelAdmin):
    form = SDCollectionForm
    list_display = ('partner_name', 'asm_name', 'zone_manager_name', 'amount', 'date', 'status')
    list_filter = ('status', 'date', 'zone_manager')
    search_fields = (
        'partner__username',
        'partner__full_name',
        'asm__username',
        'asm__full_name',
        'zone_manager__user__full_name',
    )
    ordering = ('-date',)

    # ✅ Display readable names
    def partner_name(self, obj):
        return obj.partner.full_name if obj.partner else "-"
    partner_name.short_description = "Partner"

    def asm_name(self, obj):
        return obj.asm.full_name if obj.asm else "-"
    asm_name.short_description = "ASM"

    def zone_manager_name(self, obj):
        return obj.zone_manager.user.full_name if obj.zone_manager and obj.zone_manager.user else "-"
    zone_manager_name.short_description = "Zone Manager"

    # ✅ Auto-fill ASM + ZM before saving
    def save_model(self, request, obj, form, change):
        if obj.partner:
            asm = ASM.objects.filter(partners=obj.partner).select_related("user").first()
            if asm:
                obj.asm = asm.user
                zm = ZonalManager.objects.filter(asms=asm.user).select_related("user").first()
                if zm:
                    obj.zone_manager = zm
        super().save_model(request, obj, form, change)

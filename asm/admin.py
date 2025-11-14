from django.contrib import admin
from .models import ASM
from .forms import ASMForm

@admin.register(ASM)
class ASMAdmin(admin.ModelAdmin):
    form = ASMForm
    list_display = ('asm_name', 'partner_count', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = ('created_at',)

    def asm_name(self, obj):
        return obj.user.get_full_name() if obj.user else "Unassigned"
    asm_name.short_description = "Area Sales Manager"

    def partner_count(self, obj):
        return obj.partners.count()
    partner_count.short_description = "Partners Assigned"

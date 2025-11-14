from django.contrib import admin
from django.utils.html import format_html
from .models import ZonalManager, ZMDailyTarget


@admin.register(ZonalManager)
class ZonalManagerAdmin(admin.ModelAdmin):
    list_display = ('zm_name', 'asm_count', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    filter_horizontal = ('asms',)
    list_filter = ('created_at',)

    def zm_name(self, obj):
        return obj.user.get_full_name() if obj.user else "Unassigned"
    zm_name.short_description = "Zonal Manager"

    def asm_count(self, obj):
        return obj.asms.count()
    asm_count.short_description = "ASMs Assigned"
@admin.register(ZMDailyTarget)
class ZMDailyTargetAdmin(admin.ModelAdmin):
    list_display = (
        'zonal_manager_name', 'asm_name', 'date',
        'total_target_display', 'total_achieve_display', 'achievement_percent_display',
    )
    list_filter = ('date', 'zonal_manager__user__username')
    search_fields = ('zonal_manager__user__username', 'asm__username')
    date_hierarchy = 'date'
    readonly_fields = ('achievement_summary_display',)

    fieldsets = (
        ("General Info", {"fields": ('zonal_manager', 'asm', 'date')}),
        ("🎯 Targets", {
            "fields": (
                'application_target', 'pop_target', 'esign_target',
                'new_taluk_target', 'new_live_partners_target',
                'activations_target', 'calls_target', 'sd_collection_target'
            )
        }),
        ("✅ Achievements", {
            "fields": (
                'application_achieve', 'pop_achieve', 'esign_achieve',
                'new_taluk_achieve', 'new_live_partners_achieve',
                'activations_achieve', 'calls_achieve', 'sd_collection_achieve'
            )
        }),
        ("📊 Summary", {"fields": ('achievement_summary_display',)}),
    )

    # ---------- Manager Names ----------
    def zonal_manager_name(self, obj):
        return obj.zonal_manager.user.get_full_name() if obj.zonal_manager and obj.zonal_manager.user else "No ZM"
    zonal_manager_name.short_description = "Zonal Manager"

    def asm_name(self, obj):
        return obj.asm.get_full_name() if obj.asm else "No ASM"
    asm_name.short_description = "ASM"

    # ---------- Numeric Helpers ----------
    def total_target_value(self, obj):
        return float(sum([
            obj.application_target, obj.pop_target, obj.esign_target,
            obj.new_taluk_target, obj.new_live_partners_target,
            obj.activations_target, obj.calls_target, obj.sd_collection_target
        ]))

    def total_achieve_value(self, obj):
        return float(sum([
            obj.application_achieve, obj.pop_achieve, obj.esign_achieve,
            obj.new_taluk_achieve, obj.new_live_partners_achieve,
            obj.activations_achieve, obj.calls_achieve, obj.sd_collection_achieve
        ]))

    # ---------- List Display Fields ----------
        # ---------- List Display Fields ----------
    def total_target_display(self, obj):
        value = self.total_target_value(obj)
        return format_html('<span>{}</span>', f"{value:.2f}")
    total_target_display.short_description = "Total Target"

    def total_achieve_display(self, obj):
        total = self.total_achieve_value(obj)
        color = "green" if total > 0 else "red"
        formatted_total = f"{total:.2f}"
        return format_html('<b style="color:{};">{}</b>', color, formatted_total)
    total_achieve_display.short_description = "Total Achieved"

    def achievement_percent_display(self, obj):
        total_t = self.total_target_value(obj)
        total_a = self.total_achieve_value(obj)
        percent = (total_a / total_t * 100) if total_t > 0 else 0
        color = "green" if percent >= 100 else "orange" if percent >= 50 else "red"
        formatted_percent = f"{percent:.1f}%"
        return format_html('<b style="color:{};">{}</b>', color, formatted_percent)
    achievement_percent_display.short_description = "Achievement %"


    # ---------- Summary Display ----------
    def achievement_summary_display(self, obj):
        fields = [
            ("Application", obj.application_target, obj.application_achieve),
            ("POP", obj.pop_target, obj.pop_achieve),
            ("eSign", obj.esign_target, obj.esign_achieve),
            ("New Taluk", obj.new_taluk_target, obj.new_taluk_achieve),
            ("New Live Partners", obj.new_live_partners_target, obj.new_live_partners_achieve),
            ("Activations", obj.activations_target, obj.activations_achieve),
            ("Calls", obj.calls_target, obj.calls_achieve),
            ("SD Collection", obj.sd_collection_target, obj.sd_collection_achieve),
        ]

        html = '<table style="border-collapse: collapse; width: 70%;">'
        html += '<tr><th style="border-bottom:1px solid #ccc; text-align:left;">Field</th>'
        html += '<th style="border-bottom:1px solid #ccc;">Target</th>'
        html += '<th style="border-bottom:1px solid #ccc;">Achieved</th>'
        html += '<th style="border-bottom:1px solid #ccc;">%</th></tr>'

        for name, target, achieved in fields:
            target_val = float(target or 0)
            achieved_val = float(achieved or 0)
            percent = (achieved_val / target_val * 100) if target_val > 0 else 0
            color = "green" if percent >= 100 else "orange" if percent >= 50 else "red"
            html += f"<tr><td>{name}</td><td>{target_val:.0f}</td><td>{achieved_val:.0f}</td><td style='color:{color};'><b>{percent:.1f}%</b></td></tr>"

        total_t = float(self.total_target_value(obj))
        total_a = float(self.total_achieve_value(obj))
        overall = (total_a / total_t * 100) if total_t > 0 else 0
        overall_color = "green" if overall >= 100 else "orange" if overall >= 50 else "red"

        html += f"<tr style='border-top:2px solid #ccc; font-weight:bold;'><td>Total</td><td>{total_t:.0f}</td><td>{total_a:.0f}</td><td style='color:{overall_color};'>{overall:.1f}%</td></tr>"
        html += '</table>'
        return format_html(html)


    achievement_summary_display.short_description = "📊 Detailed Achievement Summary"
from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from .models import PincodeData, State, District, Office, TaskCategory
import csv
from django import forms
# 1️⃣ CSV Upload Form
class PincodeDataImportForm(forms.Form):
    csv_file = forms.FileField(
        label="Select CSV file",
        help_text="CSV should have columns: officename, pincode, statename, district, officetype"
    )


@admin.register(PincodeData)
class PincodeDataAdmin(admin.ModelAdmin):
    list_display = ('officename', 'pincode', 'district', 'statename', 'officetype')
    search_fields = ('officename', 'pincode', 'district', 'statename')
    list_filter = ('statename', 'district', 'officetype')
    change_list_template = "admin/pincodedata_changelist.html"  # custom template

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-csv/", self.admin_site.admin_view(self.import_csv_view), name="pincodedata_import_csv"),
            path("map-to-master/", self.admin_site.admin_view(self.map_to_master_view), name="map_to_master"),
            path("map-city-state-office/", self.admin_site.admin_view(self.map_city_state_office_view), name="map_city_state_office"),
        ]
        return custom_urls + urls

    

       # 3️⃣ CSV Import View
    def import_csv_view(self, request):
        if request.method == "POST":
            form = PincodeDataImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)

                created = updated = 0
                for row in reader:
                    if not row.get('officename') or not row.get('pincode') or not row.get('statename'):
                        continue

                    obj, obj_created = PincodeData.objects.update_or_create(
                        officename=row['officename'].strip(),
                        pincode=row['pincode'].strip(),
                        statename=row['statename'].strip(),
                        district=row.get('district', '').strip(),
                        defaults={
                            'officetype': row.get('officetype', '').strip()
                        }
                    )
                    if obj_created:
                        created += 1
                    else:
                        updated += 1

                messages.success(request, f"CSV Import Completed — Created: {created}, Updated: {updated}")
                return redirect("..")
        else:
            form = PincodeDataImportForm()

        context = dict(
            self.admin_site.each_context(request),
            form=form
        )
        return render(request, "admin/pincodedata_import.html", context)

    # ✅ 1️⃣ Map-to-Master Button Logic (safe + descriptive)
    def map_to_master_view(self, request):
        created_states = created_districts = created_offices = updated_offices = 0
        summary_lines = []

        for item in PincodeData.objects.all():
            if not item.pincode or not item.officename or not item.statename:
                continue

            # 🏛 State
            state, s_created = State.objects.get_or_create(name=item.statename.strip())
            if s_created:
                created_states += 1
                summary_lines.append(f"🆕 State added: {state.name}")

            # 🏙 District
            district, d_created = District.objects.get_or_create(
                name=item.district.strip(),
                state=state
            )
            if d_created:
                created_districts += 1
                summary_lines.append(f"🏙️ District '{district.name}' under {state.name}")

            # 🏢 Office
            office, created = Office.objects.update_or_create(
                name=item.officename.strip(),
                district=district,
                defaults={
                    'officetype': item.officetype.strip() if item.officetype else "",
                    'pincode': item.pincode.strip(),
                }
            )
            if created:
                created_offices += 1
                summary_lines.append(f"📮 Office '{office.name}' created in {district.name} ({state.name})")
            else:
                updated_offices += 1
                summary_lines.append(f"🔄 Office '{office.name}' updated in {district.name} ({state.name})")

        # ✅ Success summary
        messages.success(
            request,
            f"✅ Mapping Completed — "
            f"States: {created_states}, Districts: {created_districts}, "
            f"Offices Created: {created_offices}, Offices Updated: {updated_offices}"
        )

        # ✅ Show top 10 mapping entries to avoid flooding
        talk_summary = "<br>".join(summary_lines[:10])
        if len(summary_lines) > 10:
            talk_summary += f"<br>...and {len(summary_lines) - 10} more entries processed."

        messages.info(request, f"<b>Details:</b><br>{talk_summary}")
        return redirect("..")

    # ✅ 2️⃣ City–State–Office Button Logic (safe + descriptive)
    def map_city_state_office_view(self, request):
        created_states = created_districts = created_offices = updated_offices = 0
        summary_lines = []

        for item in PincodeData.objects.all():
            if not item.statename or not item.district or not item.officename:
                continue

            # 🏛 State
            state, s_created = State.objects.get_or_create(name=item.statename.strip())
            if s_created:
                created_states += 1
                summary_lines.append(f"🆕 State added: {state.name}")

            # 🏙 District
            district, d_created = District.objects.get_or_create(
                name=item.district.strip(),
                state=state
            )
            if d_created:
                created_districts += 1
                summary_lines.append(f"🏙️ District '{district.name}' under {state.name}")

            # 🏢 Office
            office, created = Office.objects.update_or_create(
                name=item.officename.strip(),
                district=district,
                defaults={
                    "officetype": item.officetype.strip() if item.officetype else "",
                    "pincode": item.pincode.strip() if item.pincode else "",
                }
            )
            if created:
                created_offices += 1
                summary_lines.append(f"📮 Office '{office.name}' added in {district.name} ({state.name})")
            else:
                updated_offices += 1
                summary_lines.append(f"🔄 Office '{office.name}' updated in {district.name} ({state.name})")

        # ✅ Summary
        messages.success(
            request,
            f"📍 City–State–Office Mapping Done — "
            f"States: {created_states}, Districts: {created_districts}, "
            f"Offices Created: {created_offices}, Offices Updated: {updated_offices}"
        )

        # ✅ Display top 10 mappings
        talk_summary = "<br>".join(summary_lines[:10])
        if len(summary_lines) > 10:
            talk_summary += f"<br>...and {len(summary_lines) - 10} more entries processed."

        messages.info(request, f"<b>Details:</b><br>{talk_summary}")
        return redirect("..")


# ✅ Other admin registrations
@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'state')
    list_filter = ('state',)
    search_fields = ('name', 'state__name')


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'officetype', 'pincode')
    list_filter = ('district__state', 'district')
    search_fields = ('name', 'district__name', 'pincode')



@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
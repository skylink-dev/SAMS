# partner/views.py
from dal import autocomplete
from account.models import CustomUser
from zonal_manager.models import ZonalManager


# 🔹 Autocomplete for Partner (from account.CustomUser)
class PartnerAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = CustomUser.objects.filter(role="Partner", is_active=True)
        if self.q:
            qs = qs.filter(full_name__icontains=self.q)
        return qs


# 🔹 Autocomplete for ASM (Area Sales Manager)
class ASMAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = CustomUser.objects.filter(role="Area Sales Manager", is_active=True)
        if self.q:
            qs = qs.filter(full_name__icontains=self.q)
        return qs


# 🔹 Autocomplete for Zone Manager
class ZMAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = ZonalManager.objects.all()
        if self.q:
            qs = qs.filter(user__full_name__icontains=self.q)
        return qs

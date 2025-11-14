# master/views.py
from dal import autocomplete
from .models import District, Office

class DistrictAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = District.objects.all()
        state_ids = self.forwarded.get('states', None)
        if state_ids:
            qs = qs.filter(state_id__in=state_ids)
        return qs.order_by('name')


class OfficeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Office.objects.all()
        district_ids = self.forwarded.get('districts', None)
        if district_ids:
            qs = qs.filter(district_id__in=district_ids)
        return qs.order_by('name')

from django import forms
from dal import autocomplete
from .models import SDCollection

class SDCollectionForm(forms.ModelForm):
    class Meta:
        model = SDCollection
        fields = ['partner', 'amount', 'date', 'status']  # only show these in the form
        widgets = {
            "partner": autocomplete.ModelSelect2(
                url="partner-autocomplete",
                attrs={"data-placeholder": "Select Partner"},
            ),
        }

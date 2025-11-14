# partner/urls.py
from django.urls import path
from .views import PartnerAutocomplete, ASMAutocomplete, ZMAutocomplete

urlpatterns = [
    path("partner-autocomplete/", PartnerAutocomplete.as_view(), name="partner-autocomplete"),
    path("asm-autocomplete/", ASMAutocomplete.as_view(), name="asm-autocomplete"),
    path("zm-autocomplete/", ZMAutocomplete.as_view(), name="zm-autocomplete"),
]

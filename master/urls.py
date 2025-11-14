# master/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("district-autocomplete/", views.DistrictAutocomplete.as_view(), name="district-autocomplete"),
    path("office-autocomplete/", views.OfficeAutocomplete.as_view(), name="office-autocomplete"),
]

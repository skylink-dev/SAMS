from django.urls import path
from . import views
from master.views import DistrictAutocomplete, OfficeAutocomplete
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('zone-manager-dashboard/', views.zone_manager_dashboard, name='zone_manager_dashboard'),
        path('technical-manager-dashboard/', views.technical_manager_dashboard, name='technical_manager_dashboard'),
    path('area-sales-dashboard/', views.area_sales_dashboard, name='area_sales_dashboard'),
    path('customer-support-dashboard/', views.customer_support_dashboard, name='customer_support_dashboard'),
    path('field-sales-dashboard/', views.field_sales_dashboard, name='field_sales_dashboard'),
    path('partner-dashboard/', views.partner_dashboard, name='partner_dashboard'),

    path("state-autocomplete/", views.StateAutocomplete.as_view(), name="state-autocomplete"),
    path("district-autocomplete/", DistrictAutocomplete.as_view(), name="district-autocomplete"),
    path("office-autocomplete/", OfficeAutocomplete.as_view(), name="office-autocomplete"),
]

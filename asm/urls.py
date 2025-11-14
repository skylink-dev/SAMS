from django.urls import path
from . import views

urlpatterns = [
    path(
        'partner-autocomplete/',
        views.PartnerAutocomplete.as_view(),
        name='partner-autocomplete'
    ),
    path('daily-target/', views.asm_daily_target, name='asm_daily_target'),
    path('daily_target/<int:pk>/', views.asm_daily_target_detail, name='asm_daily_target_detail'),
    path("daily_target/<int:pk>/edit/", views.asm_daily_target_edit, name="asm_daily_target_edit"),


      path('sd-collections/', views.asm_sd_list, name='asm_sd_list'),
    path('sd-collections/add/', views.asm_sd_add, name='asm_sd_add'),
    path('sd-collections/<int:pk>/edit/', views.asm_sd_edit, name='asm_sd_edit'),
    path('sd-collections/<int:pk>/delete/', views.asm_sd_delete, name='asm_sd_delete'),  # optional
    path('get-partner-details/<int:partner_id>/', views.asm_get_partner_details, name='asm_get_partner_details'),

    # ASM Task URLs
path('asm/tasks/', views.asm_task_list, name='asm_task_list'),
path('asm/tasks/<int:task_id>/', views.asm_task_detail, name='asm_task_detail'),
path("asm/tasks/<int:task_id>/update-status/", views.asm_update_task_status, name="asm_update_task_status"),



]

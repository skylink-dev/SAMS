from django.urls import path
from . import views

urlpatterns = [
      path("", views.daily_target, name="daily_target"),
    path("daily_target/", views.daily_target, name="daily_target"),
    path('daily_target/<int:pk>/', views.daily_target_detail, name='daily_target_detail'),
    path("daily_target/<int:pk>/edit/", views.daily_target_edit, name="daily_target_edit"),
path("daily_target/add/", views.daily_target_add, name="daily_target_add"),
      path("assign_task/", views.assign_task_to_asm, name="zm_assign_task"),
      path("tasks/", views.zm_task_list, name="zm_task_list"),
    path("tasks/<int:task_id>/", views.zm_task_detail, name="zm_task_detail"),
    path("tasks/<int:task_id>/edit/", views.zm_task_edit, name="zm_task_edit"),
    path("tasks/<int:task_id>/delete/", views.zm_task_delete, name="zm_task_delete"),
    path("tasks/<int:task_id>/status/<str:new_status>/", views.zm_change_status, name="zm_change_status"),
path("sd-collections/", views.zm_sd_collections_view, name="sd_collection_list_zm"),
path("sd-collections/add/", views.sd_collection_add, name="sd_collection_add"),

    path("get-partner-details/<int:partner_id>/", views.get_partner_details, name="get_partner_details"),
    path('zm/sd-collections/<int:pk>/edit/', views.sd_collection_edit, name='sd_collection_edit'),
         path("sd-collections/<int:pk>/delete/", views.sd_collection_delete, name="sd_collection_delete"),

]

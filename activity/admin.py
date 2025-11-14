from django.contrib import admin
from .models import Task, TaskNote

class TaskNoteInline(admin.TabularInline):
    model = TaskNote
    extra = 1
    readonly_fields = ('user', 'created_at')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'assigned_by', 'assigned_to', 'status', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'category', 'assigned_by', 'assigned_to')
    search_fields = ('title', 'details')
    inlines = [TaskNoteInline]


@admin.register(TaskNote)
class TaskNoteAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'note', 'created_at')
    search_fields = ('task__title', 'user__username', 'note')

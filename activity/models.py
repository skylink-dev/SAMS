from django.db import models
from django.utils import timezone
from django.conf import settings
from master.models import TaskCategory  # Assuming TaskCategory is in master app
from account.models import CustomUser  # Adjust path if different


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # 🧩 Core Fields
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks"
    )
    title = models.CharField(max_length=255)
    details = models.TextField(default="No details provided")

    # 📅 Dates
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(default=timezone.now)

    # 👥 Assigned users
    assigned_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks_assigned"
    )
    assigned_to = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks_received"
    )

    # 🔄 Status and control
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_deleted = models.BooleanField(default=False)

    # 🕒 Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task"
        verbose_name_plural = "Tasks"


# 📝 Notes for a Task
class TaskNote(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="notes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="task_notes"
    )
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note by {self.user.username} on {self.task.title}"

    class Meta:
        ordering = ['-created_at']

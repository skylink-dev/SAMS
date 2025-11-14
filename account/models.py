# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from master.models import State, District, Office  # import from your master app

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Zone Manager', 'Zone Manager'),
        ('Technical Manager', 'Technical Manager'),
        ('Area Sales Manager', 'Area Sales Manager'),        
        ('Customer Support', 'Customer Support'),
        ('Field Sales', 'Field Sales'),
        ('Partner', 'Partner'),
    ]

    full_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='Field Sales')
    date_joined = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    # 🗺️ Role-based geographic mappings (multiple allowed)
    states = models.ManyToManyField(State, blank=True, related_name="users")
    districts = models.ManyToManyField(District, blank=True, related_name="users")
    offices = models.ManyToManyField(Office, blank=True, related_name="users")

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def get_full_name(self):
        return self.full_name or f"{self.first_name} {self.last_name}".strip() or self.username

    def __str__(self):
        return f"{self.username} ({self.role})"

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']

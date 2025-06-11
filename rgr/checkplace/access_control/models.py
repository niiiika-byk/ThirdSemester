from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('SECURITY', 'Служба безопасности'),
        ('STAFF', 'Персонал'),
        ('ADMIN', 'Администратор'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STAFF')
    phone = models.CharField(max_length=15, blank=True)

class AirportPass(models.Model):
    ZONE_CHOICES = [
        ('TERMINAL', 'Терминал'),
        ('AIRFIELD', 'Лётное поле'),
        ('SECURE', 'Зона повышенной безопасности'),
        ('ADMIN', 'Административная зона'),
    ]
    
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    access_zone = models.CharField(max_length=10, choices=ZONE_CHOICES)
    is_active = models.BooleanField(default=True)
    
    @property
    def is_expired(self):
        return timezone.now().date() > self.expiry_date
    
    def __str__(self):
        return f"Пропуск #{self.id} ({self.get_access_zone_display()})"
    
class PassRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'На рассмотрении'),
        ('APPROVED', 'Одобрено'),
        ('REJECTED', 'Отклонено'),
    ]
    
    ZONE_CHOICES = [
        ('TERMINAL', 'Терминал'),
        ('AIRFIELD', 'Лётное поле'),
        ('SECURE', 'Зона повышенной безопасности'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    access_zone = models.CharField(max_length=20, choices=ZONE_CHOICES)
    purpose = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_access_zone_display()} ({self.get_status_display()})"
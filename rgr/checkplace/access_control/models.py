from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from datetime import date, timedelta

def default_end_date():
    return date.today() + timedelta(days=365)

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
    ]

    ACCESS_LEVELS = [
        (1, 'Базовый (Терминал)'),
        (2, 'Средний (Лётное поле)'),
        (3, 'Высокий (Зона безопасности)'),
        (4, 'Полный (Все зоны)'),
    ]
    
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    access_zone = models.CharField(max_length=10, choices=ZONE_CHOICES)
    access_level = models.IntegerField(choices=ACCESS_LEVELS, default=1)
    is_active = models.BooleanField(default=True)
    
    @property
    def is_expired(self):
        return timezone.now().date() > self.expiry_date
    
    def __str__(self):
        return f"Пропуск #{self.id} ({self.get_access_zone_display()})"
        
    def has_access_to(self, zone):
        zone_levels = {
            'TERMINAL': 1,
            'AIRFIELD': 2,
            'SECURE': 3
        }
        required_level = zone_levels.get(zone, 4)
        return self.access_level >= required_level
    
class PassRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'На рассмотрении'),
        ('APPROVED', 'Одобрено'),
        ('REJECTED', 'Отклонено'),
    ]
    
    ACCESS_ZONE_CHOICES = [
        ('TERMINAL', 'Терминал'),
        ('AIRFIELD', 'Лётное поле'),
        ('SECURE', 'Зона повышенной безопасности'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    access_zone = models.CharField(max_length=50, choices=ACCESS_ZONE_CHOICES)
    purpose = models.TextField()
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(
        default=default_end_date,
        validators=[MinValueValidator(date.today)],
        help_text="Дата, до которой нужен пропуск"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заявка #{self.id} ({self.user.get_full_name()})"

class AccessZone(models.Model):
    ZONE_TYPES = [
        ('TERMINAL', 'Терминал'),
        ('AIRFIELD', 'Лётное поле'),
        ('SECURE', 'Зона безопасности'),
    ]
    
    name = models.CharField(max_length=100)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPES)
    required_access_level = models.IntegerField(
        choices=AirportPass.ACCESS_LEVELS,
        default=1
    )
    description = models.TextField()

    def __str__(self):
        return f"{self.name} (Уровень {self.required_access_level})"
    
class AccessAttempt(models.Model):
    ATTEMPT_TYPES = [
        ('GRANTED', 'Доступ разрешён'),
        ('DENIED', 'Доступ запрещён'),
        ('ALERT', 'Попытка доступа в запрещённую зону'),
    ]
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    pass_instance = models.ForeignKey(
        AirportPass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пропуск'
    )
    zone = models.ForeignKey(
        AccessZone,
        on_delete=models.CASCADE,
        verbose_name='Целевая зона'
    )
    attempt_type = models.CharField(
        max_length=10,
        choices=ATTEMPT_TYPES,
        verbose_name='Тип попытки'
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время попытки'
    )
    details = models.TextField(
        blank=True,
        verbose_name='Дополнительная информация'
    )

    def __str__(self):
        return f"Попытка {self.user} в {self.zone} ({self.get_attempt_type_display()})"
    
    @classmethod
    def generate_test_attempt(cls):
        """Генерирует и сохраняет тестовую попытку доступа"""
        user = cls.objects.filter(role='STAFF', is_active=True).order_by('?').first()
        zone = AccessZone.get_random_zone()
        
        attempt = cls(
            user=user,
            zone=zone,
            timestamp=timezone.now()
        )
        
        # Проверяем есть ли у пользователя активный пропуск
        pass_instance = AirportPass.get_active_pass_for_user(user)
        
        if pass_instance:
            attempt.pass_instance = pass_instance
            if pass_instance.check_access(zone):
                attempt.attempt_type = 'GRANTED'
                attempt.details = "Автотест: доступ разрешен"
            else:
                attempt.attempt_type = 'DENIED'
                attempt.details = f"Автотест: недостаточный уровень ({pass_instance.access_level}<{zone.required_access_level})"
        else:
            attempt.attempt_type = 'ALERT'
            attempt.details = "Автотест: нет активного пропуска"
        
        attempt.save()
        return attempt
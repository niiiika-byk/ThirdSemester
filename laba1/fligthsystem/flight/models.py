from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser 
import random

class CustomUser (AbstractUser ):
    email = models.EmailField(unique=True)
    pass

class Passenger(models.Model):
    STATUS_CHOICES = [
        (0, 'Не подозрительный'),
        (1, 'Подозрительный'),
    ]

    suspicious_status = models.IntegerField(choices=STATUS_CHOICES, default=0)

    def generate_random_status(self):
        self.suspicious_status = random.choice([0, 1])  # 0 - Не подозрительный, 1 - Подозрительный
        self.save()
        
class Registration(models.Model):
        # Валидатор для серии паспорта (например, 00 00)
    passport_series_validator = RegexValidator(
        regex=r'^\d{2}\s?\d{2}$',  # Формат: 00 00 или 0000
        message='Серия паспорта должна состоять из 4 цифр (например, 00 00).'
    )

    # Валидатор для номера паспорта (например, 123456)
    passport_number_validator = RegexValidator(
        regex=r'^\d{6,10}$',  # Формат: 6-10 цифр
        message='Номер паспорта должен состоять из 6-10 цифр.'
    )
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    passport_series = models.CharField(max_length=10)
    passport_number = models.CharField(max_length=10)
    flight = models.CharField(max_length=100)
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, null=True, blank=True) 

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.flight}"
    
class Flight(models.Model):
    flight_number = models.CharField(max_length=6, unique=True)  # Номер рейса (2 буквы + 4 цифры)
    destination = models.CharField(max_length=100)  # Направление

    def __str__(self):
        return f"{self.flight_number} - {self.destination}"


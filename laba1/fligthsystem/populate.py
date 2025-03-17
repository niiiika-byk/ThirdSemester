import os
import django
import random

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flightsystem.settings')
django.setup()

from flight.models import Flight

def populate():
    # Удаляем все существующие записи
    Flight.objects.all().delete()

    # Пример данных для рейсов
    flights_data = [
        {'flight_number': 'AB1234', 'destination': 'Москва'},
        {'flight_number': 'CD5678', 'destination': 'Санкт-Петербург'},
        {'flight_number': 'EF9012', 'destination': 'Екатеринбург'},
        {'flight_number': 'IJ7890', 'destination': 'Казань'},
        {'flight_number': 'KL2345', 'destination': 'Сочи'},
        {'flight_number': 'MN6789', 'destination': 'Владивосток'},
        {'flight_number': 'OP1234', 'destination': 'Калининград'},
    ]

    # Цикл для создания рейсов
    for flight_data in flights_data:
        Flight.objects.create(
            flight_number=flight_data['flight_number'],
            destination=flight_data['destination']
        )

    print("Таблица рейсов успешно заполнена.")

if __name__ == '__main__':
    populate()
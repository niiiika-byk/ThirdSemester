#3 билет
#вопрос 2
from django.db import models

class Incident(models.Model):
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('in_progress', 'В работе'),
        ('closed', 'Закрыт'),
    ]
    
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')
    status = models.CharField(
        'Статус', 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='open'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Инцидент'
        verbose_name_plural = 'Инциденты'
        ordering = ['-created_at']
        from rest_framework import viewsets

from rest_framework import serializers
from .models import Incident

class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'

from .models import Incident
from .serializers import IncidentSerializer

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all().order_by('-created_at')
    serializer_class = IncidentSerializer

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .models import Incident

@require_http_methods(["GET"])
def incident_list(request):
    incidents = Incident.objects.all().order_by('-created_at')
    return render(request, 'incident_list.html', {'incidents': incidents})

@require_http_methods(["GET", "POST"])
def incident_add(request):
    if request.method == 'POST':
        Incident.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            status=request.POST.get('status', 'open')
        )
        return render(request, 'incident_list.html', {
            'incidents': Incident.objects.all().order_by('-created_at')
        })
    
    return render(request, 'incident_form.html')

from django.urls import path
from . import views

urlpatterns = [
    path('', views.incident_list, name='incident_list'),
    path('add/', views.incident_add, name='incident_add'),
]

#вопрос 3
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Incident
from .serializers import IncidentSerializer

@api_view(['GET'])
def get_incidents_by_employee(request):
    """
    GET /api/incidents/?employee_id=<id>
    Возвращает список инцидентов, назначенных конкретному сотруднику
    """
    employee_id = request.query_params.get('employee_id')
    
    # Валидация параметра
    if not employee_id:
        return Response(
            {'error': 'Не указан параметр employee_id'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        employee_id = int(employee_id)
    except ValueError:
        return Response(
            {'error': 'employee_id должен быть целым числом'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    incidents = Incident.objects.filter(assigned_to_id=employee_id)
    serializer = IncidentSerializer(incidents, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
def delete_incident(request, pk):
    """
    DELETE /api/incidents/<pk>/
    Удаляет инцидент, если его статус 'closed'
    В противном случае возвращает 403 Forbidden
    """
    incident = get_object_or_404(Incident, pk=pk)
    
    if incident.status != 'closed':
        return Response(
            {'error': 'Можно удалять только инциденты со статусом "Закрыт"'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    incident.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

from django.urls import path
from . import views

urlpatterns = [
    path('incidents/', views.get_incidents_by_employee, name='incidents-by-employee'),
    path('incidents/<int:pk>/', views.delete_incident, name='delete-incident'),
]

#8 билет
#2 вопрос
from datetime import datetime
from typing import List, Optional

class IncidentService:
    def __init__(self, incident_repository):
        self.incident_repository = incident_repository

    def create_incident(self, data: dict) -> dict:
        """
        Создание нового инцидента с валидацией данных
        :param data: Словарь с данными инцидента
        :return: Созданный инцидент
        """
        # Валидация данных
        if not data.get('title') or len(data['title']) < 5:
            raise ValueError("Название инцидента должно содержать минимум 5 символов")
        
        if not data.get('description') or len(data['description']) < 10:
            raise ValueError("Описание инцидента должно содержать минимум 10 символов")
        
        threat_level = data.get('threat_level', 3)
        if not (1 <= threat_level <= 5):
            raise ValueError("Уровень угрозы должен быть в диапазоне 1-5")

        # Установка значений по умолчанию
        incident_data = {
            'title': data['title'],
            'description': data['description'],
            'status': 'open',
            'threat_level': threat_level,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'assigned_to': data.get('assigned_to')
        }

        # Сохранение через DAL
        return self.incident_repository.create(incident_data)

    def close_incident(self, incident_id: int, resolution_comment: str = None) -> dict:
        """
        Закрытие инцидента с проверкой бизнес-правил
        :param incident_id: ID инцидента
        :param resolution_comment: Комментарий при закрытии
        :return: Обновленный инцидент
        """
        incident = self.incident_repository.get_by_id(incident_id)
        
        if not incident:
            raise ValueError("Инцидент не найден")
        
        if incident['status'] == 'closed':
            raise ValueError("Инцидент уже закрыт")
        
        # Проверка бизнес-правил
        if incident['threat_level'] >= 4 and not resolution_comment:
            raise ValueError("Для инцидентов с высоким уровнем угрозы требуется комментарий решения")
        
        if self.incident_repository.has_pending_actions(incident_id):
            raise ValueError("Не все связанные действия завершены")

        # Подготовка данных для обновления
        update_data = {
            'status': 'closed',
            'closed_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        if resolution_comment:
            update_data['resolution_comment'] = resolution_comment

        return self.incident_repository.update(incident_id, update_data)

    def get_open_incidents_by_threat(self, min_threat_level: int) -> List[dict]:
        """
        Получение открытых инцидентов с уровнем угрозы выше заданного
        :param min_threat_level: Минимальный уровень угрозы
        :return: Список инцидентов
        """
        if not (1 <= min_threat_level <= 5):
            raise ValueError("Уровень угрозы должен быть в диапазоне 1-5")
        
        return self.incident_repository.find_open_by_threat(min_threat_level)

#DAL
class IncidentRepository:
    def create(self, data: dict) -> dict:
        """Абстрактный метод для создания инцидента"""
        pass
    
    def get_by_id(self, incident_id: int) -> Optional[dict]:
        """Абстрактный метод для получения инцидента по ID"""
        pass
    
    def update(self, incident_id: int, data: dict) -> dict:
        """Абстрактный метод для обновления инцидента"""
        pass
    
    def find_open_by_threat(self, min_threat_level: int) -> List[dict]:
        """Абстрактный метод для поиска по уровню угрозы"""
        pass
    
    def has_pending_actions(self, incident_id: int) -> bool:
        """Абстрактный метод для проверки незавершенных действий"""
        pass

#использование
# Инициализация
repository = IncidentRepository()  # Реальная или mock-реализация
incident_service = IncidentService(repository)

# Создание инцидента
try:
    new_incident = incident_service.create_incident({
        'title': 'Утечка данных',
        'description': 'Обнаружена утечка персональных данных',
        'threat_level': 4
    })
    print(f"Создан инцидент: {new_incident}")
except ValueError as e:
    print(f"Ошибка: {e}")

# Закрытие инцидента
try:
    closed_incident = incident_service.close_incident(
        incident_id=123,
        resolution_comment="Проблема решена, данные защищены"
    )
    print(f"Инцидент закрыт: {closed_incident}")
except ValueError as e:
    print(f"Ошибка при закрытии: {e}")

# Получение опасных инцидентов
critical_incidents = incident_service.get_open_incidents_by_threat(4)
print(f"Критические инциденты: {critical_incidents}")


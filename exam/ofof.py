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
from django.urls import path
from . import views

urlpatterns = [
    path('reporte-r09/', views.descargar_reporte_r09, name='reporte_r09'),
]

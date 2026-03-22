from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('metrics/', views.metrics, name='metrics'),
    path('seckill-stats/', views.seckill_stats, name='seckill_stats'),
]
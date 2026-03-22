from django.urls import path
from .views import SeckillView, OrderStatusView, HomeView, CreateActivityView

urlpatterns = [
    path('seckill/', SeckillView.as_view(), name='seckill'),
    path('order/status/', OrderStatusView.as_view(), name='order_status'),
    path('create_activity/', CreateActivityView.as_view(), name='create_activity'),
]

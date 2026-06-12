# inventory/urls.py
from django.urls import path
from . import views

# inventory/urls.py

urlpatterns = [
    # === ДАШБОРД И УСТРОЙСТВА ===
    path('', views.dashboard, name='dashboard'),
    path('devices/', views.device_list, name='device_list'),
    path('devices/add/', views.add_device, name='add_device'),
    
    # === ТИКЕТЫ ===
    path('my-tickets/', views.user_tickets, name='user_tickets'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    
    # ✅ ПРОВЕРЬ ЭТУ СТРОКУ (должна быть именно так):
    path('manage/tickets/<int:ticket_id>/', views.admin_ticket_detail, name='admin_ticket_detail'),
    
    # === ДЕЙСТВИЯ С УСТРОЙСТВАМИ ===
    path('devices/<str:inventory_number>/status/', views.change_device_status, name='change_device_status'),
    path('devices/<str:inventory_number>/assign/', views.assign_device, name='assign_device'),
    path('devices/<str:inventory_number>/label/', views.print_inventory_label, name='print_inventory_label'),
    path('devices/print-labels/', views.print_inventory_labels_batch, name='print_inventory_labels_batch'),
    
    # === КАРТОЧКА УСТРОЙСТВА (ВСЕГДА В КОНЦЕ!) ===
    path('devices/<str:inventory_number>/', views.device_detail, name='device_detail'),
    
    # === API ===
    path('api/device-template/<int:device_type_id>/', views.get_device_template, name='get_device_template'),

    path('all-tickets/', views.all_tickets, name='all_tickets'),
]
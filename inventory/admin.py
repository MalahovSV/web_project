from django.contrib import admin
from .models import (
    Position, LocationType, Location, DeviceStatus, 
    Manufacturer, DeviceType, TicketStatus,
    Employee, Device, Movement, Ticket
)

# ========== СПРАВОЧНИКИ ==========

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('id_position', 'name')
    search_fields = ('name',)

@admin.register(LocationType)
class LocationTypeAdmin(admin.ModelAdmin):
    list_display = ('id_type', 'name')

@admin.register(DeviceStatus)
class DeviceStatusAdmin(admin.ModelAdmin):
    list_display = ('id_status', 'name')

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('id_manufacturer', 'name')
    search_fields = ('name',)

@admin.register(TicketStatus)
class TicketStatusAdmin(admin.ModelAdmin):
    list_display = ('id_status', 'name')

# ========== ОСНОВНЫЕ ТАБЛИЦЫ ==========

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id_location', 'name', 'type')
    list_filter = ('type',)
    search_fields = ('name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id_employee', 'user', 'position', 'department', 'is_mol')
    list_filter = ('position', 'is_mol')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(DeviceType)
class DeviceTypeAdmin(admin.ModelAdmin):
    list_display = ('id_device_type', 'name')
    search_fields = ('name',)

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('inventory_number', 'name', 'device_type', 'manufacturer', 'status')
    list_filter = ('status', 'device_type', 'manufacturer')
    search_fields = ('inventory_number', 'name')
    
    # Показываем JSON-характеристики красиво
    readonly_fields = ('json_file_characteristics', 'json_file_settings')

@admin.register(Movement)
class MovementAdmin(admin.ModelAdmin):
    list_display = ('id_movement', 'movement_date', 'device', 'employee', 'location')
    list_filter = ('movement_date', 'location')
    date_hierarchy = 'movement_date'

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id_ticket', 'created_at', 'device', 'employee', 'status')
    list_filter = ('status', 'created_at')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
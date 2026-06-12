from django.db import models
from django.conf import settings

# ==========================================
# СПРАВОЧНИКИ (managed = False)
# ==========================================

class Position(models.Model):
    id_position = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'positions'
        managed = False  # Таблица создана вручную
        verbose_name = 'Должность'
    def __str__(self):  
        return self.name
class LocationType(models.Model):
    id_type = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'location_types'
        managed = False
        verbose_name = 'Вид местоположения'
    def __str__(self):  
        return self.name

class DeviceStatus(models.Model):
    id_status = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'device_statuses'
        managed = False
        verbose_name = 'Статус устройства'
    def __str__(self):  
        return self.name

class Manufacturer(models.Model):
    id_manufacturer = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'manufacturers'
        managed = False
        verbose_name = 'Производитель'
    def __str__(self):  
        return self.name

class TicketStatus(models.Model):
    id_status = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'ticket_statuses'
        managed = False
        verbose_name = 'Статус тикета'
    def __str__(self):  
        return self.name

# ==========================================
# ОСНОВНЫЕ ТАБЛИЦЫ
# ==========================================

class Location(models.Model):
    id_location = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    # FK на LocationType
    type = models.ForeignKey(LocationType, on_delete=models.PROTECT, db_column='id_type')

    class Meta:
        db_table = 'locations'
        managed = False
        verbose_name = 'Местоположение'
    
    def __str__(self):  
        return self.name

class Employee(models.Model):
    id_employee = models.AutoField(primary_key=True)
    # 🔥 Связь с системным пользователем Django (auth_user)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        db_column='user_id'
    )
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    is_mol = models.BooleanField(default=False)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, db_column='id_position')

    class Meta:
        db_table = 'employees'
        managed = False
        verbose_name = 'Сотрудник'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class DeviceType(models.Model):
    id_device_type = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    # JSONB поля
    json_template_characteristics = models.JSONField(blank=True, null=True)
    json_template_settings = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'device_types'
        managed = False
        verbose_name = 'Тип устройства'
    def __str__(self):  
        return self.name

class Device(models.Model):
    inventory_number = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=255)
    # JSONB поля
    json_file_characteristics = models.JSONField(blank=True, null=True)
    json_file_settings = models.JSONField(blank=True, null=True)
    
    status = models.ForeignKey(DeviceStatus, on_delete=models.PROTECT, db_column='id_status')
    device_type = models.ForeignKey(DeviceType, on_delete=models.PROTECT, db_column='id_type')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, db_column='id_manufacturer')

    class Meta:
        db_table = 'devices'
        managed = False
        verbose_name = 'Устройство'

        

class Movement(models.Model):
    id_movement = models.AutoField(primary_key=True)
    movement_date = models.DateTimeField()
    
    device = models.ForeignKey(Device, on_delete=models.CASCADE, db_column='id_device')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, db_column='id_employee')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, db_column='id_location')
    comment = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'movements'
        managed = False
        verbose_name = 'Движение устройства'

class Ticket(models.Model):
    id_ticket = models.AutoField(primary_key=True)
    created_at = models.DateTimeField()
    comment = models.TextField(blank=True)
    technical_response = models.TextField(blank=True)
    
    status = models.ForeignKey(TicketStatus, on_delete=models.PROTECT, db_column='id_status')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, db_column='inventory_number')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, db_column='id_employee')

    class Meta:
        db_table = 'tickets'
        managed = False
        verbose_name = 'Тикет'
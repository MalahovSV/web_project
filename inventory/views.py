import base64
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from .models import Device, Ticket, Movement, Employee, Location, DeviceStatus, DeviceType
from django.urls import reverse
from .utils import generate_qr_code, get_device_qr_url, render_characteristics_html, render_settings_html
from django.contrib.auth.decorators import login_required
import json
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .forms import DeviceAddForm
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Ticket, Device, Employee, TicketStatus
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction


def is_staff(user):
    """Проверка: пользователь является админом/стаффом"""
    return user.is_staff






@login_required
def print_inventory_label(request, inventory_number):
    """Печать инвентарной этикетки с QR-кодом"""
    device = get_object_or_404(
        Device.objects.select_related('status', 'device_type', 'manufacturer'),
        inventory_number=inventory_number
    )
    
    # Генерируем QR-код
    qr_buffer = generate_qr_code(get_device_qr_url(device), size=300)
    qr_base64 = base64.b64encode(qr_buffer.read()).decode('utf-8')
    
    context = {
        'device': device,
        'qr_code': qr_base64,
        'qr_url': get_device_qr_url(device),
        'org_name': "Администрация города Рубцовска",  # Или из org_data.json
    }
    
    html = render_to_string('devices/inventory_label.html', context)
    
    return HttpResponse(html)

@login_required
def print_inventory_labels_batch(request):
    """Печать нескольких этикеток (массовая печать)"""
    # Получаем список инвентарных номеров из GET параметров
    inventory_numbers = request.GET.getlist('devices')
    
    if not inventory_numbers:
        return HttpResponse("❌ Не выбраны устройства для печати", status=400)
    
    devices_data = []
    for inv_num in inventory_numbers:
        try:
            device = Device.objects.select_related(
                'status', 'device_type', 'manufacturer'
            ).get(inventory_number=inv_num)
            
            qr_buffer = generate_qr_code(get_device_qr_url(device), size=250)
            qr_base64 = base64.b64encode(qr_buffer.read()).decode('utf-8')
            
            devices_data.append({
                'device': device,
                'qr_code': qr_base64,
            })
        except Device.DoesNotExist:
            continue
    
    context = {
        'devices': devices_data,
        'org_name': "МБОУ \"Средняя общеобразовательная школа №3\"",
    }
    
    html = render_to_string('devices/inventory_labels_batch.html', context)
    return HttpResponse(html)


# inventory/views.py

@login_required
@user_passes_test(is_staff)
def change_device_status(request, inventory_number):
    """Админ: смена статуса устройства с журналированием"""
    device = get_object_or_404(
        Device.objects.select_related('status', 'device_type', 'manufacturer'),
        inventory_number=inventory_number
    )
    
    statuses = DeviceStatus.objects.all()
    locations = Location.objects.all().order_by('name')  # ✅ ВСЕГДА передаём локации
    
    if request.method == 'POST':
        new_status_id = request.POST.get('status')
        comment = request.POST.get('comment', '').strip()
        location_id = request.POST.get('location') or None
        
        if new_status_id:
            try:
                with transaction.atomic():
                    old_status = device.status.name
                    device.status_id = new_status_id
                    device.save()
                    new_status = DeviceStatus.objects.get(id_status=new_status_id).name
                    
                    # Автоматическое снятие с МОЛ при ремонте/складе
                    if new_status in ['В ремонте', 'На складе']:
                        Movement.objects.create(
                            device=device,
                            employee=None,
                            location_id=location_id,
                            movement_date=timezone.now(),
                            comment=f"Смена статуса: {old_status} → {new_status}. {comment}" if comment else f"Смена статуса: {old_status} → {new_status}"
                        )
                        messages.success(request, f"✅ Статус: {new_status}. Устройство снято с ответственного.")
                    else:
                        Movement.objects.create(
                            device=device,
                            employee=device.movement_set.filter(employee__isnull=False).order_by('-movement_date').first().employee if device.movement_set.exists() else None,
                            location_id=location_id,
                            movement_date=timezone.now(),
                            comment=f"Смена статуса: {old_status} → {new_status}. {comment}" if comment else f"Смена статуса: {old_status} → {new_status}"
                        )
                        messages.success(request, f"✅ Статус изменён: {old_status} → {new_status}")
                        
            except Exception as e:
                messages.error(request, f" Ошибка: {e}")
            
            return redirect('device_detail', inventory_number=device.inventory_number)
    
    context = {
        'device': device,
        'statuses': statuses,
        'current_status_id': device.status_id,
        'locations': locations,  # ✅ Теперь список всегда заполнен
    }
    return render(request, 'devices/change_status.html', context)

@login_required
@user_passes_test(is_staff)
def admin_ticket_detail(request, ticket_id):
    """Админ-панель: управление заявкой (статус, ответ, отмена)"""
    ticket = get_object_or_404(
        Ticket.objects.select_related('device', 'employee__user', 'status'),
        id_ticket=ticket_id
    )
    
    statuses = TicketStatus.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 🔄 Смена статуса
        if action == 'change_status':
            new_status_id = request.POST.get('status')
            if new_status_id:
                ticket.status_id = new_status_id
                ticket.save()
                messages.success(request, f"✅ Статус изменён на: {ticket.status.name}")
        
        # 💬 Добавление/обновление ответа
        elif action == 'add_response':
            response = request.POST.get('technical_response', '').strip()
            if response:
                ticket.technical_response = response
                ticket.save()
                messages.success(request, "✅ Ответ сохранён")
        
        # ❌ Отмена заявки (статус "Отклонен")
        elif action == 'cancel':
            cancelled_status = TicketStatus.objects.filter(name='Отклонен').first()
            if cancelled_status:
                ticket.status = cancelled_status
                ticket.save()
                messages.info(request, "🚫 Заявка отменена")
        
        # 🗑️ Удаление заявки (только если ещё не в работе)
        elif action == 'delete' and ticket.status.name in ['Новый', 'Отклонен']:
            ticket_id = ticket.id_ticket
            ticket.delete()
            messages.success(request, f"🗑️ Заявка #{ticket_id} удалена")
            return redirect('dashboard')
        
        return redirect('admin_ticket_detail', ticket_id=ticket.id_ticket)
    
    context = {
        'ticket': ticket,
        'statuses': statuses,
        'current_status_id': ticket.status_id
    }
    return render(request, 'tickets/admin_ticket_detail.html', context)


def is_regular_user(user):
    """Проверка: пользователь НЕ является админом/стаффом"""
    return not user.is_staff

@login_required
@user_passes_test(is_regular_user)
def user_tickets(request):
    """Страница пользователя: создание и просмотр своих тикетов"""
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        messages.error(request, "Ваш профиль сотрудника не найден.")
        return redirect('dashboard')
    
    # Обработка создания тикета
    if request.method == 'POST':
        device_id = request.POST.get('device')
        comment = request.POST.get('comment', '').strip()
        
        if device_id and comment:
            try:
                device = Device.objects.get(inventory_number=device_id)
                Ticket.objects.create(
                    created_at=timezone.now(),
                    comment=comment,
                    status_id=1,  # ✅ Используем status_id для создания (PK статуса "Новый")
                    device=device,  # ✅ Имя поля из модели
                    employee=employee  # ✅ Имя поля из модели
                )
                messages.success(request, "✅ Заявка успешно создана!")
                return redirect('user_tickets')
            except Device.DoesNotExist:
                messages.error(request, "❌ Устройство не найдено")
        else:
            messages.error(request, "❌ Заполните все поля")
    
    # Получаем устройства сотрудника
    from .models import Movement
    user_devices = Device.objects.filter(
        movement__employee=employee
    ).select_related('status', 'device_type').distinct()
    
    # Получаем тикеты сотрудника
    user_tickets_list = Ticket.objects.filter(
        employee=employee  # ✅ Имя поля из модели
    ).select_related('status', 'device').order_by('-created_at')
    
    context = {
        'employee': employee,
        'devices': user_devices,
        'tickets': user_tickets_list,
    }
    return render(request, 'tickets/user_tickets.html', context)


@login_required
def ticket_detail(request, ticket_id):
    """Просмотр деталей тикета"""
    ticket = get_object_or_404(
        Ticket.objects.select_related('device', 'employee__user', 'status'),
        id_ticket=ticket_id
    )
    
    # Проверка доступа
    if not request.user.is_staff and ticket.employee.user != request.user:
        messages.error(request, "Доступ запрещён")
        return redirect('user_tickets')
    
    context = {'ticket': ticket}
    return render(request, 'tickets/ticket_detail.html', context)

@login_required
def ticket_detail(request, ticket_id):
    """Просмотр деталей тикета"""
    # ✅ ИСПРАВЛЕНО: указываем имена полей модели, а не колонки БД
    ticket = get_object_or_404(
        Ticket.objects.select_related('device', 'employee__user', 'status'),
        id_ticket=ticket_id
    )

    # Проверка доступа (обычный юзер видит только свои тикеты)
    if not request.user.is_staff and ticket.employee.user != request.user:
        messages.error(request, "Доступ запрещён")
        return redirect('user_tickets')

    context = {'ticket': ticket}
    return render(request, 'tickets/ticket_detail.html', context)



@login_required
def dashboard(request):
    """Главная страница - дашборд"""
    
    # Получаем профиль сотрудника (может быть None)
    employee = None
    try:
        employee = Employee.objects.select_related('user', 'position').get(user=request.user)
    except Employee.DoesNotExist:
        pass

    # === ИНИЦИАЛИЗАЦИЯ ПЕРЕМЕННЫХ ПО УМОЛЧАНИЮ ===
    # Это гарантирует, что все переменные существуют для шаблона
    total = active = repair = warehouse = tickets = 0
    movements = []
    recent_tickets = []
    active_tickets_count = 0

    if request.user.is_staff:
        # === СТАТИСТИКА ДЛЯ АДМИНОВ ===
        total = Device.objects.count()
        active = Device.objects.filter(status__name='В эксплуатации').count()
        repair = Device.objects.filter(status__name='В ремонте').count()
        warehouse = Device.objects.filter(status__name='На складе').count()
        
        # ✅ Правильное имя поля: status (не id_status!)
        open_tickets = Ticket.objects.filter(
            status__name__in=['Новый', 'В работе']
        ).count()
        
        movements = Movement.objects.select_related(
            'device', 'employee__user', 'location'
        ).order_by('-movement_date')[:10]
        
        recent_tickets = Ticket.objects.select_related(
            'device', 'employee__user', 'status'
        ).order_by('-created_at')[:10]
        
        tickets = open_tickets  # для совместимости с шаблоном
        
    else:
        # === ДЛЯ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ ===
        # Переменные уже инициализированы нулями/пустыми списками выше
        
        # Считаем активные заявки пользователя
        if employee:
            active_tickets_count = employee.ticket_set.exclude(
                status__name__in=["Выполнен", "Отклонен"]
            ).count()

    # === КОНТЕКСТ СОЗДАЁТСЯ В ЛЮБОМ СЛУЧАЕ ===
    context = {
        'employee': employee,
        'total': total,
        'active': active,
        'repair': repair,
        'warehouse': warehouse,
        'tickets': tickets,
        'movements': movements,
        'recent_tickets': recent_tickets,
        'active_tickets_count': active_tickets_count,
    }
    
    return render(request, 'dashboard.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)  # Только для админов/ИТ
def device_list(request):
    """Список всех устройств с фильтрами"""
    devices = Device.objects.select_related(
        'status', 'device_type', 'manufacturer'
    ).all()
    
    # Фильтры из GET параметров
    status_id = request.GET.get('status')
    location_id = request.GET.get('location')
    search = request.GET.get('search', '')
    
    if status_id:
        devices = devices.filter(status_id=status_id)
    if location_id:
        # Ищем устройства через таблицу movements
        devices = devices.filter(movement__location_id=location_id).distinct()
    if search:
        devices = devices.filter(
            Q(inventory_number__icontains=search) |
            Q(name__icontains=search)
        )
    
    # Получаем справочники для фильтров
    statuses = DeviceStatus.objects.all()
    locations = Location.objects.all()
    
    context = {
        'devices': devices,
        'statuses': statuses,
        'locations': locations,
        'current_status': status_id,
        'current_location': location_id,
        'search_query': search
    }
    return render(request, 'devices/device_list.html', context)

@login_required
def device_detail(request, inventory_number):
    """Детальная информация об устройстве"""
    device = get_object_or_404(
        Device.objects.select_related('status', 'device_type', 'manufacturer'),
        inventory_number=inventory_number
    )
    
    # История перемещений
    movements = Movement.objects.filter(
        device=device
    ).select_related('employee__user', 'location').order_by('-movement_date')
    
    # Тикеты по этому устройству
    tickets = Ticket.objects.filter(
        device=device
    ).select_related('status', 'employee__user').order_by('-created_at')
    
    # Текущее местоположение и МОЛ (последняя запись в movements)
    current_movement = movements.first()
    specs_dict = device.json_file_characteristics
    specs_html = render_characteristics_html(specs_dict)
    status_history = Movement.objects.filter(
        device=device
    ).select_related('location').order_by('-movement_date')[:10]

    specs_dict = device.json_file_characteristics
    specs_html = render_characteristics_html(specs_dict)
    
    settings_dict = device.json_file_settings
    settings_html = render_settings_html(settings_dict)  # ✅ НОВОЕ
    
    # История статусов
    status_history = Movement.objects.filter(
        device=device
    ).select_related('location').order_by('-movement_date')[:10]


    context = {
        'device': device,
        'movements': movements,
        'tickets': tickets,
        'current_movement': current_movement,
        'specs_html': specs_html,
        'settings_html': settings_html, 
        'status_history': status_history,
    }
    return render(request, 'devices/device_detail.html', context)


def employee_devices(request, employee_id):
    """Устройства, закрепленные за сотрудником"""
    employee = get_object_or_404(
        Employee.objects.select_related('user', 'position'),
        id_employee=employee_id
    )
    
    # Получаем устройства через последнюю запись в movements
    devices = Device.objects.filter(
        movements__employee=employee
    ).select_related('status', 'device_type', 'manufacturer').distinct()
    
    context = {
        'employee': employee,
        'devices': devices
    }
    return render(request, 'employees/employee_devices.html', context)
User = get_user_model()
@login_required
def add_device(request):
    """Добавление нового устройства с авто-закреплением за админом"""
    if request.method == 'POST':
        form = DeviceAddForm(request.POST)
        if form.is_valid():
            try:
                device = form.save(commit=False)
                
                if form.cleaned_data.get('characteristics_data'):
                    device.json_file_characteristics = json.loads(form.cleaned_data['characteristics_data'])
                if form.cleaned_data.get('settings_data'):
                    device.json_file_settings = json.loads(form.cleaned_data['settings_data'])
                
                device.save()
                
                # 🆕 АВТО-ЗАКРЕПЛЕНИЕ ЗА АДМИНИСТРАТОРОМ
                try:
                    # Ищем или создаем профиль сотрудника для текущего пользователя
                    admin_emp, _ = Employee.objects.get_or_create(user=request.user)
                    
                    # Находим склад ИТ (или первый доступный location)
                    default_loc = Location.objects.filter(name__icontains='Склад').first() or Location.objects.first()
                    
                    Movement.objects.create(
                        device=device,
                        employee=admin_emp,
                        location=default_loc,
                        movement_date=timezone.now()
                    )
                    messages.success(request, f"✅ Устройство {device.inventory_number} создано и закреплено за вами (Администратором).")
                except Exception as e:
                    messages.warning(request, f"Устройство создано, но авто-закрепление не удалось: {e}")
                    
                return redirect('device_detail', inventory_number=device.inventory_number)
                
            except Exception as e:
                messages.error(request, f"❌ Ошибка при сохранении: {e}")
    else:
        form = DeviceAddForm()
    
    return render(request, 'devices/device_add.html', {'form': form})

@require_http_methods(["GET"])
def get_device_template(request, device_type_id):
    """API: Возвращает JSON-шаблон для выбранного типа устройства"""
    try:
        device_type = DeviceType.objects.get(id_device_type=device_type_id)
        template = {
            'characteristics': device_type.json_template_characteristics or {},
            'settings': device_type.json_template_settings or {}
        }
        return JsonResponse(template)
    except DeviceType.DoesNotExist:
        return JsonResponse({'error': 'Тип устройства не найден'}, status=404)
    
@login_required
def assign_device(request, inventory_number):
    """Форма передачи устройства ответственному МОЛ"""
    device = get_object_or_404(Device, inventory_number=inventory_number)
    
    # Показываем только тех, у кого стоит флаг МОЛ (или всех сотрудников)
    employees = Employee.objects.filter(is_mol=True).select_related('user', 'position')
    locations = Location.objects.all()
    
    if request.method == 'POST':
        emp_id = request.POST.get('employee')
        loc_id = request.POST.get('location')
        comment = request.POST.get('comment', '')
        
        if emp_id and loc_id:
            try:
                emp = Employee.objects.get(id_employee=emp_id)
                loc = Location.objects.get(id_location=loc_id)
                
                Movement.objects.create(
                    device=device,
                    employee=emp,
                    location=loc,
                    movement_date=timezone.now()
                )
                messages.success(request, f"✅ Устройство передано: {emp.user.get_full_name()} ({loc.name})")
                return redirect('device_detail', inventory_number=device.inventory_number)
            except Exception as e:
                messages.error(request, f"❌ Ошибка при передаче: {e}")
    
    context = {
        'device': device,
        'employees': employees,
        'locations': locations
    }
    return render(request, 'devices/assign_device.html', context)

@login_required
@user_passes_test(is_staff)
def all_tickets(request):
    """Страница админа: все заявки с фильтрами"""
    tickets = Ticket.objects.select_related(
        'device', 
        'device__device_type',
        'employee__user', 
        'status'
    ).order_by('-created_at')
    
    # Фильтры
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        tickets = tickets.filter(status_id=status_filter)
    
    if search_query:
        tickets = tickets.filter(
            Q(device__inventory_number__icontains=search_query) |
            Q(device__name__icontains=search_query) |
            Q(comment__icontains=search_query) |
            Q(employee__user__first_name__icontains=search_query) |
            Q(employee__user__last_name__icontains=search_query)
        )
    
    # Статистика
    all_tickets = Ticket.objects.all()
    stats = {
        'total': all_tickets.count(),
        'new': all_tickets.filter(status__name='Новый').count(),
        'in_progress': all_tickets.filter(status__name='В работе').count(),
        'completed': all_tickets.filter(status__name='Выполнен').count(),
        'cancelled': all_tickets.filter(status__name='Отклонен').count(),
    }
    
    context = {
        'tickets': tickets,
        'stats': stats,
        'statuses': TicketStatus.objects.all(),
        'current_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'tickets/all_tickets.html', context)
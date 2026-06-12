# reports/views.py
import json
import os
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from inventory.models import Device, Employee, Movement, DeviceStatus, Location, Ticket, TicketStatus

def load_org_data():
    """Загружает и структурирует данные организации из org_data.json"""
    org_data_path = os.path.join(settings.BASE_DIR, 'org_data.json')
    try:
        with open(org_data_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        org = raw.get('organization', {})
        contacts = raw.get('contacts', {})
        responsible = raw.get('responsible_persons', {})
        it_dept = raw.get('it_department', {})
        
        return {
            'org_full_name': org.get('full_name', ''),
            'org_short_name': org.get('short_name', ''),
            'org_legal_address': org.get('legal_address', ''),
            'org_inn': org.get('inn', ''),
            'org_kpp': org.get('kpp', ''),
            'org_ogrn': org.get('ogrn', ''),
            'contact_phone': contacts.get('phone_reception', ''),
            'contact_fax': contacts.get('fax', ''),
            'contact_email': contacts.get('email', ''),
            'contact_website': contacts.get('website', ''),
            'head_fio': responsible.get('head', {}).get('fio', ''),
            'head_position': responsible.get('head', {}).get('position', ''),
            'accountant_fio': responsible.get('chief_accountant', {}).get('fio', ''),
            'accountant_position': responsible.get('chief_accountant', {}).get('position', ''),
            'it_head_fio': responsible.get('it_head', {}).get('fio', ''),
            'it_head_position': responsible.get('it_head', {}).get('position', ''),
            'it_dept_name': it_dept.get('name', ''),
            'it_dept_phone': it_dept.get('phone', ''),
            'it_dept_email': it_dept.get('email', ''),
            'it_dept_address': it_dept.get('address', ''),
        }
    except Exception as e:
        return {
            'org_full_name': 'МБОУ "СОШ №3"',
            'org_short_name': 'МБОУ "СОШ №3"',
            'org_legal_address': '',
            'org_inn': '',
            'org_kpp': '',
            'head_fio': '',
            'it_head_fio': '',
            'it_dept_name': 'ИТ-отдел',
        }

def flatten_json_values(data):
    """Рекурсивно собирает все строковые и числовые значения из вложенного JSON"""
    values = []
    if isinstance(data, dict):
        for v in data.values():
            values.extend(flatten_json_values(v))
    elif isinstance(data, list):
        for item in data:
            values.extend(flatten_json_values(item))
    elif isinstance(data, (str, int, float)):
        val = str(data).strip()
        if val and val not in ('0', '0.0', 'false', 'False', 'null', 'None'):
            values.append(val)
    return values


@login_required
def reports_list(request):
    """Страница со списком всех доступных отчетов"""
    report_types = [
        {
            'id': 'list',
            'name': '📋 Полный реестр оборудования',
            'desc': 'Все устройства с характеристиками, стоимостью и местоположением',
            'icon': '📋',
            'url': f'/reports/print/?type=list'
        },
        {
            'id': 'network',
            'name': '🌐 Сетевая информация',
            'desc': 'IP-адреса, MAC-адреса, DNS и сетевые настройки',
            'icon': '🌐',
            'url': f'/reports/print/?type=network'
        },
        {
            'id': 'value',
            'name': '💰 Анализ стоимости',
            'desc': 'Устройства по стоимости с фильтрами и итоговой суммой',
            'icon': '💰',
            'url': f'/reports/print/?type=value'
        },
        {
            'id': 'user',
            'name': '👤 Закрепленные устройства',
            'desc': 'Техника, закрепленная за конкретным сотрудником (МОЛ)',
            'icon': '👤',
            'url': f'/reports/print/?type=user&user_id={request.user.id}'
        },
        {
            'id': 'location',
            'name': '📍 Устройства по кабинетам',
            'desc': 'Распределение техники по помещениям школы',
            'icon': '📍',
            'url': f'/reports/print/?type=location'
        },
        {
            'id': 'status',
            'name': '🔧 Устройства по статусам',
            'desc': 'Статистика по состоянию оборудования (в работе, в ремонте и т.д.)',
            'icon': '🔧',
            'url': f'/reports/print/?type=status'
        },
        {
            'id': 'warranty',
            'name': '⏰ Гарантия и сроки',
            'desc': 'Устройства с истекающей или истекшей гарантией',
            'icon': '⏰',
            'url': f'/reports/print/?type=warranty'
        },
        {
            'id': 'tickets',
            'name': '🎫 Заявки и обслуживание',
            'desc': 'Статистика обращений в техподдержку',
            'icon': '🎫',
            'url': f'/reports/print/?type=tickets'
        },
    ]
    
    context = {
        'report_types': report_types,
        'page_title': 'Отчеты',
    }
    return render(request, 'reports/reports_list.html', context)


@login_required
def print_report(request):
    report_type = request.GET.get('type', 'list')
    user_id = request.GET.get('user_id', request.user.id)
    min_val = request.GET.get('min_value')
    max_val = request.GET.get('max_value')
    
    org_data = load_org_data()
    devices_qs = Device.objects.select_related('status', 'device_type', 'manufacturer').all()

    # Фильтрация по типу отчета
    if report_type == 'network':
        devices_list = [d for d in devices_qs if d.json_file_settings.get('сеть', {}).get('ip_адрес')]
    elif report_type == 'value':
        devices_list = [d for d in devices_qs if float(d.json_file_settings.get('стоимость_руб', 0)) > 0]
        if min_val: 
            devices_list = [d for d in devices_list if float(d.json_file_settings.get('стоимость_руб', 0)) >= float(min_val)]
        if max_val: 
            devices_list = [d for d in devices_list if float(d.json_file_settings.get('стоимость_руб', 0)) <= float(max_val)]
    elif report_type == 'user':
        try:
            emp = Employee.objects.get(user_id=user_id)
            dev_ids = Movement.objects.filter(employee=emp).values_list('device', flat=True)
            devices_list = list(devices_qs.filter(inventory_number__in=dev_ids))
        except Employee.DoesNotExist:
            devices_list = []
    elif report_type == 'location':
        # Группировка по кабинетам
        locations = Location.objects.all().order_by('name')
        location_data = []
        for loc in locations:
            loc_devices = [d for d in devices_qs if d.movement_set.first() and d.movement_set.first().location == loc]
            if loc_devices:
                location_data.append({
                    'location': loc,
                    'devices': loc_devices,
                    'count': len(loc_devices),
                })
        
        context = {
            'location_data': location_data,
            'report_type': report_type,
            'generated_at': timezone.now().strftime("%d.%m.%Y %H:%M"),
            'org': org_data,
            'total_locations': len(location_data),
            'total_devices': sum(loc['count'] for loc in location_data),
        }
        return render(request, 'reports/location_report.html', context)
    
    elif report_type == 'status':
        # Группировка по статусам
        statuses = DeviceStatus.objects.all()
        status_data = []
        for status in statuses:
            status_devices = list(devices_qs.filter(status=status))
            if status_devices:
                status_data.append({
                    'status': status,
                    'devices': status_devices,
                    'count': len(status_devices),
                })
        
        context = {
            'status_data': status_data,
            'report_type': report_type,
            'generated_at': timezone.now().strftime("%d.%m.%Y %H:%M"),
            'org': org_data,
        }
        return render(request, 'reports/status_report.html', context)
    
    elif report_type == 'warranty':
        # Гарантия
        from datetime import datetime, timedelta
        warranty_info = []
        for device in devices_qs:
            settings = device.json_file_settings
            if settings:
                year = settings.get('год_покупки')
                warranty_months = settings.get('гарантия_месяцев', 12)
                
                if year:
                    purchase_date = datetime(year, 1, 1)
                    warranty_end = purchase_date + timedelta(days=warranty_months*30)
                    days_left = (warranty_end - datetime.now()).days
                    
                    warranty_info.append({
                        'device': device,
                        'purchase_year': year,
                        'warranty_months': warranty_months,
                        'warranty_end': warranty_end,
                        'days_left': days_left,
                        'expired': days_left < 0,
                        'expiring_soon': 0 <= days_left <= 90,
                    })
        
        warranty_info.sort(key=lambda x: (x['expired'], x['days_left']))
        
        context = {
            'warranty_info': warranty_info,
            'report_type': report_type,
            'generated_at': timezone.now().strftime("%d.%m.%Y %H:%M"),
            'org': org_data,
            'expired_count': sum(1 for w in warranty_info if w['expired']),
            'expiring_soon_count': sum(1 for w in warranty_info if w['expiring_soon']),
        }
        return render(request, 'reports/warranty_report.html', context)
    
    elif report_type == 'tickets':
        # Заявки
        tickets = Ticket.objects.select_related(
            'device', 
            'employee__user', 
            'status'
        ).order_by('-created_at')
        
        stats = {
            'total': tickets.count(),
            'new': tickets.filter(status__name__icontains='нов').count(),
            'in_progress': tickets.filter(status__name__icontains='работ').count(),
            'completed': tickets.filter(status__name__icontains='выполн').count(),
            'cancelled': tickets.filter(status__name__icontains='отклон').count(),
        }
        
        context = {
            'tickets': tickets,
            'stats': stats,
            'report_type': report_type,
            'generated_at': timezone.now().strftime("%d.%m.%Y %H:%M"),
            'org': org_data,
        }
        return render(request, 'reports/tickets_report.html', context)
    
    else:
        # По умолчанию - полный список
        devices_list = list(devices_qs)

    # Предварительная обработка для шаблона (для list, network, value, user)
    processed_devices = []
    for d in devices_list:
        raw_chars = d.json_file_characteristics or {}
        flat_vals = flatten_json_values(raw_chars)
        chars_str = ', '.join(flat_vals) if flat_vals else '—'

        net = d.json_file_settings.get('сеть', {})
        net_parts = []
        if net.get('ip_адрес'): net_parts.append(f"IP: {net['ip_адрес']}")
        if net.get('mac_адрес'): net_parts.append(f"MAC: {net['mac_адрес']}")
        if net.get('dns_основной'): net_parts.append(f"DNS: {net['dns_основной']}")
        if net.get('dns_альтернативный'): net_parts.append(f"DNS2: {net['dns_альтернативный']}")
        if net.get('шлюз'): net_parts.append(f"GW: {net['шлюз']}")
        net_str = '<br>'.join(net_parts) if net_parts else '—'

        movement = d.movement_set.select_related('location', 'employee__user').first()

        processed_devices.append({
            'obj': d,
            'chars_str': chars_str,
            'net_str': net_str,
            'movement': movement,
            'cost': float(d.json_file_settings.get('стоимость_руб', 0)),
            'year': d.json_file_settings.get('год_покупки', '—')
        })

    context = {
        'devices': processed_devices,
        'report_type': report_type,
        'generated_at': timezone.now().strftime("%d.%m.%Y %H:%M"),
        'org': org_data
    }

    if report_type == 'value':
        context['total_value'] = sum(item['cost'] for item in processed_devices)
    elif report_type == 'user':
        try:
            context['target_user'] = Employee.objects.get(user_id=user_id).user
        except:
            context['target_user'] = request.user

    return render(request, 'reports/print_report.html', context)
# reports/views.py
import json
import os
from django.conf import settings
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from inventory.models import Device, Employee, Movement

def load_org_data():
    """Загружает и структурирует данные организации из org_data.json"""
    org_data_path = os.path.join(settings.BASE_DIR, 'org_data.json')
    try:
        with open(org_data_path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        # Возвращаем плоскую структуру для удобства в шаблоне
        org = raw.get('organization', {})
        contacts = raw.get('contacts', {})
        responsible = raw.get('responsible_persons', {})
        it_dept = raw.get('it_department', {})
        
        return {
            # Организация
            'org_full_name': org.get('full_name', ''),
            'org_short_name': org.get('short_name', ''),
            'org_legal_address': org.get('legal_address', ''),
            'org_inn': org.get('inn', ''),
            'org_kpp': org.get('kpp', ''),
            'org_ogrn': org.get('ogrn', ''),
            # Контакты
            'contact_phone': contacts.get('phone_reception', ''),
            'contact_fax': contacts.get('fax', ''),
            'contact_email': contacts.get('email', ''),
            'contact_website': contacts.get('website', ''),
            # Ответственные лица
            'head_fio': responsible.get('head', {}).get('fio', ''),
            'head_position': responsible.get('head', {}).get('position', ''),
            'accountant_fio': responsible.get('chief_accountant', {}).get('fio', ''),
            'accountant_position': responsible.get('chief_accountant', {}).get('position', ''),
            'it_head_fio': responsible.get('it_head', {}).get('fio', ''),
            'it_head_position': responsible.get('it_head', {}).get('position', ''),
            # ИТ-отдел
            'it_dept_name': it_dept.get('name', ''),
            'it_dept_phone': it_dept.get('phone', ''),
            'it_dept_email': it_dept.get('email', ''),
            'it_dept_address': it_dept.get('address', ''),
        }
    except Exception as e:
        # Fallback при ошибке
        return {
            'org_full_name': 'Администрация города',
            'org_short_name': 'Администрация',
            'org_legal_address': '',
            'org_inn': '',
            'org_kpp': '',
            'head_fio': '',
            'it_head_fio': '',
            'it_dept_name': 'Отдел ИТ',
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
def print_report(request):
    report_type = request.GET.get('type', 'list')
    user_id = request.GET.get('user_id', request.user.id)
    min_val = request.GET.get('min_value')
    max_val = request.GET.get('max_value')
    
    org_data = load_org_data()
    devices_qs = Device.objects.select_related('status', 'device_type', 'manufacturer').all()

    # Фильтрация
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
            dev_ids = Movement.objects.filter(employee=emp).values_list('id_device', flat=True)
            devices_list = list(devices_qs.filter(inventory_number__in=dev_ids))
        except Employee.DoesNotExist:
            devices_list = []
    else:
        devices_list = list(devices_qs)

    # Предварительная обработка для шаблона
    processed_devices = []
    for d in devices_list:
        # Характеристики: только значения через запятую
        raw_chars = d.json_file_characteristics or {}
        flat_vals = flatten_json_values(raw_chars)
        chars_str = ', '.join(flat_vals) if flat_vals else '—'

        # Сеть: аккуратный список ключ-значение
        net = d.json_file_settings.get('сеть', {})
        net_parts = []
        if net.get('ip_адрес'): net_parts.append(f"IP: {net['ip_адрес']}")
        if net.get('mac_адрес'): net_parts.append(f"MAC: {net['mac_адрес']}")
        if net.get('dns_основной'): net_parts.append(f"DNS: {net['dns_основной']}")
        if net.get('dns_альтернативный'): net_parts.append(f"DNS2: {net['dns_альтернативный']}")
        if net.get('шлюз'): net_parts.append(f"GW: {net['шлюз']}")
        net_str = '<br>'.join(net_parts) if net_parts else '—'

        # Текущее движение
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
        'org': org_data  # Передаем как 'org' для краткости
    }

    if report_type == 'value':
        context['total_value'] = sum(item['cost'] for item in processed_devices)
    elif report_type == 'user':
        try:
            context['target_user'] = Employee.objects.get(user_id=user_id).user
        except:
            context['target_user'] = request.user

    return render(request, 'reports/print_report.html', context)
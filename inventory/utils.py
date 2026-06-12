import qrcode
from io import BytesIO
from django.conf import settings

# inventory/utils.py
import qrcode
from io import BytesIO
from django.conf import settings

def generate_qr_code(data, size=200):
    """
    Генерирует QR-код для переданных данных
    Возвращает BytesIO объект с изображением
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))
    
    # Сохраняем в BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer

def get_device_qr_url(device):
    """Возвращает URL для QR-кода устройства"""
    return f"{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'http://localhost:8000'}/devices/{device.inventory_number}/"


def format_spec_value(value):
    """Вспомогательная функция для форматирования значения"""
    if isinstance(value, bool):
        return "Да" if value else "Нет"
    if isinstance(value, int):
        return str(value)
    return str(value)

def render_characteristics_html(json_data):
    """Рендеринг технических характеристик"""
    if not json_data:
        return '<p style="color:#718096;">Характеристики не заполнены</p>'

    section_names = {
        'процессор': 'Процессор',
        'материнская_плата': 'Материнская плата',
        'видеокарта': 'Видеокарта',
        'оперативная_память': 'Оперативная память',
        'накопитель': 'Накопитель',
        'блок_питания': 'Блок питания',
        'охлаждение': 'Охлаждение',
        'монитор': 'Монитор',
        'экран': 'Экран',
        'аккумулятор': 'Аккумулятор',
        'печать': 'Печать',
        'сканирование': 'Сканирование',
        'подключение': 'Подключение',
    }

    html = '<table class="specs-main-table">'
    
    for key, value in json_data.items():
        title = section_names.get(key, key.replace('_', ' ').title())
        
        html += f'<tr>'
        html += f'<th class="spec-title">{title}</th>'
        html += '<td class="spec-content">'
        
        if isinstance(value, dict):
            html += render_dict_to_html(value)
        elif isinstance(value, list):
            html += render_list_to_html(value)
        else:
            html += f'<span class="spec-text">{format_spec_value(value)}</span>'
            
        html += '</td></tr>'

    html += '</table>'
    return html


def render_settings_html(json_data):
    """Рендеринг программных настроек (ОС, сеть, софт)"""
    if not json_data:
        return '<p style="color:#718096;">Настройки не заполнены</p>'

    section_names = {
        'операционная_система': 'Операционная система',
        'сеть': 'Сетевые настройки',
        'антивирус': 'Антивирусная защита',
        'домен': 'Домен',
        'расписание_резервного_копирования': 'Резервное копирование',
        'удаленный_доступ': 'Удалённый доступ',
        'автоматические_обновления': 'Автообновления',
        'схема_питания': 'Схема питания',
        'bitlocker': 'BitLocker',
        'год_покупки': 'Год покупки',
        'стоимость_руб': 'Стоимость',
        'версия_драйвера': 'Драйвер',
        'порог_тонера_процентов': 'Порог тонера',
        'лоток_по_умолчанию': 'Лоток по умолчанию',
        'эко_режим': 'ECO режим',
    }

    html = '<table class="specs-main-table">'
    
    for key, value in json_data.items():
        title = section_names.get(key, key.replace('_', ' ').title())
        
        html += f'<tr>'
        html += f'<th class="spec-title">{title}</th>'
        html += '<td class="spec-content">'
        
        if isinstance(value, dict):
            html += render_dict_to_html(value)
        elif isinstance(value, bool):
            html += f'<span class="spec-text">{"✅ Да" if value else "❌ Нет"}</span>'
        elif isinstance(value, (int, float)):
            if key == 'стоимость_руб':
                html += f'<span class="spec-text" style="font-weight: 600; color: #2d3748;">{value:,.2f} ₽</span>'
            else:
                html += f'<span class="spec-text">{value}</span>'
        elif isinstance(value, str):
            if value:
                html += f'<span class="spec-text">{value}</span>'
            else:
                html += '<span class="spec-text" style="color: #a0aec0;">—</span>'
        else:
            html += f'<span class="spec-text">{format_spec_value(value)}</span>'
            
        html += '</td></tr>'

    html += '</table>'
    return html


def render_dict_to_html(d):
    """Рендерит вложенный словарь"""
    if not d:
        return "<span style='color: #a0aec0;'>Не указано</span>"
    
    html = '<table class="spec-nested-table">'
    for k, v in d.items():
        nice_key = k.replace('_', ' ').title()
        
        if isinstance(v, bool):
            html += f'<tr><td class="nested-key">{nice_key}:</td><td>{"✅ Да" if v else "❌ Нет"}</td></tr>'
        elif isinstance(v, (int, float)):
            html += f'<tr><td class="nested-key">{nice_key}:</td><td>{v}</td></tr>'
        elif isinstance(v, str):
            if v:
                # Особое форматирование для IP-адресов
                if k in ['ip_адрес', 'ip_address', 'mac_адрес', 'mac_address']:
                    html += f'<tr><td class="nested-key">{nice_key}:</td><td><span style="font-family: monospace; font-weight: 600; color: #667eea;">{v}</span></td></tr>'
                else:
                    html += f'<tr><td class="nested-key">{nice_key}:</td><td>{v}</td></tr>'
            else:
                html += f'<tr><td class="nested-key">{nice_key}:</td><td style="color: #a0aec0;">—</td></tr>'
        else:
            html += f'<tr><td class="nested-key">{nice_key}:</td><td>{v}</td></tr>'
    html += '</table>'
    return html


def render_list_to_html(lst):
    """Рендерит список (например, плашки RAM)"""
    if not lst:
        return "<span style='color: #a0aec0;'>Не указано</span>"
    
    html = '<ul class="spec-list">'
    for item in lst:
        if isinstance(item, dict):
            summary = ", ".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in item.items() if v])
            html += f'<li>{summary}</li>'
        else:
            html += f'<li>{format_spec_value(item)}</li>'
    html += '</ul>'
    return html
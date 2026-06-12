# inventory/forms.py
from django import forms
from .models import Device, DeviceType, Manufacturer, DeviceStatus

class DeviceAddForm(forms.ModelForm):
    # Основные поля
    inventory_number = forms.CharField(
        max_length=50, 
        label="Инвентарный номер",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '1013400000XXX'})
    )
    name = forms.CharField(
        max_length=255, 
        label="Наименование",
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'ПК Dell OptiPlex 3050'})
    )
    device_type = forms.ModelChoiceField(
        queryset=DeviceType.objects.all(),
        label="Тип устройства",
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'device-type-select'})
    )
    manufacturer = forms.ModelChoiceField(
        queryset=Manufacturer.objects.all(),
        label="Производитель",
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    status = forms.ModelChoiceField(
        queryset=DeviceStatus.objects.all(),
        label="Статус",
        initial=1,  # По умолчанию "В эксплуатации"
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    
    # Скрытые поля для JSON-данных
    characteristics_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    settings_data = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = Device
        fields = ['inventory_number', 'name', 'device_type', 'manufacturer', 'status']

    def clean_inventory_number(self):
        """Проверка уникальности инвентарного номера"""
        inv_number = self.cleaned_data.get('inventory_number')
        if Device.objects.filter(inventory_number=inv_number).exists():
            raise forms.ValidationError(f"Устройство с инвентарным номером {inv_number} уже существует")
        return inv_number
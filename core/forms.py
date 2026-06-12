from django import forms
from django.contrib.auth import get_user_model
from inventory.models import Position, Employee  # Импортируем из инвентаря

User = get_user_model()

class EmployeeRegistrationForm(forms.ModelForm):
    # Поля для создания Django User
    username = forms.CharField(
        max_length=150, 
        label="Логин", 
        widget=forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'логин'})
    )
    password = forms.CharField(
        label="Пароль", 
        widget=forms.PasswordInput(attrs={'class': 'input-field', 'placeholder': '******'}),
        help_text="Минимум 8 символов"
    )
    first_name = forms.CharField(max_length=150, label="Имя",  widget=forms.TextInput(attrs={'class': 'input-field'}))
    last_name = forms.CharField(max_length=150, label="Фамилия", widget=forms.TextInput(attrs={'class': 'input-field'}))
    email = forms.EmailField(required=False, label="Email", widget=forms.TextInput(attrs={'class': 'input-field'}))
    
    # Поля для создания профиля Employee
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(), 
        label="Должность",
        empty_label="Выберите должность",
        
    )

    class Meta:
        model = Employee
        fields = ['phone', 'department', 'is_mol', 'position']
        labels = {
            'phone': 'Телефон',
            'department': 'Отдел',
            'is_mol': 'Материально-ответственное лицо (МОЛ)'
        }
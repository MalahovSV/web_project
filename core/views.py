from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from .forms import EmployeeRegistrationForm
from inventory.models import Employee
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout

# 🔐 Страница входа (используем встроенный View с нашим шаблоном)
class CustomLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True  # Если уже вошёл — сразу на дашборд
    
    def get_success_url(self):
        messages.success(self.request, f"Добро пожаловать, {self.request.user.get_full_name() or self.request.user.username}!")
        return super().get_success_url()

# 🚪 ИСПРАВЛЕННЫЙ ВЫХОД ИЗ СИСТЕМЫ
def custom_logout(request):
    """Корректный выход: завершаем сессию и перенаправляем"""
    logout(request)  # Django корректно завершает сессию
    messages.info(request, "Вы успешно вышли из системы.")
    return redirect('login')  # Явное перенаправление на login

User = get_user_model()

def check_admin(user):
    return user.is_staff

@login_required
@user_passes_test(check_admin)
def register_employee(request):
    if request.method == 'POST':
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Создаем пользователя Django
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        password=form.cleaned_data['password'],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        email=form.cleaned_data['email'],
                        #is_staff=True  # Даем доступ в админку/Поиграли в админов и хватит
                    )
                    
                    # 2. Создаем профиль сотрудника и связываем
                    employee = form.save(commit=False)
                    employee.user = user
                    employee.save()
                
                messages.success(request, f"✅ Сотрудник {user.get_full_name()} успешно создан!")
                return redirect('dashboard')
            except Exception as e:
                messages.error(request, f"❌ Ошибка при создании: {e}")
    else:
        form = EmployeeRegistrationForm()
        
    return render(request, 'core/register.html', {'form': form})
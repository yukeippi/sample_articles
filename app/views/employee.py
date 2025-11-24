from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView

from app.forms import EmployeeForm
from app.models import Employee


class EmployeeListView(View):
    """社員一覧ビュー"""

    def get(self, request):
        employees = Employee.objects.select_related('organization').all()

        context = {
            'employees': employees,
        }
        return render(request, 'employees/list.html', context)


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """社員作成ビュー"""

    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/form.html'
    success_url = reverse_lazy('app:employee_list')


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    """社員編集ビュー"""

    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/form.html'
    success_url = reverse_lazy('app:employee_list')


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    """社員削除ビュー"""

    model = Employee
    template_name = 'employees/confirm_delete.html'
    success_url = reverse_lazy('app:employee_list')

from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView

from app.forms import EmployeeForm, EmployeeReservationForm
from app.models import Employee, StagedChange
from app.utils.employee_reservation import EmployeeReservationHelper


class EmployeeListView(View):
    """社員一覧ビュー"""

    def get(self, request):
        employees = Employee.objects.select_related('department').all()

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


class EmployeeReservationListView(LoginRequiredMixin, View):
    """社員予約更新一覧ビュー"""

    def get(self, request):
        # 全ステータスの予約を取得(pending以外も表示)
        content_type = EmployeeReservationHelper.get_content_type()
        reservations = StagedChange.objects.filter(content_type=content_type).order_by(
            '-scheduled_date', '-created_at'
        )

        # 各予約に表示用の情報を追加
        reservations_with_info = []
        for reservation in reservations:
            formatted = EmployeeReservationHelper.format_for_display(reservation)
            # Reservationオブジェクトに表示用の情報を追加
            reservation.display_employee = formatted['employee']
            reservation.display_name = formatted['name']
            reservation.display_email = formatted['email']
            reservation.display_department = formatted['department']
            reservation.display_action = formatted['action_display']
            reservations_with_info.append(reservation)

        context = {
            'reservations': reservations_with_info,
        }
        return render(request, 'employees/reservations/list.html', context)


class EmployeeReservationCreateView(LoginRequiredMixin, View):
    """社員予約更新作成ビュー"""

    def get(self, request):
        form = EmployeeReservationForm()
        return render(request, 'employees/reservations/form.html', {'form': form})

    def post(self, request):
        form = EmployeeReservationForm(request.POST)
        if form.is_valid():
            # フォームデータから予約更新を作成
            EmployeeReservationHelper.create_reservation(
                action=form.cleaned_data['action'],
                scheduled_date=form.cleaned_data['scheduled_date'],
                employee=form.cleaned_data.get('employee'),
                name=form.cleaned_data.get('name'),
                email=form.cleaned_data.get('email'),
                department=form.cleaned_data.get('department'),
            )
            return redirect('app:employee_reservation_list')
        return render(request, 'employees/reservations/form.html', {'form': form})


class EmployeeReservationUpdateView(LoginRequiredMixin, View):
    """社員予約更新編集ビュー"""

    def get(self, request, pk):
        reservation = StagedChange.objects.get(pk=pk, status=StagedChange.PENDING)
        formatted = EmployeeReservationHelper.format_for_display(reservation)

        # フォームの初期値を設定
        form = EmployeeReservationForm(
            initial={
                'employee': formatted['employee'],
                'action': formatted['action'],
                'name': formatted['name'],
                'email': formatted['email'],
                'department': formatted['department'],
                'scheduled_date': formatted['scheduled_date'],
            }
        )
        return render(
            request,
            'employees/reservations/form.html',
            {
                'form': form,
                'object': reservation,
            },
        )

    def post(self, request, pk):
        reservation = StagedChange.objects.get(pk=pk, status=StagedChange.PENDING)
        form = EmployeeReservationForm(request.POST)
        if form.is_valid():
            # 予約更新を更新
            reservation.action = form.cleaned_data['action']
            reservation.object_id = (
                form.cleaned_data.get('employee').id if form.cleaned_data.get('employee') else None
            )
            reservation.scheduled_date = form.cleaned_data['scheduled_date']

            data = {}
            if form.cleaned_data.get('name'):
                data['name'] = form.cleaned_data['name']
            if form.cleaned_data.get('email'):
                data['email'] = form.cleaned_data['email']
            if form.cleaned_data.get('department'):
                data['department_id'] = str(form.cleaned_data['department'].id)
            elif 'department' in form.cleaned_data and form.cleaned_data['department'] is None:
                data['department_id'] = None
            reservation.data = data
            reservation.save()

            return redirect('app:employee_reservation_list')
        return render(
            request,
            'employees/reservations/form.html',
            {
                'form': form,
                'object': reservation,
            },
        )


class EmployeeReservationDeleteView(LoginRequiredMixin, DeleteView):
    """社員予約更新削除（キャンセル）ビュー"""

    model = StagedChange
    template_name = 'employees/reservations/confirm_delete.html'
    success_url = reverse_lazy('app:employee_reservation_list')

    def get_queryset(self):
        # 予約中のレコードのみ削除可能
        content_type = EmployeeReservationHelper.get_content_type()
        return StagedChange.objects.filter(content_type=content_type, status=StagedChange.PENDING)

    def form_valid(self, form):
        # 物理削除ではなくステータス変更
        self.object.status = StagedChange.CANCELLED
        self.object.save()
        return redirect(self.success_url)


class EmployeePreviewView(LoginRequiredMixin, View):
    """社員プレビュービュー（予約更新を含めた一覧表示）"""

    def get(self, request):
        preview_date_str = request.GET.get('date')
        preview_date = (
            date.fromisoformat(preview_date_str) if preview_date_str else timezone.now().date()
        )

        # 現在の社員データを取得
        employees = Employee.objects.select_related('department').all()

        # メモリ上で社員データを配列化
        employee_dict = {}
        for emp in employees:
            employee_dict[str(emp.id)] = {
                'id': str(emp.id),
                'name': emp.name,
                'email': emp.email,
                'department_id': str(emp.department.id) if emp.department else None,
                'department_name': emp.department.name if emp.department else None,
            }

        # プレビュー日付までの予約更新を適用（メモリ上のみ）
        reservations = EmployeeReservationHelper.get_pending_reservations(
            scheduled_date=preview_date
        )

        for reservation in reservations:
            formatted = EmployeeReservationHelper.format_for_display(reservation)

            if reservation.action == StagedChange.ACTION_CREATE:
                # 新規作成
                new_id = str(reservation.id)  # 仮のID
                employee_dict[new_id] = {
                    'id': new_id,
                    'name': formatted['name'],
                    'email': formatted['email'],
                    'department_id': str(formatted['department'].id)
                    if formatted['department']
                    else None,
                    'department_name': formatted['department'].name
                    if formatted['department']
                    else None,
                    'is_preview': True,  # プレビューフラグ
                }
            elif reservation.action == StagedChange.ACTION_UPDATE:
                # 更新
                emp_id = str(reservation.object_id)
                if emp_id in employee_dict:
                    if formatted['name']:
                        employee_dict[emp_id]['name'] = formatted['name']
                    if formatted['email']:
                        employee_dict[emp_id]['email'] = formatted['email']
                    if formatted['department']:
                        employee_dict[emp_id]['department_id'] = str(formatted['department'].id)
                        employee_dict[emp_id]['department_name'] = formatted['department'].name
                    elif 'department' in reservation.data:
                        employee_dict[emp_id]['department_id'] = None
                        employee_dict[emp_id]['department_name'] = None
            elif reservation.action == StagedChange.ACTION_DELETE:
                # 削除
                emp_id = str(reservation.object_id)
                employee_dict.pop(emp_id, None)

        # リスト化
        employee_list = list(employee_dict.values())

        context = {
            'preview_date': preview_date,
            'employees': employee_list,
            'employees_count': len(employee_list),
        }
        return render(request, 'employees/preview.html', context)

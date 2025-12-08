from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DeleteView

from app.forms import DepartmentReservationForm
from app.models import Department, Reservation, UpdateStatus
from app.utils.department_reservation import DepartmentReservationHelper
from app.utils.tree import build_tree, get_tree_html


class DepartmentReservationListView(LoginRequiredMixin, View):
    """予約更新一覧ビュー"""

    def get(self, request):
        # 全ステータスの予約を取得(pending以外も表示)
        content_type = DepartmentReservationHelper.get_content_type()
        reservations = Reservation.objects.filter(
            content_type=content_type
        ).select_related('status', 'depends_on').order_by('-scheduled_date', '-created_at')

        # 各予約に表示用の情報を追加
        reservations_with_info = []
        for reservation in reservations:
            formatted = DepartmentReservationHelper.format_for_display(reservation)
            # Reservationオブジェクトに表示用の情報を追加
            reservation.display_department = formatted['department']
            reservation.display_name = formatted['name']
            reservation.display_parent = formatted['parent']
            reservation.display_target_department = formatted.get('target_department')
            reservation.display_action = formatted['action_display']
            reservations_with_info.append(reservation)

        context = {
            'reservations': reservations_with_info,
        }
        return render(request, 'reservations/list.html', context)


class DepartmentReservationCreateView(LoginRequiredMixin, View):
    """予約更新作成ビュー"""

    def get(self, request):
        form = DepartmentReservationForm()
        return render(request, 'reservations/form.html', {'form': form})

    def post(self, request):
        form = DepartmentReservationForm(request.POST)
        if form.is_valid():
            # フォームデータから予約更新を作成
            DepartmentReservationHelper.create_reservation(
                action=form.cleaned_data['action'],
                scheduled_date=form.cleaned_data['scheduled_date'],
                department=form.cleaned_data.get('department'),
                name=form.cleaned_data.get('name'),
                parent=form.cleaned_data.get('parent'),
                parent_reservation=form.cleaned_data.get('parent_reservation'),
                target_department=form.cleaned_data.get('target_department'),
            )
            return redirect('app:department_reservation_list')
        return render(request, 'reservations/form.html', {'form': form})


class DepartmentReservationUpdateView(LoginRequiredMixin, View):
    """予約更新編集ビュー"""

    def get(self, request, pk):
        reservation = Reservation.objects.get(pk=pk, status_id=UpdateStatus.PENDING)
        formatted = DepartmentReservationHelper.format_for_display(reservation)

        # フォームの初期値を設定
        form = DepartmentReservationForm(initial={
            'department': formatted['department'],
            'action': formatted['action'],
            'name': formatted['name'],
            'parent': formatted['parent'],
            'parent_reservation': formatted.get('depends_on'),
            'target_department': formatted.get('target_department'),
            'scheduled_date': formatted['scheduled_date'],
        })
        return render(request, 'reservations/form.html', {
            'form': form,
            'object': reservation,
        })

    def post(self, request, pk):
        reservation = Reservation.objects.get(pk=pk, status_id=UpdateStatus.PENDING)
        form = DepartmentReservationForm(request.POST)
        if form.is_valid():
            # 予約更新を更新
            reservation.action = form.cleaned_data['action']
            reservation.object_id = form.cleaned_data.get('department').id if form.cleaned_data.get('department') else None
            reservation.scheduled_date = form.cleaned_data['scheduled_date']
            reservation.depends_on = form.cleaned_data.get('parent_reservation')

            data = {}
            if form.cleaned_data.get('name'):
                data['name'] = form.cleaned_data['name']
            if form.cleaned_data.get('parent'):
                data['parent_id'] = str(form.cleaned_data['parent'].id)
            elif 'parent' in form.cleaned_data and form.cleaned_data['parent'] is None:
                data['parent_id'] = None
            if form.cleaned_data.get('target_department'):
                data['target_department_id'] = str(form.cleaned_data['target_department'].id)
            reservation.data = data
            reservation.save()

            return redirect('app:department_reservation_list')
        return render(request, 'reservations/form.html', {
            'form': form,
            'object': reservation,
        })


class DepartmentReservationDeleteView(LoginRequiredMixin, DeleteView):
    """予約更新削除（キャンセル）ビュー"""

    model = Reservation
    template_name = 'reservations/confirm_delete.html'
    success_url = reverse_lazy('app:department_reservation_list')

    def get_queryset(self):
        # 予約中のレコードのみ削除可能
        content_type = DepartmentReservationHelper.get_content_type()
        return Reservation.objects.filter(
            content_type=content_type,
            status_id=UpdateStatus.PENDING
        )

    def form_valid(self, form):
        # 物理削除ではなくステータス変更
        self.object.status_id = UpdateStatus.CANCELLED
        self.object.save()
        return redirect(self.success_url)


class DepartmentPreviewView(LoginRequiredMixin, View):
    """組織プレビュービュー（予約更新を含めたツリー表示）"""

    def get(self, request):
        preview_date_str = request.GET.get('date')
        preview_date = date.fromisoformat(preview_date_str) if preview_date_str else date.today()

        # 現在の組織データを取得
        departments = Department.objects.select_related('parent').all()

        # メモリ上で組織データを配列化
        dept_dict = {}
        for dept in departments:
            dept_dict[str(dept.id)] = {
                'id': str(dept.id),
                'name': dept.name,
                'parent': str(dept.parent.id) if dept.parent else None,
            }

        # プレビュー日付までの予約更新を適用（メモリ上のみ）
        reservations = DepartmentReservationHelper.get_pending_reservations(
            scheduled_date=preview_date
        )

        for reservation in reservations:
            formatted = DepartmentReservationHelper.format_for_display(reservation)

            if reservation.action == Reservation.ACTION_CREATE:
                # 新規作成
                new_id = str(reservation.id)  # 仮のID
                parent_id = None

                # 既存の親組織がある場合
                if formatted['parent']:
                    parent_id = str(formatted['parent'].id)
                # depends_onで未来の組織を親として指定している場合
                elif reservation.depends_on:
                    parent_id = str(reservation.depends_on.id)

                dept_dict[new_id] = {
                    'id': new_id,
                    'name': formatted['name'],
                    'parent': parent_id,
                }
            elif reservation.action == Reservation.ACTION_UPDATE:
                # 更新
                dept_id = str(reservation.object_id)
                if dept_id in dept_dict:
                    if formatted['name']:
                        dept_dict[dept_id]['name'] = formatted['name']
                    if formatted['parent'] is not None:
                        dept_dict[dept_id]['parent'] = str(formatted['parent'].id)
                    elif reservation.depends_on:
                        dept_dict[dept_id]['parent'] = str(reservation.depends_on.id)
            elif reservation.action == Reservation.ACTION_DELETE:
                # 削除
                dept_id = str(reservation.object_id)
                if dept_id in dept_dict:
                    del dept_dict[dept_id]

        # ツリー構築
        dept_list = list(dept_dict.values())
        tree = build_tree(dept_list)
        tree_html = get_tree_html(tree)

        context = {
            'preview_date': preview_date,
            'tree_html': tree_html,
            'departments_count': len(dept_list),
        }
        return render(request, 'departments/preview.html', context)

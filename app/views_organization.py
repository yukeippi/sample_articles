from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView

from app.forms import OrganizationForm, OrganizationReservationForm
from app.models import Organization, OrganizationReservation, UpdateStatus
from app.utils.tree import build_tree, get_tree_html


class OrganizationListView(View):
    """組織一覧ビュー"""

    def get(self, request):
        organizations = Organization.objects.select_related('parent').all()

        # ツリー構造用のデータを準備
        org_list = [
            {
                'id': str(org.id),
                'name': org.name,
                'parent': str(org.parent.id) if org.parent else None,
            }
            for org in organizations
        ]

        tree = build_tree(org_list)
        tree_html = get_tree_html(tree)

        context = {
            'organizations': organizations,
            'tree_html': tree_html,
        }
        return render(request, 'organizations/organization_list.html', context)


class OrganizationCreateView(LoginRequiredMixin, CreateView):
    """組織作成ビュー"""

    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    success_url = reverse_lazy('app:organization_list')


class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    """組織編集ビュー"""

    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    success_url = reverse_lazy('app:organization_list')


class OrganizationDeleteView(LoginRequiredMixin, DeleteView):
    """組織削除ビュー"""

    model = Organization
    template_name = 'organizations/organization_confirm_delete.html'
    success_url = reverse_lazy('app:organization_list')


class OrganizationReservationListView(LoginRequiredMixin, View):
    """予約更新一覧ビュー"""

    def get(self, request):
        reservations = OrganizationReservation.objects.select_related(
            'organization', 'parent', 'status'
        ).all()

        context = {
            'reservations': reservations,
        }
        return render(request, 'organizations/reservation_list.html', context)


class OrganizationReservationCreateView(LoginRequiredMixin, CreateView):
    """予約更新作成ビュー"""

    model = OrganizationReservation
    form_class = OrganizationReservationForm
    template_name = 'organizations/reservation_form.html'
    success_url = reverse_lazy('app:organization_reservation_list')

    def form_valid(self, form):
        # デフォルトのステータスを設定
        form.instance.status_id = UpdateStatus.PENDING
        return super().form_valid(form)


class OrganizationReservationUpdateView(LoginRequiredMixin, UpdateView):
    """予約更新編集ビュー"""

    model = OrganizationReservation
    form_class = OrganizationReservationForm
    template_name = 'organizations/reservation_form.html'
    success_url = reverse_lazy('app:organization_reservation_list')

    def get_queryset(self):
        # 予約中のレコードのみ編集可能
        return OrganizationReservation.objects.filter(status_id=UpdateStatus.PENDING)


class OrganizationReservationDeleteView(LoginRequiredMixin, DeleteView):
    """予約更新削除（キャンセル）ビュー"""

    model = OrganizationReservation
    template_name = 'organizations/reservation_confirm_delete.html'
    success_url = reverse_lazy('app:organization_reservation_list')

    def get_queryset(self):
        # 予約中のレコードのみ削除可能
        return OrganizationReservation.objects.filter(status_id=UpdateStatus.PENDING)

    def form_valid(self, form):
        # 物理削除ではなくステータス変更
        self.object.status_id = UpdateStatus.CANCELLED
        self.object.save()
        return redirect(self.success_url)


class OrganizationPreviewView(LoginRequiredMixin, View):
    """組織プレビュービュー（予約更新を含めたツリー表示）"""

    def get(self, request):
        preview_date_str = request.GET.get('date')
        preview_date = date.fromisoformat(preview_date_str) if preview_date_str else date.today()

        # 現在の組織データを取得
        organizations = Organization.objects.select_related('parent').all()

        # メモリ上で組織データを配列化
        org_dict = {}
        for org in organizations:
            org_dict[str(org.id)] = {
                'id': str(org.id),
                'name': org.name,
                'parent': str(org.parent.id) if org.parent else None,
            }

        # プレビュー日付までの予約更新を適用（メモリ上のみ）
        reservations = OrganizationReservation.objects.filter(
            scheduled_date__lte=preview_date, status_id=UpdateStatus.PENDING
        ).select_related('organization', 'parent').order_by('scheduled_date', 'created_at')

        for reservation in reservations:
            if reservation.action == OrganizationReservation.ACTION_CREATE:
                # 新規作成
                new_id = str(reservation.id)  # 仮のID
                org_dict[new_id] = {
                    'id': new_id,
                    'name': reservation.name,
                    'parent': str(reservation.parent.id) if reservation.parent else None,
                }
            elif reservation.action == OrganizationReservation.ACTION_UPDATE:
                # 更新
                org_id = str(reservation.organization.id)
                if org_id in org_dict:
                    if reservation.name:
                        org_dict[org_id]['name'] = reservation.name
                    if reservation.parent is not None:
                        org_dict[org_id]['parent'] = str(reservation.parent.id)
            elif reservation.action == OrganizationReservation.ACTION_DELETE:
                # 削除
                org_id = str(reservation.organization.id)
                if org_id in org_dict:
                    del org_dict[org_id]

        # ツリー構築
        org_list = list(org_dict.values())
        tree = build_tree(org_list)
        tree_html = get_tree_html(tree)

        context = {
            'preview_date': preview_date,
            'tree_html': tree_html,
            'organizations_count': len(org_list),
        }
        return render(request, 'organizations/organization_preview.html', context)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView

from app.forms import OrganizationForm
from app.models import Organization
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
        return render(request, 'organizations/list.html', context)


class OrganizationCreateView(LoginRequiredMixin, CreateView):
    """組織作成ビュー"""

    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/form.html'
    success_url = reverse_lazy('app:organization_list')


class OrganizationUpdateView(LoginRequiredMixin, UpdateView):
    """組織編集ビュー"""

    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/form.html'
    success_url = reverse_lazy('app:organization_list')


class OrganizationDeleteView(LoginRequiredMixin, DeleteView):
    """組織削除ビュー"""

    model = Organization
    template_name = 'organizations/confirm_delete.html'
    success_url = reverse_lazy('app:organization_list')

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView

from app.forms import OrganizationForm, OrganizationMergeForm
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


class OrganizationMergeView(LoginRequiredMixin, View):
    """組織統合ビュー"""

    def get(self, request):
        form = OrganizationMergeForm()
        return render(request, 'organizations/merge.html', {'form': form})

    def post(self, request):
        form = OrganizationMergeForm(request.POST)
        if form.is_valid():
            source = form.cleaned_data['source_organization']
            target = form.cleaned_data['target_organization']

            try:
                # 統合実行
                source.merge_into(target)
                messages.success(
                    request,
                    f'組織「{source.name}」を「{target.name}」に統合しました。'
                )
                return redirect('app:organization_list')
            except ValueError as e:
                messages.error(request, f'統合に失敗しました: {str(e)}')
                return render(request, 'organizations/merge.html', {'form': form})

        return render(request, 'organizations/merge.html', {'form': form})

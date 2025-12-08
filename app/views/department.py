from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, UpdateView

from app.forms import DepartmentForm, DepartmentMergeForm
from app.models import Department
from app.utils.tree import build_tree, get_tree_html


class DepartmentListView(View):
    """組織一覧ビュー"""

    def get(self, request):
        departments = Department.objects.select_related('parent').all()

        # ツリー構造用のデータを準備
        dept_list = [
            {
                'id': str(dept.id),
                'name': dept.name,
                'parent': str(dept.parent.id) if dept.parent else None,
            }
            for dept in departments
        ]

        tree = build_tree(dept_list)
        tree_html = get_tree_html(tree)

        context = {
            'departments': departments,
            'tree_html': tree_html,
        }
        return render(request, 'departments/list.html', context)


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """組織作成ビュー"""

    model = Department
    form_class = DepartmentForm
    template_name = 'departments/form.html'
    success_url = reverse_lazy('app:department_list')


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """組織編集ビュー"""

    model = Department
    form_class = DepartmentForm
    template_name = 'departments/form.html'
    success_url = reverse_lazy('app:department_list')


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    """組織削除ビュー"""

    model = Department
    template_name = 'departments/confirm_delete.html'
    success_url = reverse_lazy('app:department_list')


class DepartmentMergeView(LoginRequiredMixin, View):
    """組織統合ビュー"""

    def get(self, request):
        form = DepartmentMergeForm()
        return render(request, 'departments/merge.html', {'form': form})

    def post(self, request):
        form = DepartmentMergeForm(request.POST)
        if form.is_valid():
            source = form.cleaned_data['source_department']
            target = form.cleaned_data['target_department']

            try:
                # 統合実行
                source.merge_into(target)
                messages.success(
                    request,
                    f'組織「{source.name}」を「{target.name}」に統合しました。'
                )
                return redirect('app:department_list')
            except ValueError as e:
                messages.error(request, f'統合に失敗しました: {str(e)}')
                return render(request, 'departments/merge.html', {'form': form})

        return render(request, 'departments/merge.html', {'form': form})

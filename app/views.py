from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, UpdateView, View

from app.forms import ArticleForm
from app.models import Article


class IndexView(View):
    def get(self, request):
        articles = Article.objects.select_related('user').all()
        context = {
            'articles': articles,
        }
        return render(request, 'index.html', context)


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('app:index')
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                next_url = request.GET.get('next', 'app:index')
                return redirect(next_url)
        return render(request, 'login.html', {'form': form})


class LogoutView(View):
    def post(self, request):
        auth_logout(request)
        return redirect('app:index')


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = 'article_create.html'

    def form_valid(self, form):
        # ログインユーザーを投稿者として設定
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:article_detail', kwargs={'pk': self.object.pk})


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.select_related('user').prefetch_related('comments__user')


class ArticleUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'article_edit.html'
    context_object_name = 'article'

    def test_func(self):
        # 記事の所有者のみ編集可能
        article = self.get_object()
        return article.user == self.request.user

    def get_success_url(self):
        return reverse_lazy('app:article_detail', kwargs={'pk': self.object.pk})


class ArticleDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Article
    template_name = 'article_delete.html'
    context_object_name = 'article'
    success_url = reverse_lazy('app:index')

    def test_func(self):
        # 記事の所有者のみ削除可能
        article = self.get_object()
        return article.user == self.request.user

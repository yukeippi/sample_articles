from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, UpdateView, View

from app.forms import ArticleForm
from app.models import Article


class IndexView(View):
    def get(self, request):
        articles = Article.objects.select_related('user').all()
        context = {
            'articles': articles,
        }
        return render(request, 'index.html', context)


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return Article.objects.select_related('user').prefetch_related('comments__user')


class ArticleUpdateView(UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'article_edit.html'
    context_object_name = 'article'

    def get_success_url(self):
        return reverse_lazy('app:article_detail', kwargs={'pk': self.object.pk})


class ArticleDeleteView(DeleteView):
    model = Article
    template_name = 'article_delete.html'
    context_object_name = 'article'
    success_url = reverse_lazy('app:index')

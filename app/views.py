from django.shortcuts import render
from django.views.generic import View

from app.models import Article


class IndexView(View):
    def get(self, request):
        articles = Article.objects.select_related('user').all()
        context = {
            'articles': articles,
        }
        return render(request, 'index.html', context)

from django.urls import path

from . import views

app_name = 'app'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('article/<uuid:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
]

from django.urls import path

from . import views

app_name = 'app'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('article/new/', views.ArticleCreateView.as_view(), name='article_create'),
    path('article/<uuid:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('article/<uuid:pk>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),
    path('article/<uuid:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),
]

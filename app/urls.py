from django.urls import path

from . import views, views_organization

app_name = 'app'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('article/new/', views.ArticleCreateView.as_view(), name='article_create'),
    path('article/<uuid:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('article/<uuid:pk>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),
    path('article/<uuid:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),
    # 組織関連
    path(
        'organizations/',
        views_organization.OrganizationListView.as_view(),
        name='organization_list',
    ),
    path(
        'organizations/new/',
        views_organization.OrganizationCreateView.as_view(),
        name='organization_create',
    ),
    path(
        'organizations/<uuid:pk>/edit/',
        views_organization.OrganizationUpdateView.as_view(),
        name='organization_update',
    ),
    path(
        'organizations/<uuid:pk>/delete/',
        views_organization.OrganizationDeleteView.as_view(),
        name='organization_delete',
    ),
    path(
        'organizations/preview/',
        views_organization.OrganizationPreviewView.as_view(),
        name='organization_preview',
    ),
    # 予約更新関連
    path(
        'organizations/reservations/',
        views_organization.OrganizationReservationListView.as_view(),
        name='organization_reservation_list',
    ),
    path(
        'organizations/reservations/new/',
        views_organization.OrganizationReservationCreateView.as_view(),
        name='organization_reservation_create',
    ),
    path(
        'organizations/reservations/<uuid:pk>/edit/',
        views_organization.OrganizationReservationUpdateView.as_view(),
        name='organization_reservation_update',
    ),
    path(
        'organizations/reservations/<uuid:pk>/delete/',
        views_organization.OrganizationReservationDeleteView.as_view(),
        name='organization_reservation_delete',
    ),
]

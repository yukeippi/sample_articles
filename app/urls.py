from django.urls import path

from app import views

app_name = 'app'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('article/new/', views.ArticleCreateView.as_view(), name='article_create'),
    path('article/<uuid:pk>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('article/<uuid:pk>/edit/', views.ArticleUpdateView.as_view(), name='article_edit'),
    path('article/<uuid:pk>/delete/', views.ArticleDeleteView.as_view(), name='article_delete'),
    # 社員関連
    path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
    path('employees/new/', views.EmployeeCreateView.as_view(), name='employee_create'),
    path(
        'employees/<uuid:pk>/edit/',
        views.EmployeeUpdateView.as_view(),
        name='employee_update',
    ),
    path(
        'employees/<uuid:pk>/delete/',
        views.EmployeeDeleteView.as_view(),
        name='employee_delete',
    ),
    # 組織関連
    path(
        'organizations/',
        views.OrganizationListView.as_view(),
        name='organization_list',
    ),
    path(
        'organizations/new/',
        views.OrganizationCreateView.as_view(),
        name='organization_create',
    ),
    path(
        'organizations/<uuid:pk>/edit/',
        views.OrganizationUpdateView.as_view(),
        name='organization_update',
    ),
    path(
        'organizations/<uuid:pk>/delete/',
        views.OrganizationDeleteView.as_view(),
        name='organization_delete',
    ),
    path(
        'organizations/preview/',
        views.OrganizationPreviewView.as_view(),
        name='organization_preview',
    ),
    # 予約更新関連
    path(
        'organizations/reservations/',
        views.OrganizationReservationListView.as_view(),
        name='organization_reservation_list',
    ),
    path(
        'organizations/reservations/new/',
        views.OrganizationReservationCreateView.as_view(),
        name='organization_reservation_create',
    ),
    path(
        'organizations/reservations/<uuid:pk>/edit/',
        views.OrganizationReservationUpdateView.as_view(),
        name='organization_reservation_update',
    ),
    path(
        'organizations/reservations/<uuid:pk>/delete/',
        views.OrganizationReservationDeleteView.as_view(),
        name='organization_reservation_delete',
    ),
]

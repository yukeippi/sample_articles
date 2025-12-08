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
    # 社員予約更新関連
    path(
        'employees/reservations/',
        views.EmployeeReservationListView.as_view(),
        name='employee_reservation_list',
    ),
    path(
        'employees/reservations/new/',
        views.EmployeeReservationCreateView.as_view(),
        name='employee_reservation_create',
    ),
    path(
        'employees/reservations/<uuid:pk>/edit/',
        views.EmployeeReservationUpdateView.as_view(),
        name='employee_reservation_update',
    ),
    path(
        'employees/reservations/<uuid:pk>/delete/',
        views.EmployeeReservationDeleteView.as_view(),
        name='employee_reservation_delete',
    ),
    path(
        'employees/preview/',
        views.EmployeePreviewView.as_view(),
        name='employee_preview',
    ),
    # 組織関連
    path(
        'departments/',
        views.DepartmentListView.as_view(),
        name='department_list',
    ),
    path(
        'departments/new/',
        views.DepartmentCreateView.as_view(),
        name='department_create',
    ),
    path(
        'departments/<uuid:pk>/edit/',
        views.DepartmentUpdateView.as_view(),
        name='department_update',
    ),
    path(
        'departments/<uuid:pk>/delete/',
        views.DepartmentDeleteView.as_view(),
        name='department_delete',
    ),
    path(
        'departments/merge/',
        views.DepartmentMergeView.as_view(),
        name='department_merge',
    ),
    path(
        'departments/preview/',
        views.DepartmentPreviewView.as_view(),
        name='department_preview',
    ),
    # 予約更新関連
    path(
        'departments/reservations/',
        views.DepartmentReservationListView.as_view(),
        name='department_reservation_list',
    ),
    path(
        'departments/reservations/new/',
        views.DepartmentReservationCreateView.as_view(),
        name='department_reservation_create',
    ),
    path(
        'departments/reservations/<uuid:pk>/edit/',
        views.DepartmentReservationUpdateView.as_view(),
        name='department_reservation_update',
    ),
    path(
        'departments/reservations/<uuid:pk>/delete/',
        views.DepartmentReservationDeleteView.as_view(),
        name='department_reservation_delete',
    ),
]

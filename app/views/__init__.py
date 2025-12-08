from app.views.article import (
    ArticleCreateView,
    ArticleDeleteView,
    ArticleDetailView,
    ArticleUpdateView,
    IndexView,
    LoginView,
    LogoutView,
)
from app.views.employee import (
    EmployeeCreateView,
    EmployeeDeleteView,
    EmployeeListView,
    EmployeePreviewView,
    EmployeeReservationCreateView,
    EmployeeReservationDeleteView,
    EmployeeReservationListView,
    EmployeeReservationUpdateView,
    EmployeeUpdateView,
)
from app.views.department import (
    DepartmentCreateView,
    DepartmentDeleteView,
    DepartmentListView,
    DepartmentMergeView,
    DepartmentUpdateView,
)
from app.views.reservation import (
    DepartmentPreviewView,
    DepartmentReservationCreateView,
    DepartmentReservationDeleteView,
    DepartmentReservationListView,
    DepartmentReservationUpdateView,
)

__all__ = [
    # Article views
    'IndexView',
    'LoginView',
    'LogoutView',
    'ArticleCreateView',
    'ArticleDetailView',
    'ArticleUpdateView',
    'ArticleDeleteView',
    # Employee views
    'EmployeeListView',
    'EmployeeCreateView',
    'EmployeeUpdateView',
    'EmployeeDeleteView',
    'EmployeeReservationListView',
    'EmployeeReservationCreateView',
    'EmployeeReservationUpdateView',
    'EmployeeReservationDeleteView',
    'EmployeePreviewView',
    # Department views
    'DepartmentListView',
    'DepartmentCreateView',
    'DepartmentUpdateView',
    'DepartmentDeleteView',
    'DepartmentMergeView',
    # Reservation views
    'DepartmentReservationListView',
    'DepartmentReservationCreateView',
    'DepartmentReservationUpdateView',
    'DepartmentReservationDeleteView',
    'DepartmentPreviewView',
]

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
from app.views.organization import (
    OrganizationCreateView,
    OrganizationDeleteView,
    OrganizationListView,
    OrganizationMergeView,
    OrganizationUpdateView,
)
from app.views.reservation import (
    OrganizationPreviewView,
    OrganizationReservationCreateView,
    OrganizationReservationDeleteView,
    OrganizationReservationListView,
    OrganizationReservationUpdateView,
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
    # Organization views
    'OrganizationListView',
    'OrganizationCreateView',
    'OrganizationUpdateView',
    'OrganizationDeleteView',
    'OrganizationMergeView',
    # Reservation views
    'OrganizationReservationListView',
    'OrganizationReservationCreateView',
    'OrganizationReservationUpdateView',
    'OrganizationReservationDeleteView',
    'OrganizationPreviewView',
]

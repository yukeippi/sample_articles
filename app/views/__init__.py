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
    EmployeeUpdateView,
)
from app.views.organization import (
    OrganizationCreateView,
    OrganizationDeleteView,
    OrganizationListView,
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
    # Organization views
    'OrganizationListView',
    'OrganizationCreateView',
    'OrganizationUpdateView',
    'OrganizationDeleteView',
    # Reservation views
    'OrganizationReservationListView',
    'OrganizationReservationCreateView',
    'OrganizationReservationUpdateView',
    'OrganizationReservationDeleteView',
    'OrganizationPreviewView',
]

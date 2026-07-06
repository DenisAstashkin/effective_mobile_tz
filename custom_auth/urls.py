from django.urls import path
from .views import (
    RegisterView, LoginView, ProfileView, 
    LogoutView, ManageRulesView, MockDocumentView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    
    path('admin/rules/', ManageRulesView.as_view(), name='manage_rules'),
    
    path('documents/', MockDocumentView.as_view(), name='document_list'),
    path('documents/<int:pk>/', MockDocumentView.as_view(), name='document_detail'),
]

from django.urls import path, include

urlpatterns = [
    path('api/', include('custom_auth.urls')),
]

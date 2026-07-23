"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from api.auth_views import RegisterView, MeView, UserListView, UserDetailView, ChangePasswordView, ApproveUserView
from api.google_auth import GoogleLoginView

from api.landing_view import landing_view, health_check_view
from rest_framework.permissions import AllowAny

urlpatterns = [
    path('', landing_view, name='landing'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/health/', health_check_view, name='health_check'),
    # Auth endpoints
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/google/', GoogleLoginView.as_view(), name='google_login'),
    path('api/auth/users/create/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='auth_change_password'),
    path('api/auth/me/', MeView.as_view(), name='auth_me'),
    path('api/auth/users/', UserListView.as_view(), name='auth_users'),
    path('api/auth/users/<int:pk>/', UserDetailView.as_view(), name='auth_user_detail'),
    path('api/auth/users/<int:pk>/approve/', ApproveUserView.as_view(), name='auth_user_approve'),
    # Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[AllowAny]), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[AllowAny]), name='swagger-ui'),
]


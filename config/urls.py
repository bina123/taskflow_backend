"""
URL configuration for TaskFlow AI project.
================================================================================
Laravel equivalent: routes/api.php + routes/web.php
================================================================================

In Django:
- urls.py = routes/web.php (defines URL patterns)
- Each app has its own urls.py (like route groups in Laravel)
- path() = Route::get(), Route::post(), etc.
- include() = Route::prefix()->group()
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Django Admin (like Laravel Nova or Filament)
    path('admin/', admin.site.urls),
    
    # ==========================================================================
    # JWT Authentication endpoints
    # Laravel equivalent: Route::post('/login', [AuthController::class, 'login'])
    # ==========================================================================
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # ==========================================================================
    # App URLs (included from each app's urls.py)
    # Laravel equivalent: Route::prefix('api')->group(base_path('routes/api.php'))
    # ==========================================================================
    path('api/auth/', include('accounts.urls')),
    path('api/', include('projects.urls')),
    path('api/', include('tasks.urls')),
]

# Serve media files in development
# Laravel equivalent: Storage::url() for public files
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

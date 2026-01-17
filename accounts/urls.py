"""
URL configuration for accounts app.
================================================================================
Laravel equivalent: Part of routes/api.php with auth routes
================================================================================

Route::prefix('auth')->group(function () {
    Route::post('/register', [AuthController::class, 'register']);
    Route::get('/me', [AuthController::class, 'me'])->middleware('auth');
    ...
});
"""

from django.urls import path
from .views import RegisterView, ProfileView, ChangePasswordView

# app_name is used for namespacing URLs (like route names in Laravel)
app_name = 'accounts'

urlpatterns = [
    # POST /api/auth/register/
    path('register/', RegisterView.as_view(), name='register'),
    
    # GET, PATCH /api/auth/me/
    path('me/', ProfileView.as_view(), name='profile'),
    
    # POST /api/auth/change-password/
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]

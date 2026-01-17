"""
URL configuration for projects app.
================================================================================
Laravel equivalent: 
Route::apiResource('projects', ProjectController::class);
Route::get('/projects/{project}/members', [ProjectController::class, 'members']);
Route::post('/projects/{project}/invite', [ProjectController::class, 'invite']);
================================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet

# Router automatically creates URLs for ViewSet
# Laravel equivalent: Route::apiResource()
router = DefaultRouter()
router.register('projects', ProjectViewSet, basename='project')

app_name = 'projects'

urlpatterns = [
    path('', include(router.urls)),
]

# This creates the following URLs:
# GET    /api/projects/           -> list
# POST   /api/projects/           -> create
# GET    /api/projects/{id}/      -> retrieve
# PUT    /api/projects/{id}/      -> update
# PATCH  /api/projects/{id}/      -> partial_update
# DELETE /api/projects/{id}/      -> destroy
# GET    /api/projects/{id}/members/  -> members (custom action)
# POST   /api/projects/{id}/invite/   -> invite (custom action)

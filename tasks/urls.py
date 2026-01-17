"""
URL configuration for tasks app.
================================================================================
Laravel equivalent: 
Route::apiResource('tasks', TaskController::class);
Route::post('/tasks/{task}/reorder', [TaskController::class, 'reorder']);
Route::get('/tasks/{task}/comments', [TaskController::class, 'comments']);
Route::post('/tasks/{task}/comments', [TaskController::class, 'addComment']);
================================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet

router = DefaultRouter()
router.register('tasks', TaskViewSet, basename='task')

app_name = 'tasks'

urlpatterns = [
    path('', include(router.urls)),
]

# Generated URLs:
# GET    /api/tasks/                  -> list (with filters)
# POST   /api/tasks/                  -> create
# GET    /api/tasks/{id}/             -> retrieve (with comments)
# PUT    /api/tasks/{id}/             -> update
# PATCH  /api/tasks/{id}/             -> partial_update
# DELETE /api/tasks/{id}/             -> destroy
# POST   /api/tasks/{id}/reorder/     -> reorder (custom)
# GET    /api/tasks/{id}/comments/    -> list comments (custom)
# POST   /api/tasks/{id}/comments/    -> add comment (custom)

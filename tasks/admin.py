"""Admin configuration for tasks app."""

from django.contrib import admin
from .models import Task, Comment, Label, Activity


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    raw_id_fields = ['user']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'priority', 'assignee', 'due_date']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['title', 'description']
    raw_id_fields = ['project', 'assignee', 'created_by']
    inlines = [CommentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'user', 'created_at']
    raw_id_fields = ['task', 'user']


@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'color']
    list_filter = ['project']

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['user','action','project', 'description','created_at']
    list_filter = ['action', 'created_at', 'project']
    search_fields = ['description', 'user__email']
    raw_id_fields = ['user', 'project', 'task']
    readonly_fields = ['created_at']
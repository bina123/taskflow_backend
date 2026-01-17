"""Admin configuration for projects app."""

from django.contrib import admin
from .models import Project, ProjectMember


class ProjectMemberInline(admin.TabularInline):
    """Inline for project members in project admin."""
    model = ProjectMember
    extra = 0
    raw_id_fields = ['user']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'owner__email']
    raw_id_fields = ['owner']
    inlines = [ProjectMemberInline]


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['project__name', 'user__email']
    raw_id_fields = ['project', 'user']

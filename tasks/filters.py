"""
Filters for TaskFlow AI
================================================================================
Laravel equivalent: Query scopes + request filters
================================================================================
"""

import django_filters
from django.db.models import Q
from datetime import date
from .models import Task


class TaskFilter(django_filters.FilterSet):
    """
    Filter for tasks.
    
    Usage:
        /api/tasks/?status=todo
        /api/tasks/?priority=high,urgent
        /api/tasks/?assignee=1
        /api/tasks/?assignee=me
        /api/tasks/?unassigned=true
        /api/tasks/?search=auth
        /api/tasks/?due_before=2025-01-20
        /api/tasks/?due_after=2025-01-01
        /api/tasks/?overdue=true
        /api/tasks/?project=1
    
    Laravel equivalent:
        Task::where('status', $request->status)
            ->where('priority', $request->priority)
            ->when($request->search, fn($q) => $q->where('title', 'like', "%{$search}%"))
    """
    
    status = django_filters.ChoiceFilter(choices=Task.Status.choices)
    priority = django_filters.MultipleChoiceFilter(choices=Task.Priority.choices)
    project = django_filters.NumberFilter(field_name='project_id')
    
    
    assignee = django_filters.CharFilter(method='filter_assignee')
    unassigned = django_filters.BooleanFilter(method='filter_unassigned')
    
    due_before = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')
    due_after = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    overdue = django_filters.BooleanFilter(method='filter_overdue')
    
    search = django_filters.CharFilter(method='filter_search')
    
    due_this_week = django_filters.BooleanFilter(method='filter_due_this_week')
    
    class Meta:
        model = Task
        fields = ['status', 'priority', 'project', 'assignee']
        
    def filter_assignee(self, queryset, name, value):
        """
        Filter by assignee.
        - 'me' = current user
        - number = user ID
        """
        if value == 'me':
            return queryset.filter(assignee=self.request.user)
        
        try:
            return queryset.filter(assignee = int(value))
        except (ValueError, TypeError):
            return queryset.none()
        
    def filter_unassignee(self, queryset, name, value):
        """Filter unassigned tasks."""
        if value:
            return queryset.filter(assignee__isnull=True)
        return queryset
    
    def filter_overdue(self, queryset, name, value):
        """Filter overdue tasks (due_date < today and not done)."""
        if value:
                return queryset.filter(
                    due_date__lte = date.today()
                ).exclude(status=Task.Status.DONE)
        return queryset

    def filter_search(self, queryset, name, value):
        """Search in title and description."""
        if value:
            return queryset.filter(
                Q(title__icontains=value) | Q(description__icontains=value)
            )
        return queryset
    
    def filter_due_this_week(self, queryset, name, value):
        """Filter tasks due this week."""
        if value:
            from datetime import timedelta
            today = date.today()
            week_end = today + timedelta(days=(6-today.weekday()))
            return queryset.filter(
                due_date__gte=today,
                due_date__lte=week_end
            )
        return queryset
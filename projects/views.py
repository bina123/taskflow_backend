"""
Project Views for TaskFlow AI
================================================================================
Laravel equivalent: app/Http/Controllers/ProjectController.php
================================================================================
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from datetime import date, timedelta

from .models import Project, ProjectMember
from tasks.models import Task
from .serializers import (
    ProjectSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
    ProjectMemberSerializer,
    InviteMemberSerializer
)
from tasks.serializers import ActivitySerializer

User = get_user_model()


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project CRUD operations.
    
    This is equivalent to a Laravel Resource Controller:
    - list()    = index()
    - create()  = store()
    - retrieve() = show()
    - update()  = update()
    - destroy() = destroy()
    
    Laravel equivalent:
    class ProjectController extends Controller {
        public function index() { ... }
        public function store(StoreProjectRequest $request) { ... }
        public function show(Project $project) { ... }
        public function update(UpdateProjectRequest $request, Project $project) { ... }
        public function destroy(Project $project) { ... }
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Project.objects.all()
    def get_queryset(self):
        """
        Get projects that user owns or is a member of.
        
        Laravel equivalent:
        public function index() {
            return Project::where('owner_id', auth()->id())
                ->orWhereHas('members', fn($q) => $q->where('user_id', auth()->id()))
                ->get();
        }
        """
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct().select_related('owner')
    
    def get_serializer_class(self):
        """
        Return different serializers for different actions.
        
        Laravel equivalent:
        You'd use different FormRequest classes for different methods
        """
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        return ProjectSerializer
    
    def perform_create(self, serializer):
        """
        Called when creating a project.
        The serializer handles setting the owner.
        """
        serializer.save()
    
    # ==========================================================================
    # Custom Actions (like additional route methods in Laravel)
    # ==========================================================================
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """
        Get project members.
        
        GET /api/projects/{id}/members/
        
        Laravel equivalent:
        Route::get('/projects/{project}/members', [ProjectController::class, 'members']);
        
        public function members(Project $project) {
            return ProjectMemberResource::collection($project->members);
        }
        """
        project = self.get_object()
        members = project.memberships.select_related('user')
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        """
        Invite a user to the project.
        
        POST /api/projects/{id}/invite/
        
        Laravel equivalent:
        public function invite(InviteRequest $request, Project $project) {
            $user = User::where('email', $request->email)->firstOrFail();
            $project->members()->attach($user->id, ['role' => $request->role]);
            return response()->json(['message' => 'User invited']);
        }
        """
        project = self.get_object()
        
        # Check if user is owner or admin
        if project.owner != request.user:
            membership = project.memberships.filter(
                user=request.user,
                role=ProjectMember.Role.ADMIN
            ).first()
            if not membership:
                return Response(
                    {'error': 'Only project owner or admin can invite members'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Find user by email
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already a member
        if project.memberships.filter(user=user).exists():
            return Response(
                {'error': 'User is already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add member
        membership = ProjectMember.objects.create(
            project=project,
            user=user,
            role=serializer.validated_data['role']
        )
        
        return Response(
            ProjectMemberSerializer(membership).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        """
        Remove a member from the project.
        
        DELETE /api/projects/{id}/members/{user_id}/
        
        Laravel equivalent:
        Route::delete('/projects/{project}/members/{user}', ...);
        
        public function removeMember(Project $project, User $user) {
            $project->members()->detach($user->id);
            return response()->json(['message' => 'Member removed']);
        }
        """
        project = self.get_object()
        
        # Check permissions
        if project.owner != request.user:
            return Response(
                {'error': 'Only project owner can remove members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Cannot remove owner
        if str(project.owner.id) == user_id:
            return Response(
                {'error': 'Cannot remove project owner'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Remove membership
        deleted, _ = project.memberships.filter(user_id=user_id).delete()
        
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Member not found'},
            status=status.HTTP_404_NOT_FOUND
        )
        
    @action(detail=True, methods=['get'])
    def priority_summary(self, request, pk=None):
        """
        GET /api/projects/{id}/priority-summary/
        
        Returns task statistics for the project.
        """
        project = self.get_object()
        tasks = project.tasks.all()
        
        # Count by priority
        by_priority = {}
        for priority in Task.Priority.choices:
            key = priority[0]
            by_priority[key] = tasks.filter(priority=key).count()
        
        # Count by status
        by_status = {}
        for status_choice in Task.Status.choices:
            key = status_choice[0]
            by_status[key] = tasks.filter(status=key).count()
            
        overdue_count = tasks.filter(due_date__lt=date.today()).filter(status='done').count()
        
        data = {
            'project': project.name,
            'total_tasks': tasks.count(),
            'by_priority': by_priority,
            'by_status': by_status,
            'overdue_count': overdue_count
        }
        
        return Response(data)
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """
        GET /api/projects/{id}/activities/
        
        Returns activity feed for the project.
        """
        project = self.get_object()
        activities = project.activities.select_related('user', 'task')[:50]
        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        from tasks.models import Task
        from tasks.serializers import TaskSerializer
        from tasks.filters import TaskFilter
        
        project = self.get_object()
        tasks = Task.objects.filter(project=project).select_related('assignee', 'created_by')
        
        filterset = TaskFilter(request.GET, queryset=tasks, request=request)
        filtered_tasks = filterset.qs
        
        page = self.paginate.queryset(filtered_tasks)
        if page is not None:
            serializer = TaskSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = TaskSerializer(filtered_tasks, many=True)
        return Response(TaskSerializer(serializer.data))
"""
Project Serializers for TaskFlow AI
================================================================================
Laravel equivalent: ProjectResource.php + ProjectRequest.php
================================================================================
"""

from rest_framework import serializers
from .models import Project, ProjectMember
from accounts.serializers import UserSerializer


class ProjectMemberSerializer(serializers.ModelSerializer):
    """Serializer for project members."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'role', 'joined_at']


class ProjectSerializer(serializers.ModelSerializer):
    """
    Project serializer for read operations.
    
    Laravel equivalent:
    class ProjectResource extends JsonResource {
        public function toArray($request) {
            return [
                'id' => $this->id,
                'name' => $this->name,
                'owner' => new UserResource($this->owner),
                'members_count' => $this->members()->count(),
                'tasks_count' => $this->tasks()->count(),
                ...
            ];
        }
    }
    """
    owner = UserSerializer(read_only=True)
    members_count = serializers.SerializerMethodField()
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'owner',
            'status',
            'color',
            'members_count',
            'tasks_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
    
    def get_members_count(self, obj):
        """
        Get count of project members.
        Laravel equivalent: $this->members()->count()
        """
        return obj.memberships.count()
    
    def get_tasks_count(self, obj):
        """
        Get count of project tasks.
        Laravel equivalent: $this->tasks()->count()
        """
        return obj.tasks.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating projects.
    
    Laravel equivalent: StoreProjectRequest
    """
    class Meta:
        model = Project
        fields = ['name', 'description', 'color']
    
    def create(self, validated_data):
        """
        Create project with current user as owner.
        
        Laravel equivalent:
        $project = $request->user()->owned_projects()->create($validated);
        """
        # Get current user from context (set by view)
        user = self.context['request'].user
        
        # Create project with user as owner
        project = Project.objects.create(owner=user, **validated_data)
        
        # Automatically add owner as admin member
        ProjectMember.objects.create(
            project=project,
            user=user,
            role=ProjectMember.Role.ADMIN
        )
        
        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating projects."""
    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'color']


class InviteMemberSerializer(serializers.Serializer):
    """
    Serializer for inviting members to project.
    
    Laravel equivalent: InviteMemberRequest
    """
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=ProjectMember.Role.choices,
        default=ProjectMember.Role.MEMBER
    )
    
class ProjectSummarySerializer(serializers.Serializer):
    """
    custom serialize for computed data
    """
    project = serializers.CharField()
    total_tasks =serializers.CharField()
    by_priority = serializers.DictField()
    by_status = serializers.DictField()
    overdue_count = serializers.CharField()

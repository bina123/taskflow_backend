"""
Task Serializers for TaskFlow AI
================================================================================
Laravel equivalent: TaskResource.php + TaskRequest.php + CommentResource.php
================================================================================
"""

from rest_framework import serializers
from .models import Task, Comment, Label, Activity
from accounts.serializers import UserSerializer


class LabelSerializer(serializers.ModelSerializer):
    """Serializer for task labels."""
    class Meta:
        model = Label
        fields = ['id', 'name', 'color']

class LabelCreateSerializer(serializers.ModelSerializer):
    """create labels for a project"""
    class Meta:
        model = Label
        fields = ['name','color', 'project']
        
class LabelUpdateSerializer(serializers.ModelSerializer):
    """Update a model"""
    class Meta:
        model = Label
        fields = ['name', 'color']

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    
    Laravel equivalent:
    class CommentResource extends JsonResource {
        public function toArray($request) {
            return [
                'id' => $this->id,
                'content' => $this->content,
                'user' => new UserResource($this->user),
                'created_at' => $this->created_at,
            ];
        }
    }
    """
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'user', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""
    class Meta:
        model = Comment
        fields = ['content', 'task']


class TaskSerializer(serializers.ModelSerializer):
    """
    Task serializer for read operations.
    
    Laravel equivalent:
    class TaskResource extends JsonResource {
        public function toArray($request) {
            return [
                'id' => $this->id,
                'title' => $this->title,
                'assignee' => new UserResource($this->whenLoaded('assignee')),
                'comments_count' => $this->comments()->count(),
                ...
            ];
        }
    }
    """
    assignee = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    labels = LabelSerializer(many=True, read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'description',
            'project',
            'created_by',
            'assignee',
            'status',
            'priority',
            'due_date',
            'position',
            'labels',
            'comments_count',
            # AI fields
            'ai_time_estimate',
            'ai_suggested_priority',
            # Timestamps
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'created_by', 'created_at', 'updated_at',
            'ai_time_estimate', 'ai_suggested_priority'
        ]
    
    def get_comments_count(self, obj):
        return obj.comments.count()


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating tasks.
    
    Laravel equivalent:
    class StoreTaskRequest extends FormRequest {
        public function rules() {
            return [
                'title' => 'required|string|max:300',
                'project_id' => 'required|exists:projects,id',
                'assignee_id' => 'nullable|exists:users,id',
                ...
            ];
        }
    }
    """
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'project',
            'assignee',
            'status',
            'priority',
            'due_date',
        ]
    
    def create(self, validated_data):
        """Create task with current user as creator."""
        user = self.context['request'].user
        task = Task.objects.create(**validated_data)
        return task


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tasks."""
    class Meta:
        model = Task
        fields = [
            'title',
            'description',
            'assignee',
            'status',
            'priority',
            'due_date',
        ]


class TaskReorderSerializer(serializers.Serializer):
    """
    Serializer for reordering tasks (Kanban drag-drop).
    
    Used when user drags a task to a new position/column.
    """
    status = serializers.ChoiceField(choices=Task.Status.choices)
    position = serializers.IntegerField(min_value=0)


class TaskWithCommentsSerializer(TaskSerializer):
    """Task serializer that includes all comments."""
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['comments']

class ActivitySerializer(serializers.ModelSerializer):
    """serilizer for activity log"""
    user = UserSerializer(read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True,allow_null=True)
    
    class Meta:
        model = Activity
        fields = [
            'id',
            'user',
            'action',
            'task',
            'task_title',
            'details',
            'description',
            'created_at'
        ]
    